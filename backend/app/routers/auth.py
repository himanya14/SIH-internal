from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app import models, schemas
from app.utils.security import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_officer
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


# ---------- REGISTER OFFICER ----------

@router.post(
    "/register",
    response_model=schemas.OfficerResponse
)
def register_officer(
    officer: schemas.OfficerRegister,
    db: Session = Depends(get_db)
):
    existing_officer = db.query(
        models.Officer
    ).filter(
        models.Officer.officer_id
        == officer.officer_id
    ).first()

    if existing_officer:
        raise HTTPException(
            status_code=400,
            detail="Officer ID already registered"
        )

    if officer.email:
        existing_email = db.query(
            models.Officer
        ).filter(
            models.Officer.email
            == officer.email
        ).first()

        if existing_email:
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )

    new_officer = models.Officer(
        officer_id=officer.officer_id,
        name=officer.name,
        designation=officer.designation,
        police_station=officer.police_station,
        email=officer.email,
        phone=officer.phone,
        hashed_password=hash_password(
            officer.password
        )
    )

    try:
        db.add(new_officer)
        db.commit()
        db.refresh(new_officer)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=400,
            detail="Officer account already exists"
        )

    return new_officer


# ---------- LOGIN ----------

@router.post("/login")
def login_officer(
    login: schemas.OfficerLogin,
    db: Session = Depends(get_db)
):
    officer = db.query(
        models.Officer
    ).filter(
        models.Officer.officer_id
        == login.officer_id
    ).first()

    if not officer:
        raise HTTPException(
            status_code=401,
            detail="Invalid Officer ID or password"
        )

    if not verify_password(
        login.password,
        officer.hashed_password
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid Officer ID or password"
        )

    if officer.status != "Active":
        raise HTTPException(
            status_code=403,
            detail="Officer account is inactive"
        )

    access_token = create_access_token(
        officer.officer_id
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "officer": {
            "officer_id": officer.officer_id,
            "name": officer.name,
            "designation": officer.designation,
            "police_station": officer.police_station
        }
    }


# ---------- CURRENT OFFICER ----------

@router.get(
    "/me",
    response_model=schemas.OfficerResponse
)
def get_me(
    current_officer=Depends(
        get_current_officer
    )
):
    return current_officer