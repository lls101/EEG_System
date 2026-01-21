"""
简化的特征提取控制器 - 支持多种数据源
移除复杂的任务系统，直接返回特征提取结果
"""
import mne
import json
import uuid
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import HTTPException
from pydantic import BaseModel

from app.models.system.preprocessing import PreprocessingStep
from app.settings.config import settings

# 核心特征提取模块
from app.core.features.time_domain import extract_time_domain_features
from app.core.features.frequency_domain import extract_frequency_features_mne110
from app.core.features.time_frequency import extract_time_frequency_features


class FeatureExtractionRequest(BaseModel):
    """特征提取请求模型"""
    # 数据来源配置
    source_type: str = "preprocessing"  # "preprocessing", "ica", "wavelet"
    source_id: int  # preprocessing_step_id, ica_analysis_id, 或 wavelet_denoise_id
    
    # 特征提取配置
    domain: str = "time"  # "time", "frequency", "time_frequency"
    epoch_duration: float = 2.0  # 默认2秒epoch
    method: Optional[str] = None  # 方法参数，如频域的'multitaper'或'welch'
    
    
class FeatureExtractionResponse(BaseModel):
    """特征提取响应模型"""
    success: bool
    message: str
    feature_count: int
    epoch_count: int
    channels: list[str]
    source_type: str
    source_id: int
    features_summary: Dict[str, Any]
    download_url: Optional[str] = None


class FeaturesController:
    """支持多种数据源的特征提取控制器"""
    
    def __init__(self):
        self.storage_path = Path(settings.EEG_STORAGE_PATH)
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    async def extract_features(self, request: FeatureExtractionRequest) -> FeatureExtractionResponse:
        """
        直接执行特征提取，返回结果
        """
        try:
            # 1. 根据数据来源类型获取数据文件路径
            if request.source_type == "preprocessing":
                input_file, source_info = await self._get_preprocessing_file(request.source_id)
            elif request.source_type == "ica":
                input_file, source_info = await self._get_ica_file(request.source_id)
            elif request.source_type == "wavelet":
                input_file, source_info = await self._get_wavelet_file(request.source_id)
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported source type: {request.source_type}. Use 'preprocessing', 'ica', or 'wavelet'"
                )
            
            # 2. 加载预处理后的EEG数据
            if not input_file.exists():
                raise HTTPException(
                    status_code=404,
                    detail=f"Data file not found: {input_file}"
                )
            
            print(f"Loading EEG data from: {input_file}")
            raw = mne.io.read_raw_fif(str(input_file), preload=True, verbose=False)
            
            # 3. 创建固定长度的epochs
            print(f"Creating epochs with duration: {request.epoch_duration}s")
            epochs = mne.make_fixed_length_epochs(
                raw, 
                duration=request.epoch_duration, 
                preload=True, 
                verbose=False
            )
            
            print(f"Created {len(epochs)} epochs from {len(epochs.ch_names)} channels")
            
            # 4. 根据域类型提取特征
            if request.domain == "time":
                features, feature_names = extract_time_domain_features(epochs)
            elif request.domain == "frequency":
                method = request.method or "multitaper"
                features, feature_names = extract_frequency_features_mne110(epochs, method=method)
            elif request.domain == "time_frequency":
                method = request.method or "morlet"
                features, feature_names = extract_time_frequency_features(epochs, method=method)
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported domain: {request.domain}. Use 'time', 'frequency', or 'time_frequency'"
                )
            
            # 5. 转换为DataFrame并保存
            features_df = self._features_to_dataframe(features, feature_names, epochs)
            
            # 6. 保存结果
            results_filename = f"features_{request.domain}_{request.source_type}_{request.source_id}_{uuid.uuid4().hex[:8]}.csv"
            results_path = self.storage_path / results_filename
            features_df.to_csv(results_path, index=False)
            
            # 7. 生成响应
            features_summary = self._generate_summary(features_df, request.domain)
            
            return FeatureExtractionResponse(
                success=True,
                message="Feature extraction completed successfully",
                feature_count=len(feature_names),
                epoch_count=len(epochs),
                channels=epochs.ch_names,
                source_type=request.source_type,
                source_id=request.source_id,
                features_summary=features_summary,
                download_url=f"/api/v1/features/download/{results_filename}"
            )
            
        except HTTPException:
            raise
        except Exception as e:
            print(f"Feature extraction error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Feature extraction failed: {str(e)}"
            )
    
    async def _get_preprocessing_file(self, preprocessing_step_id: int):
        """获取基本预处理文件"""
        step = await PreprocessingStep.get_or_none(id=preprocessing_step_id)
        if not step:
            raise HTTPException(
                status_code=404,
                detail=f"Preprocessing step with ID {preprocessing_step_id} not found."
            )
        
        if not step.artifact_path:
            raise HTTPException(
                status_code=400,
                detail="No preprocessed data file found for this step."
            )
        
        input_file = self.storage_path / step.artifact_path
        source_info = {"type": "preprocessing", "id": preprocessing_step_id, "name": step.pipeline_name}
        return input_file, source_info
    
    async def _get_ica_file(self, ica_analysis_id: int):
        """获取ICA处理后的文件"""
        # 动态导入避免循环依赖
        from app.models.preprocess.ica import ICAAnalysis
        
        ica_analysis = await ICAAnalysis.get_or_none(id=ica_analysis_id)
        if not ica_analysis:
            raise HTTPException(
                status_code=404,
                detail=f"ICA analysis with ID {ica_analysis_id} not found."
            )
        
        if not ica_analysis.output_storage_path:
            raise HTTPException(
                status_code=400,
                detail="No ICA cleaned data file found for this analysis."
            )
        
        input_file = self.storage_path / ica_analysis.output_storage_path
        source_info = {
            "type": "ica", 
            "id": ica_analysis_id, 
            "method": ica_analysis.method,
            "components_removed": len(ica_analysis.exclude_components or [])
        }
        return input_file, source_info
    
    async def _get_wavelet_file(self, wavelet_denoise_id: int):
        """获取小波去噪后的文件"""
        # 动态导入避免循环依赖
        from app.models.preprocess.wavelet import WaveletDenoise
        
        wavelet_denoise = await WaveletDenoise.get_or_none(id=wavelet_denoise_id)
        if not wavelet_denoise:
            raise HTTPException(
                status_code=404,
                detail=f"Wavelet denoise with ID {wavelet_denoise_id} not found."
            )
        
        if not wavelet_denoise.output_storage_path:
            raise HTTPException(
                status_code=400,
                detail="No wavelet denoised data file found for this task."
            )
        
        input_file = self.storage_path / wavelet_denoise.output_storage_path
        source_info = {
            "type": "wavelet",
            "id": wavelet_denoise_id,
            "wavelet": wavelet_denoise.wavelet_name,
            "threshold_mode": wavelet_denoise.threshold_mode
        }
        return input_file, source_info
    
    def _features_to_dataframe(self, features: np.ndarray, feature_names: list, epochs) -> pd.DataFrame:
        """将特征数组转换为DataFrame"""
        # features shape: (n_epochs, n_features)
        df_data = {}
        
        # 添加epoch信息
        df_data['epoch'] = range(len(features))
        df_data['channel_count'] = [len(epochs.ch_names)] * len(features)
        
        # 添加特征
        for i, feature_name in enumerate(feature_names):
            df_data[feature_name] = features[:, i]
        
        return pd.DataFrame(df_data)
    
    def _generate_summary(self, features_df: pd.DataFrame, domain: str) -> Dict[str, Any]:
        """生成特征摘要统计"""
        # 排除非特征列
        feature_cols = [col for col in features_df.columns if col not in ['epoch', 'channel_count']]
        
        summary = {
            "domain": domain,
            "total_features": len(feature_cols),
            "feature_statistics": {}
        }
        
        # 计算每个特征的基本统计
        for col in feature_cols[:5]:  # 只显示前5个特征的统计
            col_data = features_df[col]
            summary["feature_statistics"][col] = {
                "mean": float(col_data.mean()),
                "std": float(col_data.std()),
                "min": float(col_data.min()),
                "max": float(col_data.max())
            }
        
        return summary
    
    async def download_features(self, filename: str):
        """下载特征文件"""
        file_path = self.storage_path / filename
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Feature file not found")
        
        return file_path


# 创建控制器实例
features_controller = FeaturesController()