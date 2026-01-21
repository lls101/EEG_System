
from pydantic import BaseModel, Field
from typing import List
from app.models.system.preprocessing import MNEStandardMontage
from datetime import datetime


class PreprocessingStepBase(BaseModel):
    pipeline_name: str = Field(..., description="Human-readable name for this pipeline")
    montage: MNEStandardMontage = Field(..., description="Name of the MNE standard montage applied")
    bad_chs: List[str] = Field(description="List of channel names marked as bad", default=[])
    eeg_reference: str = Field(..., description="Description of the re-referencing method (e.g., 'average', 'REST')")
    notch_freq: float | None = Field(None, description="Frequency for the notch filter in Hz")
    highpass_freq: float | None = Field(None, description="Frequency for the high-pass filter in Hz")
    lowpass_freq: float | None = Field(None, description="Frequency for the low-pass filter in Hz")
    resample_sfreq: float | None = Field(None, description="New sampling frequency after resampling")
    artifact_path: str | None = Field(None, description="Path to the preprocessed artifact file")
    save_file: bool = Field(False, description="Whether to save the preprocessed file to disk")

class PreprocessingStepCreate(PreprocessingStepBase):
    pass

class PreprocessingStepUpdate(PreprocessingStepBase):
    pass

class PreprocessingStepOut(PreprocessingStepBase):
    id: int
    eeg_file_id: int
    create_time: datetime

    class Config:
        from_attributes = True
