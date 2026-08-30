from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app import crud, schemas, models
from app.utils.security import get_current_officer


router = APIRouter(
    prefix="/cases",
    tags=["Cases"],
    dependencies=[Depends(get_current_officer)]
)


@router.post("/", response_model=schemas.CaseResponse)
def create_case(
    case: schemas.CaseCreate,
    db: Session = Depends(get_db)
):
    return crud.create_case(db, case)


@router.get("/", response_model=List[schemas.CaseResponse])
def get_cases(
    db: Session = Depends(get_db)
):
    return crud.get_cases(db)


@router.get(
    "/{case_id}",
    response_model=schemas.CaseResponse
)
def get_case(
    case_id: int,
    db: Session = Depends(get_db)
):
    case = crud.get_case_by_id(db, case_id)

    if not case:
        raise HTTPException(
            status_code=404,
            detail="Case not found"
        )

    return case


@router.put(
    "/{case_id}",
    response_model=schemas.CaseResponse
)
def update_case(
    case_id: int,
    case_data: schemas.CaseUpdate,
    db: Session = Depends(get_db)
):
    case = crud.update_case(
        db,
        case_id,
        case_data
    )

    if not case:
        raise HTTPException(
            status_code=404,
            detail="Case not found"
        )

    return case