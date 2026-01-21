from fastapi import APIRouter, File, UploadFile, HTTPException
from starlette.responses import JSONResponse
from pydantic import BaseModel
from app.controllers.pd_detection import predict_from_uploaded_epochs
from app.core.pd_detection import pd_detector, PDStimulationDetector
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


class LoadModelRequest(BaseModel):
    model_name: str


@router.get("/pd_detection/models", summary="获取可用的PD模型列表")
async def get_available_models():
    """获取所有可用的PD检测模型"""
    try:
        models = PDStimulationDetector.get_available_models()
        return JSONResponse(content={
            "code": "0000",
            "msg": "获取模型列表成功",
            "data": models
        })
    except Exception as e:
        logger.exception("获取模型列表失败")
        return JSONResponse(content={
            "code": "5000",
            "msg": f"获取模型列表失败: {str(e)}",
            "data": None
        }, status_code=500)


@router.get("/pd_detection/model_info", summary="获取当前加载的模型信息")
async def get_current_model_info():
    """获取当前加载的模型详细信息"""
    try:
        model_info = pd_detector.get_model_info()
        return JSONResponse(content={
            "code": "0000",
            "msg": "获取模型信息成功",
            "data": model_info
        })
    except Exception as e:
        logger.exception("获取模型信息失败")
        return JSONResponse(content={
            "code": "5000",
            "msg": f"获取模型信息失败: {str(e)}",
            "data": None
        }, status_code=500)


@router.post("/pd_detection/load_model", summary="加载指定的PD模型")
async def load_model(request_data: LoadModelRequest):
    """
    加载指定的模型
    
    Args:
        request_data: 包含 model_name 的请求体
    """
    try:
        model_name = request_data.model_name
        if not model_name:
            return JSONResponse(content={
                "code": "4000",
                "msg": "缺少 model_name 参数",
                "data": None
            }, status_code=400)
        
        # 构建模型路径
        from pathlib import Path
        project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
        model_path = project_root / 'app' / 'dl_models' / 'pd' / model_name
        
        if not model_path.exists():
            return JSONResponse(content={
                "code": "4000",
                "msg": f"模型文件不存在: {model_name}",
                "data": None
            }, status_code=404)
        
        # 加载模型
        pd_detector.load_model(str(model_path))
        
        # 获取新加载的模型信息
        model_info = pd_detector.get_model_info()
        
        return JSONResponse(content={
            "code": "0000",
            "msg": f"模型 {model_name} 加载成功",
            "data": model_info
        })
        
    except Exception as e:
        logger.exception(f"加载模型失败")
        return JSONResponse(content={
            "code": "5000",
            "msg": f"加载模型失败: {str(e)}",
            "data": None
        }, status_code=500)


@router.post("/pd_detection/upload", summary="上传 .fif 文件并进行 PD 刺激检测")
async def upload_and_predict(file: UploadFile = File(...)):
    filename = file.filename or ''
    if not filename.endswith('.fif') and not filename.endswith('.fif.gz'):
        raise HTTPException(status_code=400, detail="仅支持 .fif 或 .fif.gz 文件")

    try:
        result = await predict_from_uploaded_epochs(file)
        return JSONResponse(content={
            "code": "0000",
            "msg": "检测成功",
            "data": {
                "success": True,
                "result": result
            }
        })
    except Exception as e:
        logger.exception("预测时发生错误")
        return JSONResponse(content={
            "code": "5000",
            "msg": f"预测失败: {str(e)}",
            "data": None
        }, status_code=500)
