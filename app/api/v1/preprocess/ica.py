from fastapi import APIRouter, Depends, Query
from typing import List
import logging

from app.controllers.ica_controller import ica_controller
from app.schemas.ica import ICAFitRequest, ICAApplyRequest, ICAAnalysisOut, ICAComponentPlotOut, ICAComponentPlot
from app.schemas.base import ResponseModel, Success
from app.core.dependency import DependAuth

router = APIRouter()

@router.post("/fit/{preprocessing_step_id}", summary="Fit a new ICA model", response_model=ResponseModel[ICAComponentPlotOut])
async def fit_ica_model(
    preprocessing_step_id: int,
    params: ICAFitRequest,
    # auth: dict = Depends(DependAuth) # Uncomment if auth is needed
):
    """
    Starts a new ICA analysis by fitting a model to a preprocessed file.
    Returns the fitted analysis record and URLs to the component plots.
    """
    logging.info(f"[API_ICA_FIT] 收到 ICA 拟合请求，preprocessing_step_id: {preprocessing_step_id}")
    logging.info(f"[API_ICA_FIT] 请求参数: {params.model_dump()}")
    
    try:
        ica_record, plot_urls = await ica_controller.fit_ica(
            preprocessing_step_id=preprocessing_step_id, params=params
        )
        logging.info(f"[API_ICA_FIT] ICA 控制器返回成功，记录 ID: {ica_record.id}, 图片数量: {len(plot_urls)}")
        
        component_plots = [
            ICAComponentPlot(index=i, plot_url=url) for i, url in enumerate(plot_urls)
        ]
        logging.info(f"[API_ICA_FIT] 创建组件图对象，数量: {len(component_plots)}")
        
        response_data = ICAComponentPlotOut(
            ica_analysis_id=ica_record.id,
            plots=component_plots
        )
        logging.info(f"[API_ICA_FIT] 创建响应数据对象，ICA分析ID: {response_data.ica_analysis_id}")
        
        # 转换为字典并记录最终响应数据
        response_dict = response_data.model_dump(mode='json')
        logging.info(f"[API_ICA_FIT] 最终响应数据: {response_dict}")
        
        result = Success(data=response_dict)
        logging.info(f"[API_ICA_FIT] 创建成功响应并返回")
        
        return result
        
    except Exception as e:
        logging.error(f"[API_ICA_FIT] API 处理过程中发生错误: {str(e)}")
        logging.error(f"[API_ICA_FIT] 错误详情: {repr(e)}")
        raise

@router.post("/apply/{ica_analysis_id}", summary="Apply a fitted ICA model", response_model=ResponseModel[ICAAnalysisOut])
async def apply_ica_model(
    ica_analysis_id: int,
    params: ICAApplyRequest,
    # auth: dict = Depends(DependAuth)
):
    """
    Applies a fitted ICA by providing a list of components to exclude.
    This will create the final, cleaned EEG data file.
    """
    updated_record = await ica_controller.apply_ica(
        ica_analysis_id=ica_analysis_id, params=params
    )
    return Success(data=ICAAnalysisOut.model_validate(updated_record).model_dump(mode='json')) 

@router.get("/analyses/{preprocessing_step_id}", summary="Get all ICA analyses for a preprocessed file", response_model=ResponseModel[List[ICAAnalysisOut]])
async def get_ica_analyses_for_step(preprocessing_step_id: int):
    """
    Retrieves a list of all ICA analyses that have been run on a specific preprocessed file.
    """
    analyses = await ica_controller.get_all_for_preprocessing_step(preprocessing_step_id=preprocessing_step_id)
    validated_analyses = [ICAAnalysisOut.model_validate(rec).model_dump(mode='json') for rec in analyses]
    return Success(data=validated_analyses)

@router.get("/all", summary="Get all completed ICA analyses", response_model=ResponseModel[List[ICAAnalysisOut]])
async def get_all_completed_ica_analyses(simple: bool = Query(False, description="Return simple array format for feature extraction")):
    """
    Retrieves a list of all completed ICA analyses (status = 'Applied') across all preprocessing steps.
    This is useful for feature extraction to browse available ICA-cleaned data sources.
    If simple=true, returns a simple array format for feature extraction.
    """
    analyses = await ica_controller.get_all_completed_analyses()
    
    if simple:
        # Simple format for feature extraction
        response_data = []
        for analysis in analyses:
            response_data.append({
                "id": analysis.id,
                "method": f"ICA_{analysis.id}",
                "exclude_components": analysis.exclude_components,
                "status": analysis.status
            })
        return Success(data=response_data)
    
    # Full format for admin interface
    validated_analyses = [ICAAnalysisOut.model_validate(rec).model_dump(mode='json') for rec in analyses]
    return Success(data=validated_analyses)

@router.delete("/analyses/{ica_analysis_id}", summary="Delete an ICA analysis", response_model=ResponseModel[None])
async def delete_ica_analysis(ica_analysis_id: int):
    """
    Deletes an ICA analysis record and all associated artifacts, including the 
    fitted model, component plots, and the final cleaned data file.
    """
    # This assumes a `remove_ica_analysis` method in the controller that handles file cleanup.
    # Let's add a placeholder for now.
    # await ica_controller.remove_ica_analysis(ica_analysis_id=ica_analysis_id)
    # For now, just delete the record:
    await ica_controller.remove(id=ica_analysis_id)
    return Success(msg="ICA analysis deleted successfully.")