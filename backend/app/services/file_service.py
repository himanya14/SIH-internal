import os
import uuid
import shutil
from pathlib import Path

from fastapi import UploadFile, HTTPException


BASE_DIR = Path(__file__).resolve().parents[2]

EVIDENCE_UPLOAD_DIR = BASE_DIR / "uploads" / "evidence"

EVIDENCE_UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True
)


ALLOWED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".pdf",
    ".mp4",
    ".mov",
    ".avi",
    ".mp3",
    ".wav"
}


def save_evidence_file(file: UploadFile) -> str:
    original_filename = file.filename

    if not original_filename:
        raise HTTPException(
            status_code=400,
            detail="File must have a filename"
        )

    extension = Path(
        original_filename
    ).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported evidence file type"
        )

    unique_filename = (
        f"{uuid.uuid4().hex}{extension}"
    )

    physical_file_path = (
        EVIDENCE_UPLOAD_DIR /
        unique_filename
    )

    try:
        with open(
            physical_file_path,
            "wb"
        ) as buffer:
            shutil.copyfileobj(
                file.file,
                buffer
            )

    except Exception:
        if physical_file_path.exists():
            os.remove(physical_file_path)

        raise HTTPException(
            status_code=500,
            detail="Could not save evidence file"
        )

    # Store a frontend-usable URL instead of
    # this computer's local Windows path.
    return (
        f"/uploads/evidence/"
        f"{unique_filename}"
    )