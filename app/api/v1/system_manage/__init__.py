from fastapi import APIRouter

from app.core.dependency import DependPermission, DependAuth
from .apis import router as api_router
from .logs import router as log_router
from .menus import router as menu_router
from .overview import router as overview_router
from .roles import router as role_router
from .users import router as user_router

router_system_manage = APIRouter()
router_system_manage.include_router(log_router, tags=["日志管理"], dependencies=[DependPermission])
router_system_manage.include_router(api_router, tags=["API管理"], dependencies=[DependPermission])
router_system_manage.include_router(menu_router, tags=["菜单管理"], dependencies=[DependPermission])
router_system_manage.include_router(role_router, tags=["角色管理"], dependencies=[DependPermission])
router_system_manage.include_router(user_router, tags=["用户管理"], dependencies=[DependPermission])
router_system_manage.include_router(overview_router, tags=["系统概览"], dependencies=[DependAuth])
