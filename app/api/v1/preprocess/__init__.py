from multiprocessing import process
from fastapi import APIRouter

from .eeg import router as eeg_router
from .preprocessing import router as preprocessing_router
from .ica import router as ica_router
from .wavelet import router as wavelet_router

preprocess_router = APIRouter()
preprocess_router.include_router(eeg_router, prefix="/eeg", tags=["EEG数据管理"])
preprocess_router.include_router(preprocessing_router, prefix="/preprocessing", tags=["EEG预处理"])
preprocess_router.include_router(ica_router, prefix="/ica", tags=["ICA伪迹去除"])
preprocess_router.include_router(wavelet_router, prefix="/wavelet", tags=["小波去噪"]) 
