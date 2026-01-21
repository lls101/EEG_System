
from fastapi import APIRouter, File, Form, UploadFile, Query
import json
from app.controllers.eeg_controller import eeg_controller
from app.models.system.eeg import EEGFormat
from app.schemas.base import Success, ResponseModel
from app.schemas.eeg import EEGFileOut
from app.schemas.base import SuccessExtra
from app.core.dependency import DependAuth

router = APIRouter()


@router.post("/upload", summary="Upload EEG File", response_model=ResponseModel[EEGFileOut],dependencies=[DependAuth])
async def upload_eeg_file(
    file: UploadFile = File(..., description="EEG file or ZIP archive for NDF format"),
    eeg_format: EEGFormat = Form(..., description="The format of the EEG data being uploaded"),
    subject_id: str | None = Form(None, description="Identifier for the subject"),
    notes: str | None = Form(None, description="Notes about the EEG recording")
):
    """
    Handles the upload of an EEG file.

    - **file**: The EEG data file. For NDF format, this must be a ZIP archive.
    - **eeg_format**: The specific format of the EEG data from the provided list.
    - **subject_id**: Optional subject identifier.
    - **notes**: Optional notes.
    """
    eeg_file_record = await eeg_controller.handle_upload(
        file=file, eeg_format=eeg_format, subject_id=subject_id, notes=notes
    )
    response_data = EEGFileOut.model_validate(eeg_file_record)
    # print("=== response_data (Pydantic对象) ===")
    # print(response_data)
    # print("=== response_data.model_dump() (dict) ===")
    # # 先用 model_dump_json 转为 JSON 字符串，再格式化输出
    # print(json.dumps(json.loads(response_data.model_dump_json()), indent=2, ensure_ascii=False))
    # print("=== response_data.model_dump_json() (JSON字符串) ===")
    # print(response_data.model_dump_json())
    # print("=== response_data 类型 ===")
    # print(type(response_data))
    # return Success(data=json.loads(response_data.model_dump_json()))
    return Success(data=json.loads(response_data.model_dump_json()))
    

@router.get("/", summary="Get a list of EEG file records", dependencies=[DependAuth])
async def get_eeg_records(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page"),
    original_filename: str | None = Query(None, description="Filter by original filename (case-insensitive contains)"),
    subject_id: str | None = Query(None, description="Filter by subject ID (case-insensitive contains)")
):
    """
    Retrieve a paginated list of EEG file records.
    Allows filtering by original filename and subject ID.
    """
    records, total = await eeg_controller.get_records(
        page=page, page_size=page_size, original_filename=original_filename, subject_id=subject_id
    )
    
    # 将每个记录转换为 Pydantic 模型
    records_out = [EEGFileOut.from_orm(rec).model_dump(mode='json') for rec in records]
    
    return SuccessExtra(data=records_out, total=total, page=page, page_size=page_size)


@router.get("/{file_id}", summary="Get detailed information for a single EEG file", dependencies=[DependAuth])
async def get_eeg_file_details(file_id: int):
    """
    Retrieve all details for a specific EEG file, including full MNE metadata.
    """
    eeg_record = await eeg_controller.get(id=file_id)
    response_data = EEGFileOut.from_orm(eeg_record)
    return Success(data=response_data.model_dump(mode='json'))


@router.delete("/{file_id}", summary="Delete an EEG file record and its physical data", dependencies=[DependAuth])
async def delete_eeg_file(file_id: int):
    """
    Delete an EEG file record from the database and remove the corresponding
    file or folder from the server's storage.
    """
    await eeg_controller.remove_eeg_file(file_id=file_id)
    return Success(msg="File deleted successfully")
