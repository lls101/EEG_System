from pydantic import BaseModel, Field
from typing import Dict, Any, List
from datetime import datetime

from app.models.system.machine_learning import MLModelType, TrainingTaskStatus

# --- Schemas for MachineLearningModel ---

class MLModelBase(BaseModel):
    name: str = Field(..., description="A unique name for the model")
    description: str | None = None
    model_type: MLModelType
    hyperparameters: Dict[str, Any] | None = Field(None, description="Hyperparameters for the model")

class MLModelCreate(MLModelBase):
    pass

class MLModelOut(MLModelBase):
    id: int
    model_path: str | None = None
    metrics: Dict[str, Any] | None = None
    create_time: datetime
    update_time: datetime

    class Config:
        from_attributes = True

# --- Schemas for TrainingTask ---

class TrainingTaskBase(BaseModel):
    input_feature_ids: List[int] = Field(..., description="List of feature extraction result IDs to use as input")
    labels: Dict[str, Any] = Field(..., description="Labels for the input feature sets, mapping ID to label")

class TrainingTaskCreate(TrainingTaskBase):
    # We combine model creation and task creation in one request
    model_name: str = Field(..., description="A unique name for the new model to be trained")
    model_description: str | None = None
    model_type: MLModelType = Field(MLModelType.SVM, description="The type of model to train")
    hyperparameters: Dict[str, Any] | None = Field(None, description="Hyperparameters for the model")

class TrainingTaskOut(BaseModel):
    id: int
    model_id: int
    status: TrainingTaskStatus
    input_feature_ids: List[int]
    create_time: datetime
    update_time: datetime
    model: MLModelOut # Embed the full model details

    class Config:
        from_attributes = True
