import mne
import asyncio
import shutil
from pathlib import Path
import uuid
import numpy as np
import spkit as sp
import time
from typing import List, Tuple
from fastapi import HTTPException
import multiprocessing
import os
import traceback
from tortoise import Tortoise, run_async

from app.core.crud import CRUDBase
from app.log import log
from app.models.system.preprocessing import PreprocessingStep
from app.models.preprocess.wavelet import WaveletDenoise, WaveletTaskStatus
from app.schemas.wavelet import WaveletDenoiseRequest
from app.settings.config import settings

# A dictionary to keep track of running processes
RUNNING_TASKS = {}

def _denoise_worker(task_id: int):
    """The actual denoising function that runs in a separate process."""
    async def main():
        task_start: float | None = None
        # Each process must initialize its own Tortoise ORM instance
        await Tortoise.init(
            config=settings.TORTOISE_ORM
        )
        
        task = await WaveletDenoise.get_or_none(id=task_id).prefetch_related('preprocessing_step')
        if not task:
            return

        try:
            # --- Start Computation ---
            task.status = WaveletTaskStatus.RUNNING
            await task.save(update_fields=['status'])

            artifact_path = settings.EEG_STORAGE_PATH / task.preprocessing_step.artifact_path
            if not artifact_path.exists():
                raise FileNotFoundError(f"Source artifact file not found at {artifact_path}")

            log.info(f"[Wavelet] Loading raw file: {artifact_path}")
            raw = mne.io.read_raw_fif(artifact_path, preload=True)
            X = raw.get_data().T * 1e6

            atar_params = {
                'wv': task.wavelet_name.value,
                'winsize': task.window_size,
                'OptMode': task.optimal_mode.value,
                'beta': task.beta,
                'k1': task.k1,
                'k2': task.k2
            }
            log.info(f"[Wavelet] ATAR start: task_id={task.id}, params={atar_params}")
            task_start = time.perf_counter()
            XR = sp.eeg.ATAR(X, **atar_params)
            elapsed = time.perf_counter() - task_start
            log.info(f"[Wavelet] ATAR done: task_id={task.id}, elapsed={elapsed:.2f}s")
            denoised_data = XR.T / 1e6

            denoised_raw = mne.io.RawArray(denoised_data, raw.info)

            output_path = None
            if task.save_file:
                pipeline_dir = artifact_path.parent
                wavelet_output_dir = pipeline_dir / "wavelet_outputs"
                wavelet_output_dir.mkdir(exist_ok=True)
                cleaned_file_path = wavelet_output_dir / f"{uuid.uuid4()}-wavelet-cleaned.fif"
                log.info(f"[Wavelet] Saving denoised file: {cleaned_file_path}")
                denoised_raw.save(str(cleaned_file_path), overwrite=True)
                output_path = str(cleaned_file_path.relative_to(settings.EEG_STORAGE_PATH))

            task.output_storage_path = output_path
            task.elapsed_seconds = elapsed
            task.status = WaveletTaskStatus.COMPLETED
            await task.save()

        except Exception:
            if task:
                if task_start is not None:
                    task.elapsed_seconds = time.perf_counter() - task_start
                task.status = WaveletTaskStatus.FAILED
                await task.save()
            traceback.print_exc()
        finally:
            # Clean up the database connection in the child process
            await Tortoise.close_connections()

    # Run the async main function in the new process
    run_async(main())

class WaveletController(CRUDBase[WaveletDenoise, None, None]):
    def __init__(self):
        super().__init__(model=WaveletDenoise)

    async def get_task(self, *, task_id: int) -> WaveletDenoise:
        """Gets a task by id."""
        task = await self.model.get_or_none(id=task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found.")
        return task

    async def create_wavelet_task(self, *, preprocessing_step_id: int, params: WaveletDenoiseRequest) -> WaveletDenoise:
        """Creates a new wavelet denoising task with PENDING status."""
        step_record = await PreprocessingStep.get_or_none(id=preprocessing_step_id)
        if not step_record:
            raise HTTPException(status_code=404, detail=f"Preprocessing step with ID {preprocessing_step_id} not found.")

        task = await self.model.create(
            preprocessing_step_id=preprocessing_step_id,
            status=WaveletTaskStatus.PENDING,
            **params.model_dump()
        )
        return task

    async def start_wavelet_task(self, *, task_id: int) -> WaveletDenoise:
        """Starts a wavelet denoising task in a background process."""
        task = await self.model.get_or_none(id=task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found.")
        if task.status == WaveletTaskStatus.RUNNING or task_id in RUNNING_TASKS:
            raise HTTPException(status_code=400, detail="Task is already running.")

        process = multiprocessing.Process(target=_denoise_worker, args=(task.id,))
        process.start()

        RUNNING_TASKS[task.id] = process
        task.task_pid = process.pid
        task.status = WaveletTaskStatus.RUNNING
        await task.save()
        return task

    async def stop_wavelet_task(self, *, task_id: int) -> WaveletDenoise:
        """Stops a running wavelet denoising task."""
        task = await self.model.get_or_none(id=task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found.")
        if task.status != WaveletTaskStatus.RUNNING or task.id not in RUNNING_TASKS:
            raise HTTPException(status_code=400, detail="Task is not currently running.")

        process = RUNNING_TASKS.get(task.id)
        if process and process.is_alive():
            process.terminate() # Send SIGTERM
            process.join()      # Wait for the process to exit

        task.status = WaveletTaskStatus.CANCELLED
        task.task_pid = None
        await task.save()
        
        if task.id in RUNNING_TASKS:
            del RUNNING_TASKS[task.id]

        return task

    async def delete_wavelet_task(self, *, task_id: int):
        """Deletes a task, only if it is not running."""
        task = await self.model.get_or_none(id=task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found.")
        if task.status == WaveletTaskStatus.RUNNING:
            raise HTTPException(status_code=400, detail="Cannot delete a running task. Please stop it first.")
        
        await task.delete()
        return

    async def get_tasks(self) -> List[WaveletDenoise]:
        """Retrieves all non-completed tasks (Pending, Running, etc.)."""
        tasks = await self.model.filter(
            status__in=[WaveletTaskStatus.PENDING, WaveletTaskStatus.RUNNING, WaveletTaskStatus.FAILED, WaveletTaskStatus.CANCELLED]
        ).order_by('-create_time')
        return tasks

    async def get_all_denoised_results(
        self,
        *,
        page: int = 1,
        page_size: int = 10,
        sort_by: str | None = None,
        sort_order: str | None = "desc"
    ) -> Tuple[List[WaveletDenoise], int]:
        """Retrieves a paginated list of all COMPLETED wavelet denoised results."""
        query = self.model.filter(status=WaveletTaskStatus.COMPLETED).prefetch_related("preprocessing_step")

        total = await query.count()

        order_field = sort_by if sort_by and sort_by in self.model._meta.fields_map else 'create_time'
        if sort_order and sort_order.lower() == 'desc':
            order_field = f"-{order_field}"

        records = await query.order_by(order_field).offset((page - 1) * page_size).limit(page_size)

        return records, total

wavelet_controller = WaveletController()
