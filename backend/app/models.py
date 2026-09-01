from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Text,
    ForeignKey,
    Float,
    Boolean
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


# ---------- CASE ----------

class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)

    case_id = Column(String, unique=True, nullable=False)
    fir_number = Column(String, unique=True, nullable=False)

    title = Column(String, nullable=False)
    offence = Column(String, nullable=False)

    police_station = Column(String, nullable=False)
    investigating_officer = Column(String, nullable=False)

    stage = Column(String, default="Under Investigation")
    status = Column(String, default="Active")

    description = Column(Text, nullable=True)

    registered_on = Column(
        DateTime,
        server_default=func.now()
    )

    last_updated = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now()
    )

    persons = relationship(
        "CasePerson",
        back_populates="case",
        cascade="all, delete-orphan"
    )

    evidence = relationship(
        "Evidence",
        back_populates="case",
        cascade="all, delete-orphan"
    )

    diary_entries = relationship(
        "CaseDiary",
        back_populates="case",
        cascade="all, delete-orphan"
    )

    chargesheets = relationship(
        "Chargesheet",
        back_populates="case",
        cascade="all, delete-orphan"
    )

    scans = relationship(
        "Scan",
        back_populates="case"
    )

    intelligence_entities = relationship(
        "IntelligenceEntity",
        back_populates="case"
    )

    intelligence_relationships = relationship(
        "IntelligenceRelationship",
        back_populates="case"
    )


# ---------- PERSON ----------

class Person(Base):
    __tablename__ = "persons"

    id = Column(Integer, primary_key=True, index=True)

    person_id = Column(
        String,
        unique=True,
        nullable=False
    )

    name = Column(String, nullable=False)
    age = Column(Integer, nullable=True)
    gender = Column(String, nullable=True)

    phone = Column(String, nullable=True)
    address = Column(Text, nullable=True)

    role = Column(String, nullable=False)

    status = Column(
        String,
        default="Under Investigation"
    )

    profile_image_path = Column(
        String,
        nullable=True
    )

    created_at = Column(
        DateTime,
        server_default=func.now()
    )

    cases = relationship(
        "CasePerson",
        back_populates="person",
        cascade="all, delete-orphan"
    )

    scans = relationship(
        "Scan",
        back_populates="matched_person"
    )

    intelligence_entities = relationship(
        "IntelligenceEntity",
        back_populates="linked_person"
    )


# ---------- CASE-PERSON LINK ----------

class CasePerson(Base):
    __tablename__ = "case_persons"

    id = Column(Integer, primary_key=True, index=True)

    case_id = Column(
        Integer,
        ForeignKey("cases.id"),
        nullable=False
    )

    person_id = Column(
        Integer,
        ForeignKey("persons.id"),
        nullable=False
    )

    role_in_case = Column(
        String,
        nullable=False
    )

    case = relationship(
        "Case",
        back_populates="persons"
    )

    person = relationship(
        "Person",
        back_populates="cases"
    )


# ---------- EVIDENCE ----------

class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, index=True)

    evidence_id = Column(
        String,
        unique=True,
        nullable=False
    )

    case_id = Column(
        Integer,
        ForeignKey("cases.id"),
        nullable=False
    )

    title = Column(String, nullable=False)

    evidence_type = Column(
        String,
        nullable=False
    )

    description = Column(
        Text,
        nullable=True
    )

    file_path = Column(
        String,
        nullable=True
    )

    source = Column(
        String,
        nullable=True
    )

    collected_by = Column(
        String,
        nullable=False
    )

    collected_at = Column(
        DateTime,
        nullable=True
    )

    status = Column(
        String,
        default="Collected"
    )

    uploaded_at = Column(
        DateTime,
        server_default=func.now()
    )

    case = relationship(
        "Case",
        back_populates="evidence"
    )


# ---------- CASE DIARY ----------

class CaseDiary(Base):
    __tablename__ = "case_diary"

    id = Column(Integer, primary_key=True, index=True)

    case_id = Column(
        Integer,
        ForeignKey("cases.id"),
        nullable=False
    )

    officer_id = Column(
        String,
        nullable=False
    )

    entry = Column(
        Text,
        nullable=False
    )

    action_taken = Column(
        Text,
        nullable=True
    )

    created_at = Column(
        DateTime,
        server_default=func.now()
    )

    case = relationship(
        "Case",
        back_populates="diary_entries"
    )


# ---------- OFFICER ----------

class Officer(Base):
    __tablename__ = "officers"

    id = Column(Integer, primary_key=True, index=True)

    officer_id = Column(
        String,
        unique=True,
        nullable=False,
        index=True
    )

    name = Column(
        String,
        nullable=False
    )

    designation = Column(
        String,
        nullable=False
    )

    police_station = Column(
        String,
        nullable=False
    )

    email = Column(
        String,
        unique=True,
        nullable=True
    )

    phone = Column(
        String,
        nullable=True
    )

    hashed_password = Column(
        String,
        nullable=False
    )

    status = Column(
        String,
        default="Active"
    )

    created_at = Column(
        DateTime,
        server_default=func.now()
    )


# ---------- CHARGESHEET ----------

class Chargesheet(Base):
    __tablename__ = "chargesheets"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    chargesheet_id = Column(
        String,
        unique=True,
        nullable=False,
        index=True
    )

    case_id = Column(
        Integer,
        ForeignKey("cases.id"),
        nullable=False
    )

    legal_provisions = Column(
        Text,
        nullable=True
    )

    investigation_summary = Column(
        Text,
        nullable=True
    )

    conclusion = Column(
        Text,
        nullable=True
    )

    filing_status = Column(
        String,
        default="Draft"
    )

    prepared_by = Column(
        String,
        nullable=False
    )

    prepared_at = Column(
        DateTime,
        server_default=func.now()
    )

    generated_pdf_path = Column(
        String,
        nullable=True
    )

    case = relationship(
        "Case",
        back_populates="chargesheets"
    )


# ---------- FACE SCAN ----------

class Scan(Base):
    __tablename__ = "scans"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    scan_id = Column(
        String,
        unique=True,
        nullable=False,
        index=True
    )

    case_id = Column(
        Integer,
        ForeignKey("cases.id"),
        nullable=True
    )

    image_path = Column(
        String,
        nullable=False
    )

    matched_person_id = Column(
        Integer,
        ForeignKey("persons.id"),
        nullable=True
    )

    confidence = Column(
        Float,
        nullable=True
    )

    match_status = Column(
        String,
        default="Pending"
    )

    verification_status = Column(
        String,
        default="Unverified"
    )

    source = Column(
        String,
        nullable=True
    )

    device_id = Column(
        String,
        nullable=True
    )

    officer_id = Column(
        String,
        nullable=False
    )

    scanned_at = Column(
        DateTime,
        server_default=func.now()
    )

    case = relationship(
        "Case",
        back_populates="scans"
    )

    matched_person = relationship(
        "Person",
        back_populates="scans"
    )


# ---------- INTELLIGENCE ENTITY ----------

class IntelligenceEntity(Base):
    __tablename__ = "intelligence_entities"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    entity_id = Column(
        String,
        unique=True,
        nullable=False,
        index=True
    )

    case_id = Column(
        Integer,
        ForeignKey("cases.id"),
        nullable=True
    )

    linked_person_id = Column(
        Integer,
        ForeignKey("persons.id"),
        nullable=True
    )

    entity_type = Column(
        String,
        nullable=False
    )

    label = Column(
        String,
        nullable=False
    )

    value = Column(
        String,
        nullable=True
    )

    description = Column(
        Text,
        nullable=True
    )

    source = Column(
        String,
        nullable=True
    )

    confidence = Column(
        Float,
        nullable=True
    )

    verification_status = Column(
        String,
        default="Unverified"
    )

    data_origin = Column(
        String,
        default="Synthetic"
    )

    synthetic = Column(
        Boolean,
        default=True
    )

    created_by = Column(
        String,
        nullable=False
    )

    created_at = Column(
        DateTime,
        server_default=func.now()
    )

    case = relationship(
        "Case",
        back_populates="intelligence_entities"
    )

    linked_person = relationship(
        "Person",
        back_populates="intelligence_entities"
    )


# ---------- INTELLIGENCE RELATIONSHIP ----------

class IntelligenceRelationship(Base):
    __tablename__ = "intelligence_relationships"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    relationship_id = Column(
        String,
        unique=True,
        nullable=False,
        index=True
    )

    case_id = Column(
        Integer,
        ForeignKey("cases.id"),
        nullable=True
    )

    source_type = Column(
        String,
        nullable=False
    )

    source_ref = Column(
        String,
        nullable=False
    )

    target_type = Column(
        String,
        nullable=False
    )

    target_ref = Column(
        String,
        nullable=False
    )

    relationship_type = Column(
        String,
        nullable=False
    )

    description = Column(
        Text,
        nullable=True
    )

    confidence = Column(
        Float,
        nullable=True
    )

    verification_status = Column(
        String,
        default="Unverified"
    )

    source = Column(
        String,
        nullable=True
    )

    data_origin = Column(
        String,
        default="Synthetic"
    )

    synthetic = Column(
        Boolean,
        default=True
    )

    created_by = Column(
        String,
        nullable=False
    )

    created_at = Column(
        DateTime,
        server_default=func.now()
    )

    case = relationship(
        "Case",
        back_populates="intelligence_relationships"
    )