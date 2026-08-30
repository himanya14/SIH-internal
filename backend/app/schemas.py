from pydantic import BaseModel
from datetime import datetime
from typing import Optional


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


class CaseUpdate(BaseModel):
    title: Optional[str] = None
    offence: Optional[str] = None
    police_station: Optional[str] = None
    investigating_officer: Optional[str] = None
    stage: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None


class CaseResponse(CaseCreate):
    id: int
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