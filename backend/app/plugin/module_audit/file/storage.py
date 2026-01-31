"""
Common helper for persisting uploaded files for the audit module.
"""
from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from datetime import datetime
from fastapi import UploadFile

from app.config.path_conf import UPLOAD_DIR


@dataclass
class SavedFileMeta:
    """Metadata returned after persisting an uploaded file."""

    file_path: str
    original_name: str
    stored_name: str
    file_size: int
    file_extension: str


async def save_upload_file(file: UploadFile, file_type: str, category: str) -> SavedFileMeta:
    """
    Persist an uploaded file under the audit upload directory and return its metadata.

    :param file: Incoming UploadFile instance
    :param file_type: Declared file extension (txt/pdf/json etc.)
    :param category: Logical category folder (e.g. regulation, dataset)
    :return: SavedFileMeta describing the stored file
    """
    today = datetime.now()
    dir_path = os.path.join(
        UPLOAD_DIR,
        "audit",
        category,
        str(today.year),
        f"{today.month:02d}",
        f"{today.day:02d}",
    )
    os.makedirs(dir_path, exist_ok=True)

    normalized_type = (file_type or "bin").strip().lstrip(".").lower()
    extension = f".{normalized_type}" if normalized_type else ""
    stored_name = f"{uuid.uuid4()}{extension}"
    file_path = os.path.join(dir_path, stored_name)

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    # reset stream pointer so callers can re-read if necessary
    try:
        await file.seek(0)
    except Exception:
        pass

    return SavedFileMeta(
        file_path=file_path,
        original_name=file.filename,
        stored_name=stored_name,
        file_size=len(content),
        file_extension=normalized_type,
    )
