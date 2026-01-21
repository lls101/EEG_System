
from fastapi import APIRouter

from .route import router as route_router
from ..preprocess.eeg import router as eeg_router
from .pd_detection import router as pd_detection_router

router_route = APIRouter()
router_route.include_router(route_router)
router_route.include_router(eeg_router)
router_route.include_router(pd_detection_router)

