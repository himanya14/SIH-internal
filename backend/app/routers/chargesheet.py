from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app import models, schemas
from app.utils.security import get_current_officer
from app.services.chargesheet_service import (
    generate_chargesheet_pdf
)


router = APIRouter(
    prefix="/chargesheets",
    tags=["Chargesheets"]
)


# ---------- CREATE CHARGESHEET ----------

@router.post(
    "/",
    response_model=schemas.ChargesheetResponse
)
def create_chargesheet(
    chargesheet: schemas.ChargesheetCreate,
    db: Session = Depends(get_db),
    current_officer=Depends(get_current_officer)
):
    case = db.query(
        models.Case
    ).filter(
        models.Case.id == chargesheet.case_id
    ).first()

    if not case:
        raise HTTPException(
            status_code=404,
            detail="Case not found"
        )

    existing_chargesheet = db.query(
        models.Chargesheet
    ).filter(
        models.Chargesheet.chargesheet_id
        == chargesheet.chargesheet_id
    ).first()

    if existing_chargesheet:
        raise HTTPException(
            status_code=400,
            detail="Chargesheet ID already exists"
        )

    chargesheet_data = chargesheet.model_dump()

    # Always use the authenticated officer.
    chargesheet_data["prepared_by"] = (
        current_officer.officer_id
    )

    new_chargesheet = models.Chargesheet(
        **chargesheet_data
    )

    db.add(new_chargesheet)
    db.commit()
    db.refresh(new_chargesheet)

    return new_chargesheet


# ---------- GET ALL CHARGESHEETS ----------

@router.get(
    "/",
    response_model=List[schemas.ChargesheetResponse]
)
def get_chargesheets(
    db: Session = Depends(get_db),
    current_officer=Depends(get_current_officer)
):
    return db.query(
        models.Chargesheet
    ).order_by(
        models.Chargesheet.prepared_at.desc()
    ).all()


# ---------- GET CHARGESHEETS BY CASE ----------

@router.get(
    "/case/{case_id}",
    response_model=List[schemas.ChargesheetResponse]
)
def get_chargesheets_by_case(
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
        models.Chargesheet
    ).filter(
        models.Chargesheet.case_id == case_id
    ).order_by(
        models.Chargesheet.prepared_at.desc()
    ).all()


# ---------- GENERATE CHARGESHEET PDF ----------

@router.post(
    "/{chargesheet_id}/generate-pdf",
    response_model=schemas.ChargesheetResponse
)
def generate_pdf(
    chargesheet_id: int,
    db: Session = Depends(get_db),
    current_officer=Depends(get_current_officer)
):
    chargesheet = db.query(
        models.Chargesheet
    ).filter(
        models.Chargesheet.id == chargesheet_id
    ).first()

    if not chargesheet:
        raise HTTPException(
            status_code=404,
            detail="Chargesheet not found"
        )

    case = db.query(
        models.Case
    ).filter(
        models.Case.id == chargesheet.case_id
    ).first()

    if not case:
        raise HTTPException(
            status_code=404,
            detail="Case not found"
        )

    persons = db.query(
        models.CasePerson
    ).filter(
        models.CasePerson.case_id == case.id
    ).all()

    evidence = db.query(
        models.Evidence
    ).filter(
        models.Evidence.case_id == case.id
    ).all()

    file_path = generate_chargesheet_pdf(
        chargesheet=chargesheet,
        case=case,
        persons=persons,
        evidence=evidence
    )

    chargesheet.generated_pdf_path = file_path

    db.commit()
    db.refresh(chargesheet)

    return chargesheet


# ---------- GET ONE CHARGESHEET ----------

@router.get(
    "/{chargesheet_id}",
    response_model=schemas.ChargesheetResponse
)
def get_chargesheet(
    chargesheet_id: int,
    db: Session = Depends(get_db),
    current_officer=Depends(get_current_officer)
):
    chargesheet = db.query(
        models.Chargesheet
    ).filter(
        models.Chargesheet.id == chargesheet_id
    ).first()

    if not chargesheet:
        raise HTTPException(
            status_code=404,
            detail="Chargesheet not found"
        )

    return chargesheet


# ---------- UPDATE CHARGESHEET ----------

@router.put(
    "/{chargesheet_id}",
    response_model=schemas.ChargesheetResponse
)
def update_chargesheet(
    chargesheet_id: int,
    chargesheet_data: schemas.ChargesheetUpdate,
    db: Session = Depends(get_db),
    current_officer=Depends(get_current_officer)
):
    chargesheet = db.query(
        models.Chargesheet
    ).filter(
        models.Chargesheet.id == chargesheet_id
    ).first()

    if not chargesheet:
        raise HTTPException(
            status_code=404,
            detail="Chargesheet not found"
        )

    update_data = chargesheet_data.model_dump(
        exclude_unset=True
    )

    # Never allow the request to change the officer.
    update_data.pop(
        "prepared_by",
        None
    )

    for key, value in update_data.items():
        setattr(
            chargesheet,
            key,
            value
        )

    db.commit()
    db.refresh(chargesheet)

    return chargesheet