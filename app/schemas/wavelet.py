from pydantic import BaseModel, Field
from typing import List, Dict, Any
from app.models.preprocess.wavelet import WaveletName, OptimalMode, WaveletTaskStatus
from datetime import datetime

# --- Base Schema ---

class WaveletDenoiseBase(BaseModel):
    wavelet_name: WaveletName = Field(WaveletName.DB3, description="Name of the wavelet to use (wv)")
    window_size: int = Field(128, description="Window size to apply ATAR (winsize)")
    optimal_mode: OptimalMode = Field(OptimalMode.SOFT, description="Operating mode for thresholding (OptMode)")
    beta: float = Field(0.1, description="Tuning parameter for threshold (beta)")
    k1: float = Field(10.0, description="Lower bound on the threshold value")
    k2: float = Field(100.0, description="Upper bound on the threshold value")
    save_file: bool = Field(True, description="Whether to save the final cleaned data to a new file")

# --- Schema for API Requests ---

class WaveletDenoiseRequest(WaveletDenoiseBase):
    """Schema for submitting a new Wavelet Denoising job."""
    pass

# --- Schema for API Responses ---

class WaveletDenoiseOut(WaveletDenoiseBase):
    """Schema for returning a WaveletDenoise record."""
    id: int
    preprocessing_step_id: int
    status: WaveletTaskStatus
    output_storage_path: str | None = None
    elapsed_seconds: float | None = None
    create_time: datetime
    update_time: datetime

    class Config:
        from_attributes = True
