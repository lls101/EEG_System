from tortoise import fields
from enum import Enum

from .utils import BaseModel, TimestampMixin


class EEGFormat(str, Enum):
    """EEG File Formats"""
    EDF = "European Data Format (.edf)"
    BDF = "BioSemi Data Format (.bdf)"
    BRAIN_VISION = "Brain Vision Format (.vhdr, .vmrk, .eeg)"
    EEGLAB = "EEGLAB Format (.set)"
    FIF = "MNE Functional Image Format (.fif)"
    BIDS = "Brain Imaging Data Structure"
    HDF5 = "HDF5-based Formats (.hdf5)"
    NDF = "Nihon Kohden Format (.ndf)"


class ProcessingStatus(str, Enum):
    """File Processing Status"""
    UPLOADED = "Uploaded"
    PROCESSING = "Processing"
    COMPLETED = "Completed"
    ERROR = "Error"


class EEGFile(BaseModel, TimestampMixin):
    id = fields.IntField(pk=True, description="EEG File ID")
    original_filename = fields.CharField(max_length=255, description="Original name of the uploaded file")
    file_size = fields.BigIntField(null=True, description="File size in bytes")
    storage_path = fields.CharField(max_length=1024, description="Path to the stored file/folder relative to EEG_STORAGE_PATH")
    eeg_format = fields.CharEnumField(EEGFormat, description="Format of the EEG data")
    status = fields.CharEnumField(ProcessingStatus, default=ProcessingStatus.UPLOADED, description="Processing status of the file")
    subject_id = fields.CharField(max_length=128, null=True, index=True, description="Subject ID associated with the data")
    notes = fields.TextField(null=True, description="User notes for this file")

    # Promoted fields
    nchan = fields.IntField(null=True, description="Number of channels")
    sfreq = fields.FloatField(null=True, description="Sampling frequency in Hz")
    line_freq = fields.FloatField(null=True, description="Line frequency in Hz")
    highpass = fields.FloatField(null=True, description="High-pass filter frequency in Hz")
    lowpass = fields.FloatField(null=True, description="Low-pass filter frequency in Hz")
    ch_names = fields.JSONField(null=True, description="List of channel names")

    class Meta:
        table = "eeg_files"
        table_description = "Metadata for uploaded EEG files"
