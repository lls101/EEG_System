from tortoise import fields
from enum import Enum
from app.models.system.utils import BaseModel, TimestampMixin

class WaveletTaskStatus(str, Enum):
    PENDING = "Pending"
    RUNNING = "Running"
    COMPLETED = "Completed"
    FAILED = "Failed"
    CANCELLED = "Cancelled"

class WaveletName(str, Enum):
    DB3 = "db3"
    DB4 = "db4"
    DB5 = "db5"
    SYM4 = "sym4"
    SYM5 = "sym5"
    COIF2 = "coif2"
    COIF3 = "coif3"

class OptimalMode(str, Enum):
    SOFT = "soft"
    ELIMINATION = "elim"
    LINEAR_ATTENUATION = "linAtten"

class WaveletDenoise(BaseModel, TimestampMixin):
    """
    Represents a Wavelet Transform denoising task performed on a preprocessed EEG file.
    """
    id = fields.IntField(pk=True)

    preprocessing_step = fields.ForeignKeyField(
        'app_system.PreprocessingStep',
        related_name='wavelet_denoise_steps',
        on_delete=fields.CASCADE,
        description="The basic preprocessing step that serves as input for Wavelet Denoising"
    )

    # --- Task Management ---
    status = fields.CharEnumField(
        WaveletTaskStatus, 
        default=WaveletTaskStatus.PENDING, 
        description="The current status of the wavelet task"
    )
    task_pid = fields.IntField(null=True, description="Process ID of the running task")
    elapsed_seconds = fields.FloatField(null=True, description="Elapsed time in seconds for the task")

    # --- Parameters for spkit.eeg.ATAR ---
    wavelet_name = fields.CharEnumField(WaveletName, default=WaveletName.DB3, description="Name of the wavelet to use (wv)")
    window_size = fields.IntField(default=128, description="Window size to apply ATAR (winsize)")
    optimal_mode = fields.CharEnumField(OptimalMode, default=OptimalMode.SOFT, description="Operating mode for thresholding (OptMode)")
    beta = fields.FloatField(default=0.1, description="Tuning parameter for threshold (beta)")
    k1 = fields.FloatField(default=10.0, description="Lower bound on the threshold value")
    k2 = fields.FloatField(default=100.0, description="Upper bound on the threshold value")

    # --- Final output ---
    output_storage_path = fields.CharField(
        max_length=1024,
        null=True,
        description="Path to the final EEG data file after Wavelet Denoising"
    )
    save_file = fields.BooleanField(default=True, description="Whether to save the cleaned file to disk")

    class Meta:
        table = "wavelet_denoise_steps"
        table_description = "Stores Wavelet Transform denoising parameters and results"
