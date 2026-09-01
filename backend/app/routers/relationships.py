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


router = APIRouter(
    prefix="/relationships",
    tags=["Relationships"]
)


def validate_reference(
    db: Session,
    ref_type: str,
    ref_value: str
):
    normalized_type = ref_type.strip().lower()

    if normalized_type == "person":
        record = db.query(
            models.Person
        ).filter(
            models.Person.person_id == ref_value
        ).first()

        if not record:
            raise HTTPException(
                status_code=404,
                detail=f"Person reference '{ref_value}' not found"
            )

        return record

    if normalized_type == "entity":
        record = db.query(
            models.IntelligenceEntity
        ).filter(
            models.IntelligenceEntity.entity_id == ref_value
        ).first()

        if not record:
            raise HTTPException(
                status_code=404,
                detail=f"Entity reference '{ref_value}' not found"
            )

        return record

    raise HTTPException(
        status_code=400,
        detail="Reference type must be 'Person' or 'Entity'"
    )


# ---------- CREATE RELATIONSHIP ----------

@router.post(
    "/",
    response_model=schemas.IntelligenceRelationshipResponse
)
def create_relationship(
    relationship_data: schemas.IntelligenceRelationshipCreate,
    db: Session = Depends(get_db),
    current_officer=Depends(get_current_officer)
):
    existing_relationship = db.query(
        models.IntelligenceRelationship
    ).filter(
        models.IntelligenceRelationship.relationship_id
        == relationship_data.relationship_id
    ).first()

    if existing_relationship:
        raise HTTPException(
            status_code=400,
            detail="Relationship ID already exists"
        )

    if relationship_data.case_id is not None:
        case = db.query(
            models.Case
        ).filter(
            models.Case.id == relationship_data.case_id
        ).first()

        if not case:
            raise HTTPException(
                status_code=404,
                detail="Case not found"
            )

    validate_reference(
        db=db,
        ref_type=relationship_data.source_type,
        ref_value=relationship_data.source_ref
    )

    validate_reference(
        db=db,
        ref_type=relationship_data.target_type,
        ref_value=relationship_data.target_ref
    )

    if (
        relationship_data.source_type.strip().lower()
        == relationship_data.target_type.strip().lower()
        and relationship_data.source_ref
        == relationship_data.target_ref
    ):
        raise HTTPException(
            status_code=400,
            detail="Source and target cannot be the same record"
        )

    new_relationship = models.IntelligenceRelationship(
        **relationship_data.model_dump(),
        created_by=current_officer.officer_id
    )

    db.add(new_relationship)
    db.commit()
    db.refresh(new_relationship)

    return new_relationship


# ---------- GET ALL RELATIONSHIPS ----------

@router.get(
    "/",
    response_model=List[
        schemas.IntelligenceRelationshipResponse
    ]
)
def get_relationships(
    db: Session = Depends(get_db),
    current_officer=Depends(get_current_officer)
):
    return db.query(
        models.IntelligenceRelationship
    ).order_by(
        models.IntelligenceRelationship.created_at.desc()
    ).all()


# ---------- GET RELATIONSHIPS BY CASE ----------

@router.get(
    "/case/{case_id}",
    response_model=List[
        schemas.IntelligenceRelationshipResponse
    ]
)
def get_relationships_by_case(
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
        models.IntelligenceRelationship
    ).filter(
        models.IntelligenceRelationship.case_id == case_id
    ).order_by(
        models.IntelligenceRelationship.created_at.desc()
    ).all()


# ---------- GET ONE RELATIONSHIP ----------

@router.get(
    "/{relationship_id}",
    response_model=schemas.IntelligenceRelationshipResponse
)
def get_relationship(
    relationship_id: int,
    db: Session = Depends(get_db),
    current_officer=Depends(get_current_officer)
):
    relationship = db.query(
        models.IntelligenceRelationship
    ).filter(
        models.IntelligenceRelationship.id == relationship_id
    ).first()

    if not relationship:
        raise HTTPException(
            status_code=404,
            detail="Relationship not found"
        )

    return relationship


# ---------- UPDATE RELATIONSHIP ----------

@router.put(
    "/{relationship_id}",
    response_model=schemas.IntelligenceRelationshipResponse
)
def update_relationship(
    relationship_id: int,
    relationship_data: schemas.IntelligenceRelationshipUpdate,
    db: Session = Depends(get_db),
    current_officer=Depends(get_current_officer)
):
    relationship = db.query(
        models.IntelligenceRelationship
    ).filter(
        models.IntelligenceRelationship.id == relationship_id
    ).first()

    if not relationship:
        raise HTTPException(
            status_code=404,
            detail="Relationship not found"
        )

    update_data = relationship_data.model_dump(
        exclude_unset=True
    )

    case_id = update_data.get(
        "case_id",
        relationship.case_id
    )

    source_type = update_data.get(
        "source_type",
        relationship.source_type
    )

    source_ref = update_data.get(
        "source_ref",
        relationship.source_ref
    )

    target_type = update_data.get(
        "target_type",
        relationship.target_type
    )

    target_ref = update_data.get(
        "target_ref",
        relationship.target_ref
    )

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

    validate_reference(
        db=db,
        ref_type=source_type,
        ref_value=source_ref
    )

    validate_reference(
        db=db,
        ref_type=target_type,
        ref_value=target_ref
    )

    if (
        source_type.strip().lower()
        == target_type.strip().lower()
        and source_ref == target_ref
    ):
        raise HTTPException(
            status_code=400,
            detail="Source and target cannot be the same record"
        )

    for key, value in update_data.items():
        setattr(
            relationship,
            key,
            value
        )

    db.commit()
    db.refresh(relationship)

    return relationship