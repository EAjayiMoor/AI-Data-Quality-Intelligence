from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from ai_data_quality_poc.storage.db import build_engine
from ai_data_quality_poc.storage.models import InteractionNote, Payment, Quote, ServiceRequest


class CaseContextNotFoundError(ValueError):
    pass


class ServiceRequestView(BaseModel):
    id: str
    customer_name: str
    recorded_status: str
    created_at: datetime
    updated_at: datetime


class ServiceRequestSummary(BaseModel):
    id: str
    customer_name: str
    recorded_status: str
    updated_at: datetime


class InteractionNoteView(BaseModel):
    id: str
    service_request_id: str
    note_timestamp: datetime
    note_category: str
    note_text: str
    author_role: str


class QuoteView(BaseModel):
    id: str
    service_request_id: str
    quote_timestamp: datetime
    quote_status: str
    amount: Decimal | None


class PaymentView(BaseModel):
    id: str
    service_request_id: str
    payment_timestamp: datetime
    payment_status: str
    amount: Decimal | None


class CaseContext(BaseModel):
    service_request: ServiceRequestView
    interaction_notes: list[InteractionNoteView]
    quotes: list[QuoteView]
    payments: list[PaymentView]


def list_service_requests(engine: Engine | None = None) -> list[ServiceRequestSummary]:
    database_engine = engine or build_engine()

    with Session(database_engine) as session:
        service_requests = session.scalars(
            select(ServiceRequest).order_by(
                ServiceRequest.updated_at.desc(), ServiceRequest.id.asc()
            )
        ).all()

    return [
        ServiceRequestSummary(
            id=service_request.id,
            customer_name=service_request.customer_name,
            recorded_status=service_request.recorded_status,
            updated_at=service_request.updated_at,
        )
        for service_request in service_requests
    ]


def get_case_context(service_request_id: str, engine: Engine | None = None) -> CaseContext:
    database_engine = engine or build_engine()

    with Session(database_engine) as session:
        service_request = session.get(ServiceRequest, service_request_id)
        if service_request is None:
            raise CaseContextNotFoundError(f"Service request not found: {service_request_id}")

        interaction_notes = session.scalars(
            select(InteractionNote)
            .where(InteractionNote.service_request_id == service_request_id)
            .order_by(InteractionNote.note_timestamp.asc(), InteractionNote.id.asc())
        ).all()

        quotes = session.scalars(
            select(Quote)
            .where(Quote.service_request_id == service_request_id)
            .order_by(Quote.quote_timestamp.asc(), Quote.id.asc())
        ).all()

        payments = session.scalars(
            select(Payment)
            .where(Payment.service_request_id == service_request_id)
            .order_by(Payment.payment_timestamp.asc(), Payment.id.asc())
        ).all()

    return CaseContext(
        service_request=ServiceRequestView(
            id=service_request.id,
            customer_name=service_request.customer_name,
            recorded_status=service_request.recorded_status,
            created_at=service_request.created_at,
            updated_at=service_request.updated_at,
        ),
        interaction_notes=[
            InteractionNoteView(
                id=note.id,
                service_request_id=note.service_request_id,
                note_timestamp=note.note_timestamp,
                note_category=note.note_category,
                note_text=note.note_text,
                author_role=note.author_role,
            )
            for note in interaction_notes
        ],
        quotes=[
            QuoteView(
                id=quote.id,
                service_request_id=quote.service_request_id,
                quote_timestamp=quote.quote_timestamp,
                quote_status=quote.quote_status,
                amount=quote.amount,
            )
            for quote in quotes
        ],
        payments=[
            PaymentView(
                id=payment.id,
                service_request_id=payment.service_request_id,
                payment_timestamp=payment.payment_timestamp,
                payment_status=payment.payment_status,
                amount=payment.amount,
            )
            for payment in payments
        ],
    )


def list_interaction_note_counts(engine: Engine | None = None) -> dict[str, int]:
    database_engine = engine or build_engine()

    with Session(database_engine) as session:
        rows = session.execute(
            select(
                InteractionNote.service_request_id,
                func.count(InteractionNote.id),
            ).group_by(InteractionNote.service_request_id)
        ).all()

    return {service_request_id: int(count) for service_request_id, count in rows}
