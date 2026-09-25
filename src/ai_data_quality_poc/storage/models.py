from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ai_data_quality_poc.storage.base import Base


class ServiceRequest(Base):
    __tablename__ = "service_requests"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    recorded_status: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    interaction_notes: Mapped[list[InteractionNote]] = relationship(
        back_populates="service_request"
    )
    quotes: Mapped[list[Quote]] = relationship(back_populates="service_request")
    payments: Mapped[list[Payment]] = relationship(back_populates="service_request")
    assessments: Mapped[list[Assessment]] = relationship(back_populates="service_request")


class InteractionNote(Base):
    __tablename__ = "interaction_notes"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    service_request_id: Mapped[str] = mapped_column(
        ForeignKey("service_requests.id", ondelete="CASCADE"), nullable=False
    )
    note_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    note_category: Mapped[str] = mapped_column(String(64), nullable=False)
    note_text: Mapped[str] = mapped_column(Text, nullable=False)
    author_role: Mapped[str] = mapped_column(String(120), nullable=False)

    service_request: Mapped[ServiceRequest] = relationship(back_populates="interaction_notes")


class Quote(Base):
    __tablename__ = "quotes"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    service_request_id: Mapped[str] = mapped_column(
        ForeignKey("service_requests.id", ondelete="CASCADE"), nullable=False
    )
    quote_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    quote_status: Mapped[str] = mapped_column(String(64), nullable=False)
    amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)

    service_request: Mapped[ServiceRequest] = relationship(back_populates="quotes")


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    service_request_id: Mapped[str] = mapped_column(
        ForeignKey("service_requests.id", ondelete="CASCADE"), nullable=False
    )
    payment_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    payment_status: Mapped[str] = mapped_column(String(64), nullable=False)
    amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)

    service_request: Mapped[ServiceRequest] = relationship(back_populates="payments")


class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    service_request_id: Mapped[str] = mapped_column(
        ForeignKey("service_requests.id", ondelete="CASCADE"), nullable=False
    )
    recorded_status_snapshot: Mapped[str] = mapped_column(String(64), nullable=False)
    recommended_status: Mapped[str] = mapped_column(String(64), nullable=False)
    confidence: Mapped[str] = mapped_column(String(16), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(64), nullable=False)
    rules_version: Mapped[str] = mapped_column(String(64), nullable=False)
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    assessment_status: Mapped[str] = mapped_column(String(16), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    service_request: Mapped[ServiceRequest] = relationship(back_populates="assessments")
    evidence_items: Mapped[list[AssessmentEvidence]] = relationship(back_populates="assessment")
    exceptions: Mapped[list[AssessmentException]] = relationship(back_populates="assessment")
    cost_records: Mapped[list[CostTracking]] = relationship(back_populates="assessment")


class AssessmentEvidence(Base):
    __tablename__ = "assessment_evidence"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    assessment_id: Mapped[str] = mapped_column(
        ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False
    )
    evidence_type: Mapped[str] = mapped_column(String(32), nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    source_id: Mapped[str] = mapped_column(String(64), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)

    assessment: Mapped[Assessment] = relationship(back_populates="evidence_items")


class AssessmentException(Base):
    __tablename__ = "assessment_exceptions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    assessment_id: Mapped[str] = mapped_column(
        ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False
    )
    exception_type: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    assessment: Mapped[Assessment] = relationship(back_populates="exceptions")


class CostTracking(Base):
    __tablename__ = "cost_tracking"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    assessment_id: Mapped[str] = mapped_column(
        ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False
    )
    call_sequence: Mapped[int] = mapped_column(nullable=False)
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    input_tokens: Mapped[int] = mapped_column(nullable=False)
    output_tokens: Mapped[int] = mapped_column(nullable=False)
    cached_input_tokens: Mapped[int | None] = mapped_column(nullable=True)
    input_price_per_million: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    output_price_per_million: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    calculated_cost: Mapped[Decimal] = mapped_column(Numeric(14, 6), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False)
    duration_ms: Mapped[int] = mapped_column(nullable=False)
    call_status: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    assessment: Mapped[Assessment] = relationship(back_populates="cost_records")


Index(
    "ix_interaction_notes_service_request_id_note_timestamp",
    InteractionNote.service_request_id,
    InteractionNote.note_timestamp,
)
Index("ix_quotes_service_request_id", Quote.service_request_id)
Index("ix_payments_service_request_id", Payment.service_request_id)
Index(
    "ix_assessments_service_request_id_created_at",
    Assessment.service_request_id,
    Assessment.created_at,
)
Index("ix_assessment_exceptions_exception_type", AssessmentException.exception_type)
