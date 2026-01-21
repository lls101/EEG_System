
import asyncio
import mne
from pathlib import Path
import uuid
import shutil 

from typing import List

from app.core.crud import CRUDBase
from app.models.system.eeg import EEGFile
from app.models.system.preprocessing import PreprocessingStep
from app.schemas.preprocessing import PreprocessingStepCreate
from app.settings.config import settings
from fastapi import HTTPException
from tortoise.expressions import Q
from typing import List, Tuple

class PreprocessingController(CRUDBase[PreprocessingStep, PreprocessingStepCreate, None]):
    def __init__(self):
        super().__init__(model=PreprocessingStep)

    async def apply_preprocessing(
        self, *, eeg_file_id: int, params: PreprocessingStepCreate
    ) -> PreprocessingStep:
        """
        Loads an EEG file, applies a preprocessing pipeline, saves the result,
        and creates a record of the preprocessing step.
        """
        # 1. Get the original EEGFile record
        eeg_file = await EEGFile.get_or_none(id=eeg_file_id)
        if not eeg_file:
            raise HTTPException(status_code=404, detail="Original EEG file record not found")

        if eeg_file.status != "Completed":
            raise HTTPException(status_code=400, detail=f"Original EEG file status is '{eeg_file.status}', must be 'Completed'.")

        original_fif_path = settings.EEG_STORAGE_PATH / eeg_file.storage_path
        if not original_fif_path.exists():
            raise HTTPException(status_code=404, detail=f"Source .fif file not found at {original_fif_path}")

        # 2. Load the raw data from the .fif file
        raw = await asyncio.to_thread(mne.io.read_raw_fif, original_fif_path, preload=True)

        # 3. Apply the preprocessing pipeline using MNE-Python
        try:
            # Set montage
            montage = mne.channels.make_standard_montage(params.montage.value)
            raw.set_montage(montage, on_missing='warn')

            # Mark bad channels
            raw.info['bads'] = params.bad_chs

            # Apply filters
            if params.notch_freq:
                raw.notch_filter(freqs=params.notch_freq, picks='eeg', fir_design='firwin', verbose=False)
            
            if params.highpass_freq is not None or params.lowpass_freq is not None:
                raw.filter(l_freq=params.highpass_freq, h_freq=params.lowpass_freq, picks='eeg', fir_design='firwin', verbose=False)

            # Apply re-referencing
            if params.eeg_reference:
                if params.eeg_reference.lower() == 'average':
                    raw.set_eeg_reference(ref_channels='average', projection=True, verbose=False)
                    raw.apply_proj(verbose=False)
                else:
                    ref_channels = [ch.strip() for ch in params.eeg_reference.split(',')]
                    raw.set_eeg_reference(ref_channels=ref_channels, verbose=False)

            # Apply resampling
            if params.resample_sfreq:
                await asyncio.to_thread(raw.resample, sfreq=params.resample_sfreq)

        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error during MNE processing: {e}")

        # 4. Conditionally save the preprocessed file
        artifact_path_to_save = None
        if params.save_file:
            pipeline_id = uuid.uuid4()
            # The storage_path of the original file is something like '<uuid>/<uuid>.fif'
            # We will create a new directory for the pipeline artifacts
            preprocessed_dir = original_fif_path.parent / "pipelines" / str(pipeline_id)
            preprocessed_dir.mkdir(parents=True, exist_ok=True)
            preprocessed_fif_path = preprocessed_dir / "preprocessed.fif"

            await asyncio.to_thread(raw.save, str(preprocessed_fif_path), overwrite=True)

            # Store the relative path to the new artifact
            artifact_path_to_save = str(preprocessed_fif_path.relative_to(settings.EEG_STORAGE_PATH))

        # 5. Create the PreprocessingStep record in the database
        step_data = params.model_dump(exclude={'save_file', 'artifact_path'})
        step_record = PreprocessingStep(
            **step_data,
            eeg_file_id=eeg_file_id,
            artifact_path=artifact_path_to_save
        )
        await step_record.save()

        await step_record.refresh_from_db()


        return step_record

    async def get_preprocessing_steps_for_file(
        self, eeg_file_id: int
    ) -> Tuple[List[PreprocessingStep], int]:  # 1. 修改返回类型提示
        """
        Retrieves all preprocessing steps associated with a specific EEG file.
        """
        if 'created_time' in self.model._meta.fields_map:
            order_field = 'created_time'
        elif 'created_at' in self.model._meta.fields_map:
            order_field = 'created_at'
        else:
            order_field = self.model._meta.pk_attr

        # === 关键修改 ===
        # 创建一个基础查询，同时用于获取数据和计数
        query = self.model.filter(eeg_file_id=eeg_file_id).prefetch_related("eeg_file")
        
        # 获取总数
        total = await query.count()
        
        # 获取排序后的数据列表
        steps = await query.order_by(f'-{order_field}')
        
        # 2. 返回包含列表和总数的元组
        return steps, total

    async def get_all_completed_steps(
        self,
        *,
        page: int = 1,
        page_size: int = 10,
        search: str | None = None,
        sort_by: str | None = None,
        sort_order: str | None = "desc"
        ) -> Tuple[List[PreprocessingStep], int]:
        """
        Retrieves a paginated list of all completed (saved) preprocessing steps.
        Supports searching by pipeline_name.
        """
        # We define a "completed" step as one where an artifact was saved.
        query = self.model.filter(artifact_path__isnull=False).prefetch_related("eeg_file")
    

        if search:
            # Search by pipeline name or original filename
            query = query.filter(
                Q(pipeline_name__icontains=search) |
                Q(eeg_file__original_filename__icontains=search)
            )

        # Get total count for pagination
        total = await query.count()

        order_field = 'create_time'

        if sort_by and sort_by in self.model._meta.fields_map:
            order_field = sort_by

        if sort_order and sort_order.lower() == 'desc':
            order_field = f"-{order_field}"

        records = await query.order_by(order_field).offset(
            (page - 1) * page_size
        ).limit(page_size)

        return records, total

    async def remove_step(self, *, step_id: int) -> None:
        """
        Deletes a PreprocessingStep record and its associated artifact file/folder.
        """
        step_record = await self.get(id=step_id)
        if not step_record:
            raise HTTPException(status_code=404, detail="Preprocessing step not found")

        # 如果记录中有关联的物理文件路径
        if step_record.artifact_path:
            # 构建文件的完整物理路径
            artifact_full_path = settings.EEG_STORAGE_PATH / step_record.artifact_path
            
            # 要删除的是包含该文件的整个流水线目录 (例如 '.../pipelines/<pipeline_uuid>/')
            pipeline_dir = artifact_full_path.parent
            
            def delete_physical_files():
                if pipeline_dir and pipeline_dir.exists() and pipeline_dir.is_dir():
                    print(f"Deleting directory: {pipeline_dir}")
                    shutil.rmtree(pipeline_dir)

            # 在一个独立的线程中执行文件删除IO操作，避免阻塞
            await asyncio.to_thread(delete_physical_files)

        # 从数据库中删除这条记录
        await self.remove(id=step_id)
preprocessing_controller = PreprocessingController()
