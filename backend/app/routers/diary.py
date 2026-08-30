from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app import models, schemas
from app.utils.security import get_current_officer


router = APIRouter(
    prefix="/diary",
    tags=["Case Diary"]
)


# ---------- CREATE DIARY ENTRY ----------

@router.post(
    "/",
    response_model=schemas.CaseDiaryResponse
)
def create_diary_entry(
    diary: schemas.CaseDiaryCreate,
    db: Session = Depends(get_db),
    current_officer=Depends(get_current_officer)
):
    case = db.query(
        models.Case
    ).filter(
        models.Case.id == diary.case_id
    ).first()

    if not case:
        raise HTTPException(
            status_code=404,
            detail="Case not found"
        )

    diary_data = diary.model_dump()

    # Always use the authenticated officer.
    diary_data["officer_id"] = (
        current_officer.officer_id
    )

    new_entry = models.CaseDiary(
        **diary_data
    )

    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)

    return new_entry


# ---------- GET DIARY BY CASE ----------

@router.get(
    "/case/{case_id}",
    response_model=List[schemas.CaseDiaryResponse]
)
def get_case_diary(
    case_id: int,
    db: Session = Depends(get_db),
    current_officer=Depends(get_current_officer)
):
    case = db.query(
        models.Case
    ).filter(
        models.Case.id == case_id
    ).first()

    if not case:
        raise HTTPException(
            status_code=404,
            detail="Case not found"
        )

    return db.query(
        models.CaseDiary
    ).filter(
        models.CaseDiary.case_id == case_id
    ).order_by(
        models.CaseDiary.created_at.desc()
    ).all()


# ---------- GET ONE DIARY ENTRY ----------

@router.get(
    "/{diary_id}",
    response_model=schemas.CaseDiaryResponse
)
def get_diary_entry(
    diary_id: int,
    db: Session = Depends(get_db),
    current_officer=Depends(get_current_officer)
):
    entry = db.query(
        models.CaseDiary
    ).filter(
        models.CaseDiary.id == diary_id
    ).first()

    if not entry:
        raise HTTPException(
            status_code=404,
            detail="Diary entry not found"
        )

    return entry