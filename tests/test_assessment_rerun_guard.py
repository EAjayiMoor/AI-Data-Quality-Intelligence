from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from ai_data_quality_poc.services.assessment_engine import run_assessment
from ai_data_quality_poc.services.assessment_persistence import (
    persist_assessment_run,
    should_run_assessment,
)
from ai_data_quality_poc.services.case_context import (
    CaseContext,
    InteractionNoteView,
    PaymentView,
    QuoteView,
    ServiceRequestView,
)
from ai_data_quality_poc.services.llm_adapter import MockAssessmentLLMAdapter
from ai_data_quality_poc.storage.base import Base
from ai_data_quality_poc.storage.models import ServiceRequest


def _build_case_context(service_request_id: str = "SR-GUARD-001") -> CaseContext:
    return CaseContext(
        service_request=ServiceRequestView(
            id=service_request_id,
            customer_name="Rerun Guard Customer",
            recorded_status="quoted",
            created_at=datetime(2026, 4, 1, 9, 0, tzinfo=UTC),
            updated_at=datetime(2026, 4, 1, 10, 0, tzinfo=UTC),
        ),
        interaction_notes=[
            InteractionNoteView(
                id="NOTE-GUARD-1",
                service_request_id=service_request_id,
                note_timestamp=datetime(2026, 4, 1, 10, 30, tzinfo=UTC),
                note_category="customer_contact",
                note_text="Customer requested scheduling update.",
                author_role="advisor",
            )
        ],
        quotes=[
            QuoteView(
                id="Q-GUARD-1",
                service_request_id=service_request_id,
                quote_timestamp=datetime(2026, 4, 1, 10, 0, tzinfo=UTC),
                quote_status="issued",
                amount=Decimal("450.00"),
            )
        ],
        payments=[
            PaymentView(
                id="PAY-GUARD-1",
                service_request_id=service_request_id,
                payment_timestamp=datetime(2026, 4, 1, 11, 0, tzinfo=UTC),
                payment_status="paid",
                amount=Decimal("450.00"),
            )
        ],
    )


def _seed_service_request(engine, service_request_id: str) -> None:
    with Session(engine) as session:
        session.add(
            ServiceRequest(
                id=service_request_id,
                customer_name="Rerun Guard Customer",
                recorded_status="quoted",
                created_at=datetime(2026, 4, 1, 9, 0, tzinfo=UTC),
                updated_at=datetime(2026, 4, 1, 10, 0, tzinfo=UTC),
            )
        )
        session.commit()


def test_should_run_assessment_when_no_prior_assessment_exists() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)

    case_context = _build_case_context()
    _seed_service_request(engine, case_context.service_request.id)

    decision = should_run_assessment(
        service_request_id=case_context.service_request.id,
        case_context=case_context,
        engine=engine,
    )

    assert decision.should_run is True
    assert decision.reason == "no_prior_assessment"


def test_should_skip_rerun_when_no_data_change_detected() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)

    case_context = _build_case_context(service_request_id="SR-GUARD-002")
    _seed_service_request(engine, case_context.service_request.id)

    result = run_assessment(case_context, MockAssessmentLLMAdapter(mode="valid"))
    persist_assessment_run(
        service_request_id=case_context.service_request.id,
        recorded_status_snapshot=case_context.service_request.recorded_status,
        result=result,
        engine=engine,
    )

    decision = should_run_assessment(
        service_request_id=case_context.service_request.id,
        case_context=case_context,
        engine=engine,
    )

    assert decision.should_run is False
    assert decision.reason == "no_data_change_detected"


def test_should_run_when_data_changed_since_latest_assessment() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)

    case_context = _build_case_context(service_request_id="SR-GUARD-003")
    _seed_service_request(engine, case_context.service_request.id)

    result = run_assessment(case_context, MockAssessmentLLMAdapter(mode="valid"))
    persist_assessment_run(
        service_request_id=case_context.service_request.id,
        recorded_status_snapshot=case_context.service_request.recorded_status,
        result=result,
        engine=engine,
    )

    changed_context = case_context.model_copy(deep=True)
    changed_context.interaction_notes[0].note_timestamp = datetime.now(UTC) + timedelta(minutes=1)

    decision = should_run_assessment(
        service_request_id=case_context.service_request.id,
        case_context=changed_context,
        engine=engine,
    )

    assert decision.should_run is True
    assert decision.reason == "data_changed_since_last_assessment"


def test_force_rerun_bypasses_change_guard() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)

    case_context = _build_case_context(service_request_id="SR-GUARD-004")
    _seed_service_request(engine, case_context.service_request.id)

    result = run_assessment(case_context, MockAssessmentLLMAdapter(mode="valid"))
    persist_assessment_run(
        service_request_id=case_context.service_request.id,
        recorded_status_snapshot=case_context.service_request.recorded_status,
        result=result,
        engine=engine,
    )

    decision = should_run_assessment(
        service_request_id=case_context.service_request.id,
        case_context=case_context,
        force_rerun=True,
        engine=engine,
    )

    assert decision.should_run is True
    assert decision.reason == "forced_rerun"
