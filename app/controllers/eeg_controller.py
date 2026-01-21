
import asyncio
import zipfile
import uuid
import shutil
from pathlib import Path

import mne
from fastapi import UploadFile, HTTPException

from app.core.crud import CRUDBase
from app.models.system.eeg import EEGFile, EEGFormat, ProcessingStatus
from app.schemas.eeg import EEGFileCreate, EEGFileUpdate
from app.settings.config import settings
from app.utils.NDF2MNE.NDFSysMNE import mneNDF
from app.schemas.eeg import EEGFileOut
from app.log import log


class EEGController(CRUDBase[EEGFile, EEGFileCreate, EEGFileUpdate]):
    def __init__(self):
        super().__init__(model=EEGFile)

    async def handle_upload(
        self, *, file: UploadFile, eeg_format: EEGFormat, subject_id: str | None, notes: str | None
    ) -> EEGFile:
        """
        Handles the entire EEG file upload and processing workflow.
        """
        upload_id = str(uuid.uuid4())
        storage_dir = settings.EEG_STORAGE_PATH / upload_id
        storage_dir.mkdir(parents=True, exist_ok=True)
        log.info(f"Initiating upload for file: {file.filename}, assigned UUID: {upload_id}")

        original_filename = file.filename
        if original_filename is None:
            raise HTTPException(status_code=400, detail="Missing original_filename")
        temp_file_path = storage_dir / original_filename
        unzip_dir = storage_dir / "unzipped_ndf"
        log.debug(f"Storage directory: {storage_dir}")
        log.debug(f"Temporary file path: {temp_file_path}")

        initial_data = EEGFileCreate(
            original_filename=original_filename,
            file_size=file.size,
            eeg_format=eeg_format,
            subject_id=subject_id,
            notes=notes,
            storage_path=str(storage_dir.relative_to(settings.EEG_STORAGE_PATH)),
            status=ProcessingStatus.UPLOADED
        )
        eeg_file_record = await self.create(obj_in=initial_data)
        log.info(f"Created initial DB record with ID: {eeg_file_record.id}")

        should_cleanup_temp = False

        # --- Define cleanup logic ---
        def cleanup_files():
            log.info("Running cleanup task...")
            # Delete the unzipped_ndf folder and all its contents
            if unzip_dir.exists():
                log.debug(f"Deleting unzip directory: {unzip_dir}")
                shutil.rmtree(unzip_dir)
            # Delete the original uploaded .zip file
            if should_cleanup_temp and temp_file_path.exists():
                log.debug(f"Deleting temporary file: {temp_file_path}")
                temp_file_path.unlink()
            log.info("Cleanup task finished.")

        try:
            log.info("Saving uploaded file to disk...")
            with temp_file_path.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            log.info(f"File saved to {temp_file_path}")

            await self.update(id=eeg_file_record.id, obj_in={"status": ProcessingStatus.PROCESSING})
            log.info("DB status updated to 'Processing'")

            final_artifact_path: Path
            raw: mne.io.Raw
            
            processing_dir = storage_dir # Default processing dir

            if eeg_format == EEGFormat.NDF:
                log.info("Processing NDF format...")
                if not zipfile.is_zipfile(temp_file_path):
                    raise HTTPException(status_code=400, detail="NDF format requires a ZIP file upload.")
                should_cleanup_temp = True
                
                unzip_dir.mkdir(parents=True, exist_ok=True)
                log.info(f"Starting to unzip {temp_file_path} to {unzip_dir}")
                with zipfile.ZipFile(temp_file_path, 'r') as zip_ref:
                    for member in zip_ref.infolist():
                        name = member.filename
                        if not (member.flag_bits & 0x800):
                            try:
                                name = name.encode("cp437").decode("gbk")
                            except Exception as e:
                                log.warning(f"Could not decode filename '{member.filename}' as GBK, falling back. Error: {e}")
                                name = member.filename

                        log.debug(f"Extracting: '{member.filename}' -> '{name}'")
                        target_path = (unzip_dir / Path(name)).resolve()
                        if not str(target_path).startswith(str(unzip_dir.resolve())):
                            raise HTTPException(status_code=400, detail="Invalid ZIP entry path.")

                        if member.is_dir() or name.endswith("/"):
                            target_path.mkdir(parents=True, exist_ok=True)
                            continue

                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        with zip_ref.open(member) as src, target_path.open("wb") as dst:
                            shutil.copyfileobj(src, dst)
                log.info("Unzipping complete.")

                # --- Find the directory containing the .nfi/.nhf/.nsf file ---
                log.info("Searching for .nfi/.nhf/.nsf files...")
                ndf_root = None
                for pattern in ("*.NHF", "*.nhf", "*.NSF", "*.nsf"):
                    for path in unzip_dir.rglob(pattern):
                        ndf_root = path.parent
                        break
                    if ndf_root:
                        break

                if not ndf_root:
                    for path in unzip_dir.rglob("*.nfi"):
                        ndf_root = path.parent
                        break

                if not ndf_root:
                    raise ValueError("Could not find a .NFI/.NHF/.NSF folder in the extracted archive.")

                log.info(f"Calling NDF converter on directory: {ndf_root}")
                ndf_converter = mneNDF(str(ndf_root))
                raw = await asyncio.to_thread(ndf_converter.read2MneRaw)
                log.info("NDF data successfully converted to MNE Raw object.")
                
                final_artifact_path = storage_dir / f"{upload_id}.fif"
                log.info(f"Saving standardized data to .fif file: {final_artifact_path}")
                await asyncio.to_thread(raw.save, str(final_artifact_path), overwrite=True)
                log.info(".fif file saved successfully.")

            else: # Standard MNE formats
                log.info(f"Processing standard format: {eeg_format.value}")
                final_artifact_path = temp_file_path
                readers = {
                    EEGFormat.EDF: mne.io.read_raw_edf,
                    EEGFormat.BDF: mne.io.read_raw_bdf,
                    EEGFormat.BRAIN_VISION: mne.io.read_raw_brainvision,
                    EEGFormat.EEGLAB: mne.io.read_raw_eeglab,
                    EEGFormat.FIF: mne.io.read_raw_fif,
                }
                reader_func = readers.get(eeg_format)
                if not reader_func:
                    raise HTTPException(status_code=400, detail=f"Standard format {eeg_format.value} is not yet supported for metadata extraction.")
                
                log.info(f"Reading file with reader: {reader_func.__name__}")
                raw = await asyncio.to_thread(reader_func, str(final_artifact_path), preload=False)
                log.info("File read successfully into MNE Raw object.")

            # Extract metadata from MNE raw object and prepare for DB update
            log.info("Extracting metadata from MNE Raw object...")
            update_data = EEGFileUpdate(
                status=ProcessingStatus.COMPLETED,
                storage_path=str(final_artifact_path.relative_to(settings.EEG_STORAGE_PATH)),
                nchan=len(raw.ch_names),
                ch_names=raw.ch_names,
                sfreq=raw.info['sfreq'],
                highpass=raw.info['highpass'],
                lowpass=raw.info['lowpass'],
                line_freq=raw.info.get('line_freq')
            )

            # Update DB record with final info
            await self.update(id=eeg_file_record.id, obj_in=update_data)
            log.info("DB status updated to 'Completed' with extracted metadata.")
        
        except Exception as e:
            # On error, update status and re-raise
            log.exception(f"An error occurred during file processing for record ID {eeg_file_record.id}: {e}")
            await self.update(id=eeg_file_record.id, obj_in={"status": ProcessingStatus.ERROR})
            # IMPORTANT: Re-raising the exception to provide feedback to the frontend
            raise HTTPException(status_code=500, detail=f"An error occurred during file processing: {e}")

        finally:
            # --- This block will run whether the try block succeeded or failed ---
            await asyncio.to_thread(cleanup_files)

        log.info(f"Successfully processed file, returning record ID {eeg_file_record.id}")
        return await self.get(id=eeg_file_record.id)


    async def get_records(self, *, page: int = 1, page_size: int = 10, original_filename: str | None = None, subject_id: str | None = None):
        """
        获取EEG文件记录列表，支持分页和查询
        """
        skip = (page - 1) * page_size
        query = self.model.all()

        if original_filename:
            query = query.filter(original_filename__icontains=original_filename)

        if subject_id:
            query = query.filter(subject_id__icontains=subject_id)

        total = await query.count()
        records = await query.offset(skip).limit(page_size).order_by("-create_time")

        return records, total

    async def remove_eeg_file(self, *, file_id: int) -> None:
        """
        删除EEG文件记录及其关联的物理文件/文件夹
        """
        eeg_record = await self.get(id=file_id)
        if not eeg_record:
            raise HTTPException(status_code=404, detail="EEG file not found")

        # 构建物理文件的绝对路径
        storage_path = settings.EEG_STORAGE_PATH / eeg_record.storage_path
        
        # 为了安全，我们只删除与记录存储路径直接关联的文件或其父目录
        # 这可以防止意外删除整个 eeg_data 目录
        target_path_to_delete = None
        
        # 路径通常是 'uuid/uuid.fif' 或 'uuid/original_name.edf'
        # 我们要删除的是 'uuid' 这个父目录
        if storage_path.parent.name == storage_path.stem:
             target_path_to_delete = storage_path.parent
        else:
             # 对于NDF等复杂情况，也删除其父级UUID目录
             parts = storage_path.parts
             if len(parts) > len(settings.EEG_STORAGE_PATH.parts) + 1:
                 # 获取UUID目录
                 target_path_to_delete = settings.EEG_STORAGE_PATH / parts[len(settings.EEG_STORAGE_PATH.parts)]

        def delete_physical_files():
            if target_path_to_delete and target_path_to_delete.exists():
                print(f"Deleting directory: {target_path_to_delete}")
                shutil.rmtree(target_path_to_delete)

        if target_path_to_delete:
            await asyncio.to_thread(delete_physical_files)

        # 从数据库中删除记录
        await self.remove(id=file_id)

eeg_controller = EEGController()
