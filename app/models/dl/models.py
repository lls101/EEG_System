from tortoise import fields
from enum import Enum
from app.models.system.utils import BaseModel, TimestampMixin


class ModelArchitecture(str, Enum):
    CNN_1D = "1D-CNN"
    TRANSFORMER = "Transformer"
    LSTM = "LSTM"
    RESNET_1D = "ResNet1D"


class OptimizerType(str, Enum):
    ADAM = "adam"
    SGD = "sgd"
    RMSPROP = "rmsprop"


class LossFunctionType(str, Enum):
    CROSS_ENTROPY = "cross_entropy"
    FOCAL_LOSS = "focal_loss"


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    STOPPED = "stopped"


class DatasetStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DRAFT = "draft"


class Dataset(BaseModel, TimestampMixin):
    """EEG Dataset Metadata"""
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=100, unique=True, description="数据集名称")
    version = fields.CharField(max_length=20, default="v1.0", description="版本号")
    description = fields.TextField(null=True, description="描述")
    
    # Storage info
    base_path = fields.CharField(max_length=500, description="数据存储根目录")
    
    # Statistics
    sample_count = fields.IntField(default=0, description="样本总数")
    channel_info = fields.CharField(max_length=100, null=True, description="通道信息(如 '32ch')")
    
    # Labels (stored as JSON list, e.g. ["PD", "HC"])
    labels = fields.JSONField(default=[], description="包含的标签类别")
    
    status = fields.CharEnumField(enum_type=DatasetStatus, default=DatasetStatus.DRAFT)

    class Meta:
        table = "dl_datasets"
        ordering = ["-created_at"]


class TrainingConfig(BaseModel, TimestampMixin):
    """Deep Learning Training Configuration"""
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=100, description="配置名称")
    
    # Model Architecture
    model_type = fields.CharEnumField(enum_type=ModelArchitecture, default=ModelArchitecture.CNN_1D)
    
    # Hyperparameters
    epochs = fields.IntField(default=100)
    batch_size = fields.IntField(default=32)
    learning_rate = fields.FloatField(default=0.001)
    optimizer = fields.CharEnumField(enum_type=OptimizerType, default=OptimizerType.ADAM)
    loss_function = fields.CharEnumField(enum_type=LossFunctionType, default=LossFunctionType.CROSS_ENTROPY)
    
    # Advanced
    seed = fields.IntField(default=42, description="随机种子")
    val_split = fields.FloatField(default=0.2, description="验证集比例")
    
    description = fields.TextField(null=True)

    class Meta:
        table = "dl_training_configs"


class TrainingTask(BaseModel, TimestampMixin):
    """Training Task Execution Record"""
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=100, description="任务名称")
    
    # Relationships
    dataset: fields.ForeignKeyRelation[Dataset] = fields.ForeignKeyField(
        "app_dl.Dataset", related_name="tasks", on_delete=fields.CASCADE
    )
    config: fields.ForeignKeyRelation[TrainingConfig] = fields.ForeignKeyField(
        "app_dl.TrainingConfig", related_name="tasks", on_delete=fields.RESTRICT
    )
    
    # Execution State
    status = fields.CharEnumField(enum_type=TaskStatus, default=TaskStatus.PENDING)
    progress = fields.FloatField(default=0.0, description="进度 0-100")
    
    # Timing
    start_time = fields.DatetimeField(null=True)
    end_time = fields.DatetimeField(null=True)
    
    # Results (JSON for flexibility)
    metrics = fields.JSONField(null=True, description="最终指标 {acc, loss, ...}")
    log_path = fields.CharField(max_length=500, null=True, description="日志文件路径")
    
    # Artifacts
    best_model_path = fields.CharField(max_length=500, null=True, description="最佳模型权重路径")

    class Meta:
        table = "dl_training_tasks"
        ordering = ["-created_at"]


class TrainedModel(BaseModel, TimestampMixin):
    """Registered Models for Inference"""
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=100, unique=True)
    version = fields.CharField(max_length=20)
    
    source_task: fields.ForeignKeyRelation[TrainingTask] = fields.ForeignKeyField(
        "app_dl.TrainingTask", related_name="registered_models"
    )
    
    file_path = fields.CharField(max_length=500, description="模型文件绝对路径")
    metrics = fields.JSONField(description="注册时的性能指标")
    
    is_active = fields.BooleanField(default=True, description="是否可用于在线推理")

    class Meta:
        table = "dl_trained_models"
