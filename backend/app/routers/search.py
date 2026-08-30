from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app import models
from app.utils.security import get_current_officer


router = APIRouter(
    prefix="/search",
    tags=["Search"],
    dependencies=[Depends(get_current_officer)]
)


@router.get("/")
def search(
    q: str = Query(..., min_length=1),
    db: Session = Depends(get_db)
):
    search_term = f"%{q}%"

    cases = db.query(models.Case).filter(
        or_(
            models.Case.case_id.ilike(search_term),
            models.Case.fir_number.ilike(search_term),
            models.Case.title.ilike(search_term),
            models.Case.offence.ilike(search_term),
            models.Case.police_station.ilike(search_term)
        )
    ).all()

    persons = db.query(models.Person).filter(
        or_(
            models.Person.person_id.ilike(search_term),
            models.Person.name.ilike(search_term),
            models.Person.phone.ilike(search_term)
        )
    ).all()

    evidence = db.query(models.Evidence).filter(
        or_(
            models.Evidence.evidence_id.ilike(search_term),
            models.Evidence.title.ilike(search_term),
            models.Evidence.evidence_type.ilike(search_term),
            models.Evidence.source.ilike(search_term)
        )
    ).all()

    return {
        "query": q,

        "cases": [
            {
                "id": case.id,
                "case_id": case.case_id,
                "fir_number": case.fir_number,
                "title": case.title,
                "offence": case.offence,
                "police_station": case.police_station,
                "stage": case.stage,
                "status": case.status
            }
            for case in cases
        ],

        "persons": [
            {
                "id": person.id,
                "person_id": person.person_id,
                "name": person.name,
                "phone": person.phone,
                "role": person.role,
                "status": person.status
            }
            for person in persons
        ],

        "evidence": [
            {
                "id": item.id,
                "evidence_id": item.evidence_id,
                "case_id": item.case_id,
                "title": item.title,
                "evidence_type": item.evidence_type,
                "source": item.source,
                "status": item.status
            }
            for item in evidence
        ]
    }