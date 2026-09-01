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
from app.services.analysis_service import run_case_analysis


router = APIRouter(
    prefix="/intelligence",
    tags=["Intelligence"]
)


# ---------- ANALYZE CASE TEXT ----------

@router.post(
    "/analyze"
)
def analyze_intelligence(
    request: schemas.IntelligenceAnalysisRequest,
    db: Session = Depends(get_db),
    current_officer=Depends(get_current_officer)
):
    """
    Analyze FIR, report, or other investigation text
    using the intelligence pipeline.

    Results are analytical indicators only and do not
    establish guilt or legal responsibility.
    """

    if not request.text or not request.text.strip():
        raise HTTPException(
            status_code=400,
            detail="Analysis text cannot be empty"
        )

    if request.case_id is not None:

        case = db.query(
            models.Case
        ).filter(
            models.Case.id == request.case_id
        ).first()

        if not case:
            raise HTTPException(
                status_code=404,
                detail="Case not found"
            )

    try:

        analysis = run_case_analysis(
            text=request.text,
            source_type=request.source_type or "FIR"
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "Intelligence analysis failed: "
                + str(exc)
            )
        )

    return {
        "case_id": request.case_id,
        "source_type": request.source_type or "FIR",
        "analyzed_by": current_officer.officer_id,
        "analysis": analysis
    }


# ---------- CREATE ENTITY ----------

@router.post(
    "/entities",
    response_model=schemas.IntelligenceEntityResponse
)
def create_entity(
    entity: schemas.IntelligenceEntityCreate,
    db: Session = Depends(get_db),
    current_officer=Depends(get_current_officer)
):
    existing_entity = db.query(
        models.IntelligenceEntity
    ).filter(
        models.IntelligenceEntity.entity_id
        == entity.entity_id
    ).first()

    if existing_entity:
        raise HTTPException(
            status_code=400,
            detail="Entity ID already exists"
        )

    if entity.case_id is not None:

        case = db.query(
            models.Case
        ).filter(
            models.Case.id == entity.case_id
        ).first()

        if not case:
            raise HTTPException(
                status_code=404,
                detail="Case not found"
            )

    if entity.linked_person_id is not None:

        person = db.query(
            models.Person
        ).filter(
            models.Person.id
            == entity.linked_person_id
        ).first()

        if not person:
            raise HTTPException(
                status_code=404,
                detail="Linked person not found"
            )

    new_entity = models.IntelligenceEntity(
        **entity.model_dump(),
        created_by=current_officer.officer_id
    )

    db.add(new_entity)
    db.commit()
    db.refresh(new_entity)

    return new_entity


# ---------- GET ALL ENTITIES ----------

@router.get(
    "/entities",
    response_model=List[
        schemas.IntelligenceEntityResponse
    ]
)
def get_entities(
    db: Session = Depends(get_db),
    current_officer=Depends(get_current_officer)
):
    return db.query(
        models.IntelligenceEntity
    ).order_by(
        models.IntelligenceEntity.created_at.desc()
    ).all()


# ---------- GET ENTITIES BY CASE ----------

@router.get(
    "/entities/case/{case_id}",
    response_model=List[
        schemas.IntelligenceEntityResponse
    ]
)
def get_entities_by_case(
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
        models.IntelligenceEntity
    ).filter(
        models.IntelligenceEntity.case_id == case_id
    ).order_by(
        models.IntelligenceEntity.created_at.desc()
    ).all()


# ---------- GET ONE ENTITY ----------

@router.get(
    "/entities/{entity_id}",
    response_model=schemas.IntelligenceEntityResponse
)
def get_entity(
    entity_id: int,
    db: Session = Depends(get_db),
    current_officer=Depends(get_current_officer)
):
    entity = db.query(
        models.IntelligenceEntity
    ).filter(
        models.IntelligenceEntity.id == entity_id
    ).first()

    if not entity:
        raise HTTPException(
            status_code=404,
            detail="Entity not found"
        )

    return entity


# ---------- UPDATE ENTITY ----------

@router.put(
    "/entities/{entity_id}",
    response_model=schemas.IntelligenceEntityResponse
)
def update_entity(
    entity_id: int,
    entity_data: schemas.IntelligenceEntityUpdate,
    db: Session = Depends(get_db),
    current_officer=Depends(get_current_officer)
):
    entity = db.query(
        models.IntelligenceEntity
    ).filter(
        models.IntelligenceEntity.id == entity_id
    ).first()

    if not entity:
        raise HTTPException(
            status_code=404,
            detail="Entity not found"
        )

    update_data = entity_data.model_dump(
        exclude_unset=True
    )

    if "case_id" in update_data:

        case_id = update_data[
            "case_id"
        ]

        if case_id is not None:

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

    if "linked_person_id" in update_data:

        person_id = update_data[
            "linked_person_id"
        ]

        if person_id is not None:

            person = db.query(
                models.Person
            ).filter(
                models.Person.id == person_id
            ).first()

            if not person:
                raise HTTPException(
                    status_code=404,
                    detail="Linked person not found"
                )

    for key, value in update_data.items():

        setattr(
            entity,
            key,
            value
        )

    db.commit()
    db.refresh(entity)

    return entity