
from tortoise import fields
from enum import Enum
from .utils import BaseModel, TimestampMixin

# Based on mne.channels.get_builtin_montages()
class MNEStandardMontage(str, Enum):
    STANDARD_1005 = "standard_1005"
    STANDARD_1020 = "standard_1020"
    STANDARD_A = "standard_a"
    STANDARD_B = "standard_b"
    STANDARD_C = "standard_c"
    STANDARD_D = "standard_d"
    STANDARD_E = "standard_e"
    STANDARD_F = "standard_f"
    STANDARD_G = "standard_g"
    STANDARD_H = "standard_h"
    STANDARD_I = "standard_i"
    BIOSEMI16 = "biosemi16"
    BIOSEMI32 = "biosemi32"
    BIOSEMI64 = "biosemi64"
    BIOSEMI128 = "biosemi128"
    BIOSEMI160 = "biosemi160"
    BIOSEMI256 = "biosemi256"
    EASYCAP16 = "easycap16"
    EASYCAP32 = "easycap32"
    EASYCAP64 = "easycap64"
    EASYCAP128 = "easycap128"
    EGI_256 = "EGI_256"
    GSN_HYDROCEL_32 = "GSN-HydroCel-32"
    GSN_HYDROCEL_64 = "GSN-HydroCel-64"
    GSN_HYDROCEL_128 = "GSN-HydroCel-128"
    GSN_HYDROCEL_256 = "GSN-HydroCel-256"
    ARTINIS_OCTAMON = "artinis-octamon"
    ARTINIS_BRITEMON = "artinis-britemon"


class PreprocessingStep(BaseModel, TimestampMixin):
    id = fields.IntField(pk=True, description="Pipeline Step ID")
    eeg_file = fields.ForeignKeyField('app_system.EEGFile', related_name='preprocessing_steps', on_delete=fields.CASCADE)
    
    pipeline_name = fields.CharField(max_length=255, description="Human-readable name for this pipeline")
    montage = fields.CharEnumField(MNEStandardMontage, description="Name of the MNE standard montage applied")
    bad_chs = fields.JSONField(description="List of channel names marked as bad")
    eeg_reference = fields.CharField(max_length=255, description="Description of the re-referencing method (e.g., 'average', 'REST', 'TP9, TP10')")
    
    notch_freq = fields.FloatField(null=True, description="Frequency for the notch filter in Hz")
    highpass_freq = fields.FloatField(null=True, description="Frequency for the high-pass filter in Hz")
    lowpass_freq = fields.FloatField(null=True, description="Frequency for the low-pass filter in Hz")
    resample_sfreq = fields.FloatField(null=True, description="New sampling frequency after resampling")
    artifact_path = fields.CharField(max_length=1024, null=True, description="Path to the preprocessed artifact file")


    class Meta:
        table = "preprocessing_steps"
        table_description = "Records of preprocessing pipelines applied to EEG files"
