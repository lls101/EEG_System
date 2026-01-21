from tortoise import fields
from enum import Enum
from app.models.system.utils import BaseModel, TimestampMixin


class ICAMethod(str, Enum):
    """ICA algorithm method"""
    FASTICA = "fastica"
    INFOMAX = "infomax"
    PICARD = "picard"

class ICAStatus(str, Enum):
    """Status of an ICA analysis task"""
    FITTING = "Fitting"
    FITTED = "Fitted"  # ICA model is trained and saved, waiting for user to select bad components
    APPLIED = "Applied" # Bad components have been removed and final file is saved
    ERROR = "Error"

class ICAAnalysis(BaseModel, TimestampMixin):
    """
    Represents an ICA artifact removal analysis performed on a preprocessed EEG file.
    """
    id = fields.IntField(pk=True)

    # Foreign key to the basic preprocessing step, this is the input data
    preprocessing_step = fields.ForeignKeyField(
        'app_system.PreprocessingStep', 
        related_name='ica_analyses', 
        on_delete=fields.CASCADE,
        description="The basic preprocessing step that serves as input for ICA"
    )

    status = fields.CharEnumField(
        ICAStatus, 
        default=ICAStatus.FITTING, 
        description="The current status of the ICA task"
    )

    # --- Parameters used for fitting the ICA model ---
    n_components = fields.FloatField(null=True, description="n_components for ICA (float for variance, int for count)")
    method = fields.CharEnumField(ICAMethod, default=ICAMethod.FASTICA, description="ICA algorithm")
    fit_params = fields.JSONField(null=True, description="Additional parameters for the ICA fit method")
    random_state = fields.IntField(null=True, description="Seed for the random number generator for reproducibility")

    # --- Results of the fitting process ---
    ica_model_path = fields.CharField(
        max_length=1024, 
        null=True, 
        description="Path to the saved MNE ICA model object (-ica.fif)"
    )

    # --- Parameters for applying the ICA model ---
    exclude_components = fields.JSONField(
        default=[], 
        description="List of integer indices of ICA components to exclude"
    )

    # --- Final output ---
    output_storage_path = fields.CharField(
        max_length=1024, 
        null=True, 
        description="Path to the final EEG data file after applying ICA"
    )
    
    save_file = fields.BooleanField(default=False, description="Whether to save the cleaned file to disk")

    

    class Meta:
        table = "ica_analyses"
        table_description = "Stores ICA artifact removal analysis steps and parameters"

