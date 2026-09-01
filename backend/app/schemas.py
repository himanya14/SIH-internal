from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Any, Dict


# ---------- CASES ----------

class CaseCreate(BaseModel):
    case_id: str
    fir_number: str
    title: str
    offence: str
    police_station: str
    investigating_officer: str
    stage: Optional[str] = "Under Investigation"
    status: Optional[str] = "Active"
    description: Optional[str] = None

    data_origin: Optional[str] = "Synthetic Demo Data"
    synthetic: Optional[bool] = True
    source_reference: Optional[str] = None


class CaseUpdate(BaseModel):
    title: Optional[str] = None
    offence: Optional[str] = None
    police_station: Optional[str] = None
    investigating_officer: Optional[str] = None
    stage: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None

    data_origin: Optional[str] = None
    synthetic: Optional[bool] = None
    source_reference: Optional[str] = None


class CaseResponse(BaseModel):
    id: int

    case_id: str
    fir_number: str
    title: str
    offence: str
    police_station: str
    investigating_officer: str

    stage: str
    status: str
    description: Optional[str] = None

    data_origin: str
    synthetic: bool
    source_reference: Optional[str] = None

    registered_on: datetime
    last_updated: datetime

    class Config:
        from_attributes = True


# ---------- PERSONS ----------

class PersonCreate(BaseModel):
    person_id: str
    name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    role: str
    status: Optional[str] = "Under Investigation"
    profile_image_path: Optional[str] = None


class PersonResponse(PersonCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- CASE-PERSON LINK ----------

class CasePersonCreate(BaseModel):
    case_id: int
    person_id: int
    role_in_case: str


class CasePersonResponse(CasePersonCreate):
    id: int

    class Config:
        from_attributes = True


# ---------- EVIDENCE ----------

class EvidenceCreate(BaseModel):
    evidence_id: str
    case_id: int
    title: str
    evidence_type: str
    description: Optional[str] = None
    file_path: Optional[str] = None
    source: Optional[str] = None
    collected_at: Optional[datetime] = None
    status: Optional[str] = "Collected"


class EvidenceResponse(EvidenceCreate):
    id: int
    collected_by: str
    uploaded_at: datetime

    class Config:
        from_attributes = True


# ---------- CASE DIARY ----------

class CaseDiaryCreate(BaseModel):
    case_id: int
    entry: str
    action_taken: Optional[str] = None


class CaseDiaryResponse(CaseDiaryCreate):
    id: int
    officer_id: str
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- AUTH ----------

class OfficerRegister(BaseModel):
    officer_id: str
    name: str
    designation: str
    police_station: str
    email: Optional[str] = None
    phone: Optional[str] = None
    password: str


class OfficerResponse(BaseModel):
    id: int
    officer_id: str
    name: str
    designation: str
    police_station: str
    email: Optional[str] = None
    phone: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class OfficerLogin(BaseModel):
    officer_id: str
    password: str


# ---------- CHARGESHEET ----------

class ChargesheetCreate(BaseModel):
    chargesheet_id: str
    case_id: int
    legal_provisions: Optional[str] = None
    investigation_summary: Optional[str] = None
    conclusion: Optional[str] = None
    filing_status: Optional[str] = "Draft"


class ChargesheetUpdate(BaseModel):
    legal_provisions: Optional[str] = None
    investigation_summary: Optional[str] = None
    conclusion: Optional[str] = None
    filing_status: Optional[str] = None


class ChargesheetResponse(BaseModel):
    id: int
    chargesheet_id: str
    case_id: int
    legal_provisions: Optional[str] = None
    investigation_summary: Optional[str] = None
    conclusion: Optional[str] = None
    filing_status: str
    prepared_by: str
    prepared_at: datetime
    generated_pdf_path: Optional[str] = None

    class Config:
        from_attributes = True


# ---------- SCANS ----------

class ScanCreate(BaseModel):
    scan_id: str
    case_id: Optional[int] = None
    image_path: str
    matched_person_id: Optional[int] = None
    confidence: Optional[float] = None
    match_status: Optional[str] = "Pending"
    verification_status: Optional[str] = "Unverified"
    source: Optional[str] = None
    device_id: Optional[str] = None


class ScanUpdate(BaseModel):
    matched_person_id: Optional[int] = None
    confidence: Optional[float] = None
    match_status: Optional[str] = None
    verification_status: Optional[str] = None
    source: Optional[str] = None
    device_id: Optional[str] = None


class ScanResponse(BaseModel):
    id: int
    scan_id: str
    case_id: Optional[int] = None
    image_path: str
    matched_person_id: Optional[int] = None
    confidence: Optional[float] = None
    match_status: str
    verification_status: str
    source: Optional[str] = None
    device_id: Optional[str] = None
    officer_id: str
    scanned_at: datetime

    class Config:
        from_attributes = True


# ---------- INTELLIGENCE ENTITIES ----------

class IntelligenceEntityCreate(BaseModel):
    entity_id: str
    case_id: Optional[int] = None
    linked_person_id: Optional[int] = None
    entity_type: str
    label: str
    value: Optional[str] = None
    description: Optional[str] = None
    source: Optional[str] = None
    confidence: Optional[float] = None
    verification_status: Optional[str] = "Unverified"
    data_origin: Optional[str] = "Synthetic"
    synthetic: Optional[bool] = True


class IntelligenceEntityUpdate(BaseModel):
    case_id: Optional[int] = None
    linked_person_id: Optional[int] = None
    entity_type: Optional[str] = None
    label: Optional[str] = None
    value: Optional[str] = None
    description: Optional[str] = None
    source: Optional[str] = None
    confidence: Optional[float] = None
    verification_status: Optional[str] = None
    data_origin: Optional[str] = None
    synthetic: Optional[bool] = None


class IntelligenceEntityResponse(BaseModel):
    id: int
    entity_id: str
    case_id: Optional[int] = None
    linked_person_id: Optional[int] = None
    entity_type: str
    label: str
    value: Optional[str] = None
    description: Optional[str] = None
    source: Optional[str] = None
    confidence: Optional[float] = None
    verification_status: str
    data_origin: str
    synthetic: bool
    created_by: str
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- INTELLIGENCE RELATIONSHIPS ----------

class IntelligenceRelationshipCreate(BaseModel):
    relationship_id: str
    case_id: Optional[int] = None
    source_type: str
    source_ref: str
    target_type: str
    target_ref: str
    relationship_type: str
    description: Optional[str] = None
    confidence: Optional[float] = None
    verification_status: Optional[str] = "Unverified"
    source: Optional[str] = None
    data_origin: Optional[str] = "Synthetic"
    synthetic: Optional[bool] = True


class IntelligenceRelationshipUpdate(BaseModel):
    case_id: Optional[int] = None
    source_type: Optional[str] = None
    source_ref: Optional[str] = None
    target_type: Optional[str] = None
    target_ref: Optional[str] = None
    relationship_type: Optional[str] = None
    description: Optional[str] = None
    confidence: Optional[float] = None
    verification_status: Optional[str] = None
    source: Optional[str] = None
    data_origin: Optional[str] = None
    synthetic: Optional[bool] = None


class IntelligenceRelationshipResponse(BaseModel):
    id: int
    relationship_id: str
    case_id: Optional[int] = None
    source_type: str
    source_ref: str
    target_type: str
    target_ref: str
    relationship_type: str
    description: Optional[str] = None
    confidence: Optional[float] = None
    verification_status: str
    source: Optional[str] = None
    data_origin: str
    synthetic: bool
    created_by: str
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- INTELLIGENCE ANALYSIS ----------

class IntelligenceAnalysisRequest(BaseModel):
    case_id: Optional[int] = None
    text: str
    source_type: Optional[str] = "FIR"


class IntelligenceAnalysisResponse(BaseModel):
    id: int
    case_id: int
    source_type: str
    input_text: str
    result_json: Dict[str, Any]
    created_by: str
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- INTELLIGENCE ALERTS ----------

class IntelligenceAlertUpdate(BaseModel):
    status: Optional[str] = None
    severity: Optional[str] = None


class IntelligenceAlertResponse(BaseModel):
    id: int
    case_id: int
    analysis_id: int
    alert_type: str
    title: str
    description: Optional[str] = None
    severity: str
    status: str
    created_by: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True