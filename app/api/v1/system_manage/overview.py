from datetime import datetime, timezone
from pathlib import Path
import os
import platform
import sys

from fastapi import APIRouter

from app.core.runtime import APP_START_TIME
from app.models.system.eeg import EEGFile
from app.models.system.preprocessing import PreprocessingStep
from app.schemas.base import Success
from app.settings import APP_SETTINGS

router = APIRouter()


@router.get("/overview", summary="Get system overview data")
async def get_system_overview():
    uploads_count = await EEGFile.all().count()
    preprocessing_count = await PreprocessingStep.all().count()

    features_root = Path(APP_SETTINGS.EEG_STORAGE_PATH)
    features_count = 0
    if features_root.exists():
        features_count = sum(1 for _ in features_root.rglob("features_*.csv"))

    now = datetime.now(timezone.utc)
    uptime_seconds = max(0.0, (now - APP_START_TIME).total_seconds())

    data = {
        "counts": {
            "uploads": uploads_count,
            "preprocessing": preprocessing_count,
            "features": features_count
        },
        "runtime": {
            "app_title": APP_SETTINGS.APP_TITLE,
            "version": APP_SETTINGS.VERSION,
            "start_time": APP_START_TIME.isoformat(),
            "uptime_seconds": uptime_seconds,
            "pid": os.getpid(),
            "python_version": sys.version.split()[0],
            "platform": platform.platform()
        }
    }

    return Success(data=data)
