from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app import crud, schemas
from app.utils.security import get_current_officer


router = APIRouter(
    prefix="/persons",
    tags=["Persons"],
    dependencies=[Depends(get_current_officer)]
)


@router.post("/", response_model=schemas.PersonResponse)
def create_person(
    person: schemas.PersonCreate,
    db: Session = Depends(get_db)
):
    return crud.create_person(db, person)


@router.get("/", response_model=List[schemas.PersonResponse])
def get_persons(
    db: Session = Depends(get_db)
):
    return crud.get_persons(db)


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