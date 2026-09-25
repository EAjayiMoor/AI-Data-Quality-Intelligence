from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from ai_data_quality_poc.services.case_context import (
    CaseContextNotFoundError,
    get_case_context,
    list_service_requests,
)
from ai_data_quality_poc.storage.base import Base
from ai_data_quality_poc.storage.models import InteractionNote, Payment, Quote, ServiceRequest


def _seed_test_case(engine_url: str = "sqlite+pysqlite:///:memory:"):
    engine = create_engine(engine_url, future=True)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        session.add(
            ServiceRequest(
                id="SR-TEST-001",
                customer_name="Synthetic Customer",
                recorded_status="quoted",
                created_at=datetime(2026, 1, 1, 9, 0, tzinfo=UTC),
                updated_at=datetime(2026, 1, 1, 9, 0, tzinfo=UTC),
            )
        )
        session.add(
            ServiceRequest(
                id="SR-TEST-002",
                customer_name="Second Synthetic Customer",
                recorded_status="new",
                created_at=datetime(2026, 1, 7, 9, 0, tzinfo=UTC),
                updated_at=datetime(2026, 1, 7, 9, 0, tzinfo=UTC),
            )
        )

        session.add_all(
            [
                InteractionNote(
                    id="NOTE-3",
                    service_request_id="SR-TEST-001",
                    note_timestamp=datetime(2026, 1, 5, 9, 0, tzinfo=UTC),
                    note_category="delivery_update",
                    note_text="Later timeline note",
                    author_role="field_engineer",
                ),
                InteractionNote(
                    id="NOTE-1",
                    service_request_id="SR-TEST-001",
                    note_timestamp=datetime(2026, 1, 2, 10, 0, tzinfo=UTC),
                    note_category="customer_contact",
                    note_text="Early timeline note",
                    author_role="advisor",
                ),
            ]
        )

        session.add_all(
            [
                Quote(
                    id="Q-2",
                    service_request_id="SR-TEST-001",
                    quote_timestamp=datetime(2026, 1, 4, 9, 0, tzinfo=UTC),
                    quote_status="issued",
                    amount=Decimal("900.00"),
                ),
                Quote(
                    id="Q-1",
                    service_request_id="SR-TEST-001",
                    quote_timestamp=datetime(2026, 1, 3, 9, 0, tzinfo=UTC),
                    quote_status="issued",
                    amount=Decimal("800.00"),
                ),
            ]
        )

        session.add(
            Payment(
                id="PAY-1",
                service_request_id="SR-TEST-001",
                payment_timestamp=datetime(2026, 1, 6, 9, 0, tzinfo=UTC),
                payment_status="paid",
                amount=Decimal("800.00"),
            )
        )

        session.commit()

    return engine


def test_get_case_context_returns_full_ordered_case() -> None:
    engine = _seed_test_case()

    context = get_case_context("SR-TEST-001", engine=engine)

    assert context.service_request.id == "SR-TEST-001"
    assert [note.id for note in context.interaction_notes] == ["NOTE-1", "NOTE-3"]
    assert [quote.id for quote in context.quotes] == ["Q-1", "Q-2"]
    assert [payment.id for payment in context.payments] == ["PAY-1"]


def test_get_case_context_raises_for_missing_service_request() -> None:
    engine = _seed_test_case()

    with pytest.raises(CaseContextNotFoundError):
        get_case_context("SR-DOES-NOT-EXIST", engine=engine)


def test_list_service_requests_returns_latest_first() -> None:
    engine = _seed_test_case()

    service_requests = list_service_requests(engine=engine)

    assert [service_request.id for service_request in service_requests] == [
        "SR-TEST-002",
        "SR-TEST-001",
    ]
