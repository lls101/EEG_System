from pydantic import BaseModel, Field
from typing import Dict, Any

class FeatureExtractionRequest(BaseModel):
    """
    Schema for feature extraction requests.
    """
    duration: float = Field(2.0, description="Duration of epochs in seconds to create from the raw file.", gt=0)
    params: Dict[str, Any] = Field(default_factory=dict, description="Parameters for the specific feature extraction method.")
