
from pydantic import BaseModel, Field, ConfigDict
from typing import Any
from datetime import datetime

from app.models.system.eeg import EEGFormat, ProcessingStatus


class EEGFileBase(BaseModel):
    original_filename: str | None = None
    file_size: int | None = None
    eeg_format: EEGFormat | None = None
    subject_id: str | None = None
    notes: str | None = None
    storage_path: str | None = None
    status: ProcessingStatus | None = None

    # Promoted fields
    nchan: int | None = None
    sfreq: float | None = None
    line_freq: float | None = None
    highpass: float | None = None
    lowpass: float | None = None
    ch_names: list[str] | None = None


class EEGFileCreate(EEGFileBase):
    pass


class EEGFileUpdate(EEGFileBase):
    pass


class EEGFileOut(EEGFileBase):
    id: int
    created_at: datetime = Field(alias="create_time") 
    updated_at: datetime = Field(alias="update_time")

    model_config = ConfigDict(from_attributes=True)
