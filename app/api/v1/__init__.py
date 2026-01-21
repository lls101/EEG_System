from fastapi import APIRouter

from .auth import router_auth
from .route import router_route
from .preprocess import preprocess_router
from .route.features import router as features_router  # 新的简化特征提取
# from .feature_extraction import router as feature_extraction_router  # 旧的复杂版本
# from .machine_learning import router as machine_learning_router # 暂时注释掉，需要重新实现

from .system_manage import router_system_manage

v1_router = APIRouter()

v1_router.include_router(router_auth, prefix="/auth", tags=["权限认证"])
v1_router.include_router(router_route, prefix="/route", tags=["路由管理"])
v1_router.include_router(router_system_manage, prefix="/system-manage", tags=["系统管理"])
v1_router.include_router(preprocess_router, prefix="/preprocess", tags=["预处理"])
v1_router.include_router(features_router, prefix="/features", tags=["特征提取"])  # 新的简化版本
# v1_router.include_router(feature_extraction_router, prefix="/feature-extraction", tags=["特征提取"])  # 注释掉旧版本
# v1_router.include_router(machine_learning_router, prefix="/machine-learning", tags=["机器学习"]) # 暂时注释掉
