from tortoise import fields
from enum import Enum
from .utils import BaseModel, TimestampMixin

class MLModelType(str, Enum):
    SVM = "SVM"
    KNN = "KNN"
    DECISION_TREE = "DecisionTree"

class TrainingTaskStatus(str, Enum):
    PENDING = "Pending"
    RUNNING = "Running"
    COMPLETED = "Completed"
    FAILED = "Failed"
    CANCELLED = "Cancelled"

class MachineLearningModel(BaseModel, TimestampMixin):
    """
    Stores information about a trained machine learning model.
    """
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255, unique=True, description="A unique name for the trained model")
    description = fields.TextField(null=True, description="A description of the model and its purpose")
    model_type = fields.CharEnumField(MLModelType, description="The type of machine learning model")
    
    # Path to the serialized (pickled/joblib) model file
    model_path = fields.CharField(max_length=1024, null=True, description="Path to the saved model file")
    
    # Parameters used during training
    hyperparameters = fields.JSONField(null=True, description="Hyperparameters used to train the model")
    
    # Metrics from evaluation
    metrics = fields.JSONField(null=True, description="Performance metrics of the trained model (e.g., accuracy)")

    class Meta:
        table = "ml_models"
        table_description = "Registry of trained machine learning models"


class TrainingTask(BaseModel, TimestampMixin):
    """
    Represents a machine learning model training task.
    """
    id = fields.IntField(pk=True)

    # The model record that this task will create or update upon completion
    model = fields.ForeignKeyField(
        'app_system.MachineLearningModel',
        related_name='training_tasks',
        on_delete=fields.CASCADE,
        description="The model associated with this training task"
    )

    # --- Task Management ---
    status = fields.CharEnumField(
        TrainingTaskStatus,
        default=TrainingTaskStatus.PENDING,
        description="The current status of the training task"
    )
    task_pid = fields.IntField(null=True, description="Process ID of the running training task")

    # --- Input Data and Labels ---
    # A list of IDs from the FeatureExtraction table
    input_feature_ids = fields.JSONField(description="List of feature extraction result IDs to use as input")
    
    # A dictionary mapping feature_extraction_id to its label
    labels = fields.JSONField(description="Labels for the input feature sets")

    class Meta:
        table = "ml_training_tasks"
        table_description = "Stores machine learning training tasks and their status"
