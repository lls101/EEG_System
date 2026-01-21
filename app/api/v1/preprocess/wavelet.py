from fastapi import APIRouter, Depends, Query
from typing import List

from app.controllers.wavelet_controller import wavelet_controller
from app.schemas.wavelet import WaveletDenoiseRequest, WaveletDenoiseOut
from app.schemas.base import ResponseModel, Success
from app.core.dependency import DependAuth

router = APIRouter()

@router.post(
    "/tasks/{preprocessing_step_id}", 
    summary="Create a new wavelet denoising task", 
    response_model=ResponseModel[WaveletDenoiseOut],
    # dependencies=[DependAuth] # Disabled for consistency with ICA endpoints
)
async def create_wavelet_task(
    preprocessing_step_id: int,
    params: WaveletDenoiseRequest,
):
    """Creates a new wavelet denoising task with PENDING status."""
    task = await wavelet_controller.create_wavelet_task(
        preprocessing_step_id=preprocessing_step_id, params=params
    )
    return Success(data=WaveletDenoiseOut.model_validate(task).model_dump(mode='json'))

@router.get(
    "/tasks", 
    summary="Get all non-completed wavelet tasks", 
    response_model=ResponseModel[List[WaveletDenoiseOut]],
    # dependencies=[DependAuth] # Disabled for consistency
)
async def get_active_tasks():
    """Retrieves a list of all tasks that are not in COMPLETED state."""
    tasks = await wavelet_controller.get_tasks()
    response_data = [WaveletDenoiseOut.model_validate(task).model_dump(mode='json') for task in tasks]
    return Success(data=response_data)

@router.get(
    "/tasks/{task_id}",
    summary="Get a wavelet task by id",
    response_model=ResponseModel[WaveletDenoiseOut],
    # dependencies=[DependAuth] # Disabled for consistency
)
async def get_task(task_id: int):
    """Get a task by id."""
    task = await wavelet_controller.get_task(task_id=task_id)
    return Success(data=WaveletDenoiseOut.model_validate(task).model_dump(mode='json'))

@router.post(
    "/tasks/{task_id}/start", 
    summary="Start a wavelet denoising task", 
    response_model=ResponseModel[WaveletDenoiseOut],
    # dependencies=[DependAuth] # Disabled for consistency
)
async def start_wavelet_task(task_id: int):
    """Starts the computation for a specific task in the background."""
    task = await wavelet_controller.start_wavelet_task(task_id=task_id)
    return Success(data=WaveletDenoiseOut.model_validate(task).model_dump(mode='json'))

@router.post(
    "/tasks/{task_id}/stop", 
    summary="Stop a running wavelet task", 
    response_model=ResponseModel[WaveletDenoiseOut],
    # dependencies=[DependAuth] # Disabled for consistency
)
async def stop_wavelet_task(task_id: int):
    """Stops (terminates) a running wavelet denoising task."""
    task = await wavelet_controller.stop_wavelet_task(task_id=task_id)
    return Success(data=WaveletDenoiseOut.model_validate(task).model_dump(mode='json'))

@router.delete(
    "/tasks/{task_id}", 
    summary="Delete a wavelet task",
    # dependencies=[DependAuth] # Disabled for consistency
)
async def delete_wavelet_task(task_id: int):
    """Deletes a task, preferably one that is not running."""
    await wavelet_controller.delete_wavelet_task(task_id=task_id)
    return Success(msg="Task deleted successfully.")

@router.get(
    "/all", 
    summary="Get all COMPLETED wavelet denoised results",
    # dependencies=[DependAuth] # Disabled for consistency
)
async def get_all_wavelet_results(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    sort_by: str | None = Query(None, description="Column to sort by"),
    sort_order: str | None = Query("desc", description="Sort order: 'asc' or 'desc'"),
    simple: bool = Query(False, description="Return simple array format for feature extraction")
):
    """
    Retrieves a paginated list of all COMPLETED wavelet denoised results.
    If simple=true, returns a simple array format for feature extraction.
    """
    if simple:
        # Simple format for feature extraction
        records, _ = await wavelet_controller.get_all_denoised_results(
            page=1, page_size=1000, sort_by=sort_by, sort_order=sort_order
        )
        response_data = []
        for rec in records:
            response_data.append({
                "id": rec.id,
                "method": f"Wavelet_{rec.wavelet_name}",
                "wavelet_name": rec.wavelet_name,
                "status": rec.status
            })
        return Success(data=response_data)
    
    # Paginated format for admin interface
    records, total = await wavelet_controller.get_all_denoised_results(
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order
    )

    response_data = [WaveletDenoiseOut.model_validate(rec).model_dump(mode='json') for rec in records]

    paginated_result = {
        "records": response_data,
        "total": total,
        "current": page,
        "size": page_size
    }

    return Success(data=paginated_result)
