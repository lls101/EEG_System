from fastapi import UploadFile
from pathlib import Path
import shutil
import uuid
from typing import Dict, Any
from app.core.pd_detection import pd_detector
from app.models.system.pd_detection import PDDetectionResult
import asyncio
import logging

logger = logging.getLogger(__name__)


def save_upload_file_tmp(upload_file: UploadFile, dst_dir: Path) -> Path:
    dst_dir.mkdir(parents=True, exist_ok=True)
    filename = upload_file.filename or ""
    suffix = Path(filename).suffix or ''
    tmp_name = f"{uuid.uuid4().hex}{suffix}"
    out_path = dst_dir / tmp_name
    with out_path.open("wb") as f:
        shutil.copyfileobj(upload_file.file, f)
    return out_path


async def predict_from_uploaded_epochs(upload_file: UploadFile) -> Dict[str, Any]:
    """Save uploaded .fif epochs, run pd_detector.predict, persist to DB, delete tmp file, and return result."""
    tmp_dir = Path.cwd() / "tmp_uploads" / "pd_detection"
    saved = None
    try:
        saved = save_upload_file_tmp(upload_file, tmp_dir)
        logger.info(f"已保存上传文件到: {saved}")

        if not pd_detector.is_model_loaded():
            raise RuntimeError("PD 模型尚未加载")

        # 运行同步推理（模型内部为同步），放到线程池中以免阻塞事件循环
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, pd_detector.predict, str(saved))

        # 将结果写入数据库
        try:
            await PDDetectionResult.create(
                file_name=saved.name,
                model_path=str(pd_detector.model_path),
                overall_prediction=result.get('overall_prediction'),
                confidence=float(result.get('confidence', 0.0)),
                average_probability=float(result.get('average_probability', 0.0)),
                total_epochs=int(result.get('total_epochs', 0)),
                on_epochs=int(result.get('on_epochs', 0)),
                off_epochs=int(result.get('off_epochs', 0)),
                epoch_predictions=result.get('epoch_predictions'),
                epoch_probabilities=result.get('epoch_probabilities')
            )
        except Exception:
            logger.exception("保存 PDDetectionResult 到数据库时失败")

        return result
    finally:
        # 关闭上传文件并删除临时文件
        try:
            upload_file.file.close()
        except Exception:
            pass

        if saved is not None and saved.exists():
            try:
                saved.unlink()
                logger.info(f"已删除临时文件: {saved}")
            except Exception:
                logger.exception(f"删除临时文件失败: {saved}")
