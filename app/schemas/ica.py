from pydantic import BaseModel, Field
from typing import List, Dict, Any
from app.models.preprocess.ica import ICAMethod, ICAStatus
from datetime import datetime

# --- Base Schemas ---

class ICAAnalysisBase(BaseModel):
    n_components: float | int | None = Field(0.99, description="Number of components or variance to keep for ICA")
    method: ICAMethod = Field(ICAMethod.FASTICA, description="ICA algorithm to use")
    fit_params: Dict[str, Any] | None = Field(None, description="Additional fit parameters for the chosen method")
    random_state: int | None = Field(42, description="Seed for the random number generator")
    save_file: bool = Field(True, description="Whether to save the final cleaned data to a new file")

# --- Schemas for API Requests ---

class ICAFitRequest(ICAAnalysisBase):
    """Schema for submitting a new ICA fitting job."""
    pass

class ICAApplyRequest(BaseModel):
    """Schema for applying a fitted ICA to exclude components."""
    exclude_components: List[int] = Field(..., description="List of component indices to mark as artifacts and remove")
    save_file: bool = Field(True, description="Whether to save the final cleaned data to a new file")

# --- Schemas for API Responses ---

class ICAAnalysisOut(ICAAnalysisBase):
    """Schema for returning an ICAAnalysis record."""
    id: int
    preprocessing_step_id: int
    status: ICAStatus
    ica_model_path: str | None = None
    exclude_components: List[int]
    output_storage_path: str | None = None
    create_time: datetime
    update_time: datetime

    class Config:
        from_attributes = True

class ICAComponentPlot(BaseModel):
    """Represents a single ICA component plot."""
    index: int
    plot_url: str # URL to the generated image of the component topography

class ICAComponentPlotOut(BaseModel):
    """Response schema for returning component plots."""
    ica_analysis_id: int
    plots: List[ICAComponentPlot]
