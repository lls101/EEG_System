
from fastapi import APIRouter
from typing import List

from app.controllers.preprocessing_controller import preprocessing_controller
from app.schemas.preprocessing import PreprocessingStepCreate, PreprocessingStepOut
from app.schemas.base import ResponseModel, Success
from app.core.dependency import DependAuth
from fastapi import Query

router = APIRouter()

@router.post(
    "/{eeg_file_id}",
    summary="Apply a new preprocessing pipeline to an EEG file",
    response_model=ResponseModel[PreprocessingStepOut],
    dependencies=[DependAuth]
)
async def apply_preprocessing_to_file(
    eeg_file_id: int,
    params: PreprocessingStepCreate
):
    """
    Apply a set of preprocessing steps to a specified EEG file.
    This will create a new record in the PreprocessingStep table.
    """
    new_step = await preprocessing_controller.apply_preprocessing(
        eeg_file_id=eeg_file_id, params=params
    )
    response_data = PreprocessingStepOut.model_validate(new_step)
    

    return Success(data=response_data.model_dump(mode="json"))


@router.get(
    "/{eeg_file_id}/steps",
    summary="Get preprocessing steps for an EEG file",
    # response_model=ResponseModel[List[PreprocessingStepOut]], # 可以移除或保留，FastAPI 会自动推断
    dependencies=[DependAuth]
)
async def get_preprocessing_steps(eeg_file_id: int):
    """
    Retrieve a list of preprocessing steps for a specific EEG file.
    """
    steps, total = await preprocessing_controller.get_preprocessing_steps_for_file(eeg_file_id=eeg_file_id)
    
    response_data = []
    for step in steps:
        step_dump = PreprocessingStepOut.model_validate(step).model_dump(mode="json")
        step_dump['original_filename'] = step.eeg_file.original_filename if step.eeg_file else None
        response_data.append(step_dump)

    # === 关键修改：包装成标准分页格式 ===
    paginated_result = {
        "records": response_data,
        "total": total,
        "current": 1, # 因为此接口不分页，所以当前页总是1
        "size": total or 10
    }
    return Success(data=paginated_result)



@router.get(
    "/steps/completed",
    summary="Get all completed preprocessing steps",
    dependencies=[DependAuth]
)
async def get_all_completed_preprocessing_steps(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    search: str | None = Query(None, description="Search by pipeline name or original filename"),
    sort_by: str | None = Query(None, description="Column to sort by"),
    sort_order: str | None = Query("desc", description="Sort order: 'asc' or 'desc'")
):
    """
    Retrieve a paginated list of all preprocessing steps that resulted in a saved file.
    """
    steps, total = await preprocessing_controller.get_all_completed_steps(
        page=page, page_size=page_size, search=search,sort_by=sort_by,
        sort_order=sort_order
    )

    response_data = []
    for step in steps:
        step_dump = PreprocessingStepOut.model_validate(step).model_dump(mode="json")
        step_dump['original_filename'] = step.eeg_file.original_filename if step.eeg_file else None
        response_data.append(step_dump)

    # === 关键修改：同样包装成标准分页格式 ===
    paginated_result = {
        "records": response_data,
        "total": total,
        "current": page,
        "size": page_size
    }
    return Success(data=paginated_result)


@router.get(
    "/steps",
    summary="Get all completed preprocessing steps (simplified for feature extraction)",
    # Remove auth dependency for feature extraction access
)
async def get_all_preprocessing_steps():
    """
    Retrieve all completed preprocessing steps in a simplified format for feature extraction.
    This endpoint is used by the feature extraction frontend to populate data source options.
    """
    steps, total = await preprocessing_controller.get_all_completed_steps(
        page=1, page_size=1000, search=None, sort_by=None, sort_order="desc"
    )

    response_data = []
    for step in steps:
        step_data = {
            "id": step.id,
            "pipeline_name": step.pipeline_name,
            "original_filename": step.eeg_file.original_filename if step.eeg_file else None,
            "status": "completed"
        }
        response_data.append(step_data)

    return Success(data=response_data)


@router.delete(
    "/steps/{step_id}",
    summary="Delete a preprocessing step",
    dependencies=[DependAuth]
)
async def delete_preprocessing_step(step_id: int):
    """
    Delete a preprocessing step record from the database and remove the
    corresponding artifact file/folder from the server's storage.
    """
    await preprocessing_controller.remove_step(step_id=step_id)
    return Success(msg="Preprocessing step deleted successfully")
