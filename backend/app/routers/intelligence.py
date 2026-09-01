from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)
from sqlalchemy.orm import Session
from typing import List
import json

from app.database import get_db
from app import models, schemas
from app.utils.security import get_current_officer
from app.services.analysis_service import run_case_analysis


router = APIRouter(
    prefix="/intelligence",
    tags=["Intelligence"]
)


# ---------- HELPER: CONVERT VALUE TO TEXT ----------

def value_to_text(value):
    if value is None:
        return None

    if isinstance(value, str):
        return value

    if isinstance(value, (dict, list)):
        return json.dumps(
            value,
            ensure_ascii=False
        )

    return str(value)


# ---------- HELPER: SAVE AI ALERTS ----------

def save_analysis_alerts(
    db: Session,
    analysis_result: dict,
    saved_analysis: models.IntelligenceAnalysis,
    officer_id: str
):
    """
    Save alerts returned by the intelligence pipeline.

    Alert formats may evolve on the AI side, so this
    function accepts several common field names.
    """

    alerts = analysis_result.get(
        "alerts",
        []
    )

    if not isinstance(alerts, list):
        return

    for alert in alerts:

        # ---------------------------------------------
        # ALERT RETURNED AS PLAIN TEXT
        # ---------------------------------------------

        if isinstance(alert, str):

            new_alert = models.IntelligenceAlert(
                case_id=saved_analysis.case_id,
                analysis_id=saved_analysis.id,
                alert_type="Intelligence Alert",
                title=alert,
                description=None,
                severity="Medium",
                status="Open",
                created_by=officer_id
            )

            db.add(new_alert)

            continue

        # ---------------------------------------------
        # ALERT RETURNED AS DICTIONARY
        # ---------------------------------------------

        if not isinstance(alert, dict):
            continue

        alert_type = (
            alert.get("alert_type")
            or alert.get("type")
            or alert.get("category")
            or "Intelligence Alert"
        )

        severity = (
            alert.get("severity")
            or alert.get("level")
            or alert.get("priority")
            or "Medium"
        )

        title = (
            alert.get("title")
            or alert.get("message")
            or alert.get("alert")
            or alert_type
        )

        description = (
            alert.get("description")
            or alert.get("details")
            or alert.get("evidence")
            or alert.get("reason")
        )

        new_alert = models.IntelligenceAlert(
            case_id=saved_analysis.case_id,
            analysis_id=saved_analysis.id,
            alert_type=value_to_text(
                alert_type
            ),
            title=value_to_text(
                title
            ),
            description=value_to_text(
                description
            ),
            severity=value_to_text(
                severity
            ),
            status="Open",
            created_by=officer_id
        )

        db.add(new_alert)


# ---------- ANALYZE AND SAVE CASE TEXT ----------

@router.post(
    "/analyze",
    response_model=schemas.IntelligenceAnalysisResponse
)
def analyze_intelligence(
    request: schemas.IntelligenceAnalysisRequest,
    db: Session = Depends(get_db),
    current_officer=Depends(get_current_officer)
):
    """
    Analyze FIR, report, or other investigation text,
    save the complete intelligence analysis, and store
    any alerts produced by the intelligence pipeline.

    Results are analytical indicators only and do not
    establish guilt or legal responsibility.
    """

    if not request.text or not request.text.strip():

        raise HTTPException(
            status_code=400,
            detail="Analysis text cannot be empty"
        )

    if request.case_id is None:

        raise HTTPException(
            status_code=400,
            detail="Case ID is required to save analysis"
        )

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

    # ---------------------------------------------
    # RUN INTELLIGENCE PIPELINE
    # ---------------------------------------------

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

    # ---------------------------------------------
    # CREATE ANALYSIS RECORD
    # ---------------------------------------------

    saved_analysis = models.IntelligenceAnalysis(
        case_id=request.case_id,
        source_type=request.source_type or "FIR",
        input_text=request.text.strip(),
        result_json=analysis,
        created_by=current_officer.officer_id
    )

    try:

        db.add(saved_analysis)

        # Gives saved_analysis its database ID
        # before alerts are created.
        db.flush()

        # -----------------------------------------
        # SAVE ALERTS RETURNED BY AI
        # -----------------------------------------

        save_analysis_alerts(
            db=db,
            analysis_result=analysis,
            saved_analysis=saved_analysis,
            officer_id=current_officer.officer_id
        )

        db.commit()
        db.refresh(saved_analysis)

    except Exception:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to save intelligence analysis "
                "and alerts"
            )
        )

    return saved_analysis


# ---------- GET ANALYSES BY CASE ----------

@router.get(
    "/analysis/case/{case_id}",
    response_model=List[
        schemas.IntelligenceAnalysisResponse
    ]
)
def get_case_analyses(
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
        models.IntelligenceAnalysis
    ).filter(
        models.IntelligenceAnalysis.case_id == case_id
    ).order_by(
        models.IntelligenceAnalysis.created_at.desc()
    ).all()


# ---------- GET ONE ANALYSIS ----------

@router.get(
    "/analysis/{analysis_id}",
    response_model=schemas.IntelligenceAnalysisResponse
)
def get_analysis(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_officer=Depends(get_current_officer)
):
    analysis = db.query(
        models.IntelligenceAnalysis
    ).filter(
        models.IntelligenceAnalysis.id == analysis_id
    ).first()

    if not analysis:

        raise HTTPException(
            status_code=404,
            detail="Intelligence analysis not found"
        )

    return analysis


# ---------- GET ALL ALERTS ----------

@router.get(
    "/alerts",
    response_model=List[
        schemas.IntelligenceAlertResponse
    ]
)
def get_alerts(
    db: Session = Depends(get_db),
    current_officer=Depends(get_current_officer)
):
    return db.query(
        models.IntelligenceAlert
    ).order_by(
        models.IntelligenceAlert.created_at.desc()
    ).all()


# ---------- GET ALERTS BY CASE ----------

@router.get(
    "/alerts/case/{case_id}",
    response_model=List[
        schemas.IntelligenceAlertResponse
    ]
)
def get_alerts_by_case(
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
        models.IntelligenceAlert
    ).filter(
        models.IntelligenceAlert.case_id == case_id
    ).order_by(
        models.IntelligenceAlert.created_at.desc()
    ).all()


# ---------- UPDATE ALERT ----------

@router.put(
    "/alerts/{alert_id}",
    response_model=schemas.IntelligenceAlertResponse
)
def update_alert(
    alert_id: int,
    alert_data: schemas.IntelligenceAlertUpdate,
    db: Session = Depends(get_db),
    current_officer=Depends(get_current_officer)
):
    alert = db.query(
        models.IntelligenceAlert
    ).filter(
        models.IntelligenceAlert.id == alert_id
    ).first()

    if not alert:

        raise HTTPException(
            status_code=404,
            detail="Intelligence alert not found"
        )

    update_data = alert_data.model_dump(
        exclude_unset=True
    )

    for key, value in update_data.items():

        setattr(
            alert,
            key,
            value
        )

    try:

        db.commit()
        db.refresh(alert)

    except Exception:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Failed to update intelligence alert"
        )

    return alert


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