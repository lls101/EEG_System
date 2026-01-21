import mne
import asyncio
import shutil
from pathlib import Path
import uuid
from typing import List, Tuple
import logging
import traceback

from fastapi import HTTPException
import matplotlib
matplotlib.use('Agg') # Use non-interactive backend for plotting
import matplotlib.pyplot as plt

from app.core.crud import CRUDBase
from app.models.system.preprocessing import PreprocessingStep
from app.models.preprocess.ica import ICAAnalysis, ICAStatus
from app.schemas.ica import ICAFitRequest, ICAApplyRequest
from app.settings.config import settings

import mne
import asyncio
import shutil
from pathlib import Path
import uuid
from typing import List, Tuple

from fastapi import HTTPException
import matplotlib
matplotlib.use('Agg') # Use non-interactive backend for plotting
import matplotlib.pyplot as plt

from app.core.crud import CRUDBase
from app.models.system.preprocessing import PreprocessingStep
from app.models.preprocess.ica import ICAAnalysis, ICAStatus
from app.schemas.ica import ICAFitRequest, ICAApplyRequest
from app.settings.config import settings

class ICAController(CRUDBase[ICAAnalysis, None, None]):
    def __init__(self):
        super().__init__(model=ICAAnalysis)

    async def _get_preprocessed_step_and_path(self, step_id: int) -> Tuple[PreprocessingStep, Path]:
        """Helper to get a preprocessing step record and its artifact path."""
        step_record = await PreprocessingStep.get_or_none(id=step_id).prefetch_related('eeg_file')
        if not step_record:
            raise HTTPException(status_code=404, detail=f"Preprocessing step with ID {step_id} not found.")
        if not step_record.artifact_path:
            raise HTTPException(status_code=400, detail="Source preprocessed file has no artifact path.")
        
        artifact_path = settings.EEG_STORAGE_PATH / step_record.artifact_path
        if not artifact_path.exists():
            raise HTTPException(status_code=404, detail=f"Source artifact file not found at {artifact_path}")
            
        return step_record, artifact_path

    async def fit_ica(self, *, preprocessing_step_id: int, params: ICAFitRequest) -> Tuple[ICAAnalysis, List[str]]:
        """Fits an ICA model, saves it, and generates component plots."""
        logging.info(f"[ICA_FIT] 开始 ICA 拟合，preprocessing_step_id: {preprocessing_step_id}")
        logging.info(f"[ICA_FIT] 请求参数: {params.model_dump()}")
        
        step_record, artifact_path = await self._get_preprocessed_step_and_path(preprocessing_step_id)
        logging.info(f"[ICA_FIT] 找到预处理步骤和文件路径: {artifact_path}")

        # 1. Create initial ICAAnalysis record
        logging.info(f"[ICA_FIT] 创建 ICA 分析记录...")
        ica_record = await self.model.create(
            preprocessing_step_id=preprocessing_step_id,
            status=ICAStatus.FITTING,
            **params.model_dump()
        )
        logging.info(f"[ICA_FIT] ICA 记录创建成功，ID: {ica_record.id}")

        try:
            # 1. Load the raw data from the .fif file
            logging.info(f"[ICA_FIT] 加载原始数据文件: {artifact_path}")
            raw = await asyncio.to_thread(mne.io.read_raw_fif, artifact_path, preload=True)
            logging.info(f"[ICA_FIT] 数据加载成功，通道数: {raw.info['nchan']}, 采样点数: {len(raw.times)}")

            # 2. MNE best practice: fit ICA on a high-pass filtered copy of the data
            logging.info(f"[ICA_FIT] 创建数据副本并进行高通滤波...")
            raw_copy = raw.copy()
            raw_copy.filter(l_freq=1.0, h_freq=None)
            logging.info(f"[ICA_FIT] 高通滤波完成")

            logging.info(f"[ICA_FIT] 创建 ICA 对象，参数: n_components={params.n_components}, method={params.method.value}")
            ica = mne.preprocessing.ICA(
                n_components=params.n_components,
                method=params.method.value,
                random_state=params.random_state,
                fit_params=params.fit_params
            )
            logging.info(f"[ICA_FIT] 开始拟合 ICA 模型...")
            await asyncio.to_thread(ica.fit, raw_copy)
            logging.info(f"[ICA_FIT] ICA 拟合完成，实际成分数: {ica.n_components_}")

            # 3. Save the fitted ICA model
            pipeline_dir = artifact_path.parent
            ica_models_dir = pipeline_dir / "ica_models"
            ica_models_dir.mkdir(exist_ok=True)
            
            model_uuid = str(uuid.uuid4())
            ica_model_path = ica_models_dir / f"{model_uuid}-ica.fif"
            logging.info(f"[ICA_FIT] 保存 ICA 模型到: {ica_model_path}")
            await asyncio.to_thread(ica.save, str(ica_model_path))
            logging.info(f"[ICA_FIT] ICA 模型保存成功")

            # 4. Generate and save component plots
            component_plots_dir = pipeline_dir / "ica_plots" / model_uuid
            component_plots_dir.mkdir(parents=True, exist_ok=True)
            logging.info(f"[ICA_FIT] 创建成分图目录: {component_plots_dir}")
            
            plot_urls = []
            def save_plots():
                logging.info(f"[ICA_FIT] 开始生成 {ica.n_components_} 个成分图...")
                for i in range(ica.n_components_):
                    fig = ica.plot_components(picks=i, show=False)
                    plot_path = component_plots_dir / f"ic_{i:03d}.png"
                    fig.savefig(plot_path)
                    plt.close(fig)
                    # Create a URL-friendly relative path
                    relative_path = str(plot_path.relative_to(settings.EEG_STORAGE_PATH)).replace('\\', '/')
                    plot_urls.append(relative_path)
                    logging.info(f"[ICA_FIT] 成分 {i} 图片已保存: {relative_path}")
            
            await asyncio.to_thread(save_plots)
            logging.info(f"[ICA_FIT] 所有成分图生成完成，共 {len(plot_urls)} 个")

            # 5. Update ICAAnalysis record
            logging.info(f"[ICA_FIT] 更新 ICA 分析记录状态...")
            ica_record.status = ICAStatus.FITTED
            ica_record.ica_model_path = str(ica_model_path.relative_to(settings.EEG_STORAGE_PATH))
            await ica_record.save(update_fields=['status', 'ica_model_path'])
            await ica_record.refresh_from_db()
            logging.info(f"[ICA_FIT] ICA 分析记录更新成功")

            logging.info(f"[ICA_FIT] ICA 拟合过程完成，返回记录 ID: {ica_record.id}, 图片数量: {len(plot_urls)}")
            return ica_record, plot_urls

        except Exception as e:
            logging.error(f"[ICA_FIT] ICA 拟合过程中发生错误: {str(e)}")
            logging.error(f"[ICA_FIT] 错误详情: {traceback.format_exc()}")
            ica_record.status = ICAStatus.ERROR
            await ica_record.save()
            raise HTTPException(status_code=500, detail=f"An error occurred during ICA fitting: {e}")



    async def apply_ica(self, *, ica_analysis_id: int, params: ICAApplyRequest) -> ICAAnalysis:
        """Applies a fitted ICA model and creates a new PreprocessingStep for the output."""
        ica_record = await self.model.get_or_none(id=ica_analysis_id).prefetch_related('preprocessing_step')
        if not ica_record:
            raise HTTPException(status_code=404, detail="ICA analysis record not found.")
        if ica_record.status not in [ICAStatus.FITTED, ICAStatus.APPLIED]:
            raise HTTPException(status_code=400, detail=f"ICA can only be applied to a 'Fitted' or 'Applied' record. Current status: {ica_record.status}")
        if not ica_record.ica_model_path:
            raise HTTPException(status_code=400, detail="ICA model path not found in the record.")

        try:
            # 1. Load data and the saved ICA model
            step_record, artifact_path = await self._get_preprocessed_step_and_path(ica_record.preprocessing_step.id)
            raw = await asyncio.to_thread(mne.io.read_raw_fif, artifact_path, preload=True)
            ica_model_path = settings.EEG_STORAGE_PATH / ica_record.ica_model_path
            ica = await asyncio.to_thread(mne.preprocessing.read_ica, str(ica_model_path))

            # 2. Apply ICA
            ica.exclude = params.exclude_components
            await asyncio.to_thread(ica.apply, raw)

            # 3. Save the cleaned data and create a new PreprocessingStep
            output_path = None
            if params.save_file:
                pipeline_dir = (settings.EEG_STORAGE_PATH / step_record.artifact_path).parent
                ica_output_dir = pipeline_dir / "ica_outputs"
                ica_output_dir.mkdir(exist_ok=True)
                
                cleaned_file_path = ica_output_dir / f"{uuid.uuid4()}-cleaned.fif"
                await asyncio.to_thread(raw.save, str(cleaned_file_path), overwrite=True)
                output_path = str(cleaned_file_path.relative_to(settings.EEG_STORAGE_PATH))

                # --- Create a new PreprocessingStep for the cleaned file ---
                new_step = PreprocessingStep(
                    eeg_file_id=step_record.eeg_file_id,
                    pipeline_name=f"ICA Cleaned from step #{step_record.id}",
                    artifact_path=output_path,
                    # Copy relevant parameters from the original step
                    montage=step_record.montage,
                    bad_chs=step_record.bad_chs,
                    eeg_reference=step_record.eeg_reference,
                    notch_freq=step_record.notch_freq,
                    highpass_freq=step_record.highpass_freq,
                    lowpass_freq=step_record.lowpass_freq,
                    resample_sfreq=step_record.resample_sfreq
                )
                await new_step.save()

            # 4. Update ICAAnalysis record
            ica_record.status = ICAStatus.APPLIED
            ica_record.exclude_components = params.exclude_components
            ica_record.output_storage_path = output_path
            ica_record.save_file = params.save_file
            await ica_record.save()

            return ica_record

        except Exception as e:
            ica_record.status = ICAStatus.ERROR
            await ica_record.save()
            raise HTTPException(status_code=500, detail=f"An error occurred during ICA application: {e}")

    async def get_all_for_preprocessing_step(self, preprocessing_step_id: int) -> List[ICAAnalysis]:
        """Retrieves all ICA analyses for a given preprocessing step."""
        return await self.model.filter(preprocessing_step_id=preprocessing_step_id).prefetch_related('preprocessing_step')
    
    async def get_all_completed_analyses(self) -> List[ICAAnalysis]:
        """Retrieves all ICA analyses with status 'Applied' (completed with cleaned data)."""
        return await self.model.filter(status=ICAStatus.APPLIED).prefetch_related('preprocessing_step')
    
    async def get_paginated_completed_analyses(self, page: int = 1, page_size: int = 10) -> Tuple[List[ICAAnalysis], int]:
        """Retrieves paginated ICA analyses with status 'Applied'."""
        query = self.model.filter(status=ICAStatus.APPLIED).prefetch_related('preprocessing_step')
        total = await query.count()
        records = await query.order_by('-create_time').offset((page - 1) * page_size).limit(page_size)
        return records, total

ica_controller = ICAController()
