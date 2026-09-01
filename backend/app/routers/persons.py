from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File
)
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app import crud, schemas, models
from app.utils.security import get_current_officer
from app.services.file_service import save_person_image


router = APIRouter(
    prefix="/persons",
    tags=["Persons"],
    dependencies=[Depends(get_current_officer)]
)


# ---------- CREATE PERSON ----------

@router.post(
    "/",
    response_model=schemas.PersonResponse
)
def create_person(
    person: schemas.PersonCreate,
    db: Session = Depends(get_db)
):
    return crud.create_person(
        db,
        person
    )


# ---------- GET ALL PERSONS ----------

@router.get(
    "/",
    response_model=List[schemas.PersonResponse]
)
def get_persons(
    db: Session = Depends(get_db)
):
    return crud.get_persons(
        db
    )


# ---------- LINK PERSON TO CASE ----------

@router.post(
    "/link-to-case/",
    response_model=schemas.CasePersonResponse
)
def link_person_to_case(
    link: schemas.CasePersonCreate,
    db: Session = Depends(get_db)
):
    result = crud.link_person_to_case(
        db,
        link
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Case or person not found"
        )

    return result


# ---------- UPLOAD PERSON PHOTO ----------

@router.post(
    "/{person_id}/upload-photo",
    response_model=schemas.PersonResponse
)
def upload_person_photo(
    person_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    person = db.query(
        models.Person
    ).filter(
        models.Person.id == person_id
    ).first()

    if not person:
        raise HTTPException(
            status_code=404,
            detail="Person not found"
        )

    image_path = save_person_image(
        file=file,
        person_id=person.person_id
    )

    person.profile_image_path = (
        image_path
    )

    db.commit()
    db.refresh(person)

    return person


# ---------- GET ONE PERSON ----------

@router.get(
    "/{person_id}",
    response_model=schemas.PersonResponse
)
def get_person(
    person_id: int,
    db: Session = Depends(get_db)
):
    person = crud.get_person_by_id(
        db,
        person_id
    )

    if not person:
        raise HTTPException(
            status_code=404,
            detail="Person not found"
        )

    return person