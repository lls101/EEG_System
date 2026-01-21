"""
简化的特征提取API路由
"""
from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import FileResponse

from app.controllers.features_controller import (
    features_controller,
    FeatureExtractionRequest,
    FeatureExtractionResponse
)
from app.schemas.base import Success
from app.core.dependency import DependAuth

router = APIRouter()


@router.post("/extract", dependencies=[DependAuth])
async def extract_features(
    request: FeatureExtractionRequest
):
    """
    执行特征提取
    
    参数:
    - source_type: 数据源类型 ("preprocessing", "ica", "wavelet")
    - source_id: 数据源ID
    - domain: 特征域类型 ("time", "frequency", "time_frequency")
    - epoch_duration: epoch长度，默认2秒
    - method: 方法参数，频域可选"multitaper"或"welch"，时频域可选"morlet"等
    """
    result = await features_controller.extract_features(request)
    return Success(data=result.model_dump())


@router.get("/download/{filename}")
async def download_features(filename: str):
    """
    下载特征提取结果文件
    """
    file_path = await features_controller.download_features(filename)
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type='text/csv'
    )


@router.get("/domains", dependencies=[DependAuth])
async def get_supported_domains():
    """
    获取支持的特征域类型
    """
    return {
        "domains": [
            {
                "name": "time",
                "description": "时域特征",
                "methods": ["default"]
            },
            {
                "name": "frequency", 
                "description": "频域特征",
                "methods": ["multitaper", "welch"]
            },
            {
                "name": "time_frequency",
                "description": "时频域特征", 
                "methods": ["morlet", "multitaper", "stockwell", "stft"]
            }
        ]
    }