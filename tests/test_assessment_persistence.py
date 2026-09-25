from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from ai_data_quality_poc.services.assessment_engine import run_assessment
from ai_data_quality_poc.services.assessment_persistence import (
    get_latest_assessment_summary,
    persist_assessment_run,
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
from ai_data_quality_poc.storage.models import (
    Assessment,
    AssessmentException,
    CostTracking,
    ServiceRequest,
)


def _build_case_context(service_request_id: str = "SR-PERSIST-001") -> CaseContext:
    return CaseContext(
        service_request=ServiceRequestView(
            id=service_request_id,
            customer_name="Persistence Test Customer",
            recorded_status="quoted",
            created_at=datetime(2026, 3, 1, 9, 0, tzinfo=UTC),
            updated_at=datetime(2026, 3, 1, 10, 0, tzinfo=UTC),
        ),
        interaction_notes=[
            InteractionNoteView(
                id="NOTE-PERSIST-1",
                service_request_id=service_request_id,
                note_timestamp=datetime(2026, 3, 1, 10, 30, tzinfo=UTC),
                note_category="customer_contact",
                note_text="Customer verbally accepted and requested earliest slot.",
                author_role="advisor",
            )
        ],
        quotes=[
            QuoteView(
                id="Q-PERSIST-1",
                service_request_id=service_request_id,
                quote_timestamp=datetime(2026, 3, 1, 10, 0, tzinfo=UTC),
                quote_status="issued",
                amount=Decimal("300.00"),
            )
        ],
        payments=[
            PaymentView(
                id="PAY-PERSIST-1",
                service_request_id=service_request_id,
                payment_timestamp=datetime(2026, 3, 1, 11, 0, tzinfo=UTC),
                payment_status="paid",
                amount=Decimal("300.00"),
            )
        ],
    )


def _seed_service_request(engine, service_request_id: str) -> None:
    with Session(engine) as session:
        session.add(
            ServiceRequest(
                id=service_request_id,
                customer_name="Persistence Test Customer",
                recorded_status="quoted",
                created_at=datetime(2026, 3, 1, 9, 0, tzinfo=UTC),
                updated_at=datetime(2026, 3, 1, 10, 0, tzinfo=UTC),
            )
        )
        session.commit()


def test_persist_assessment_run_saves_success_payload() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)

    case_context = _build_case_context()
    _seed_service_request(engine, case_context.service_request.id)
    result = run_assessment(case_context, MockAssessmentLLMAdapter(mode="valid"))

    assessment_id = persist_assessment_run(
        service_request_id=case_context.service_request.id,
        recorded_status_snapshot=case_context.service_request.recorded_status,
        result=result,
        engine=engine,
    )

    with Session(engine) as session:
        assessment = session.get(Assessment, assessment_id)
        assert assessment is not None
        assert assessment.assessment_status == "success"
        assert assessment.recommended_status == "accepted_paid"

        exceptions = session.query(AssessmentException).filter_by(assessment_id=assessment_id).all()
        assert len(exceptions) == 1
        assert exceptions[0].exception_type == "status_mismatch"

        costs = session.query(CostTracking).filter_by(assessment_id=assessment_id).all()
        assert len(costs) == 1
        assert costs[0].input_tokens == 860
        assert costs[0].output_tokens == 230
        assert costs[0].calculated_cost == Decimal("0.000445")


def test_persist_assessment_run_saves_failure_with_assessment_failure_exception() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)

    case_context = _build_case_context(service_request_id="SR-PERSIST-FAIL-001")
    _seed_service_request(engine, case_context.service_request.id)
    result = run_assessment(case_context, MockAssessmentLLMAdapter(mode="invalid_status"))

    assessment_id = persist_assessment_run(
        service_request_id=case_context.service_request.id,
        recorded_status_snapshot=case_context.service_request.recorded_status,
        result=result,
        engine=engine,
    )

    with Session(engine) as session:
        assessment = session.get(Assessment, assessment_id)
        assert assessment is not None
        assert assessment.assessment_status == "failed"

        failure_exceptions = (
            session.query(AssessmentException).filter_by(assessment_id=assessment_id).all()
        )
        assert len(failure_exceptions) == 1
        assert failure_exceptions[0].exception_type == "assessment_failure"


def test_get_latest_assessment_summary_returns_newest_saved_assessment() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)

    case_context = _build_case_context(service_request_id="SR-PERSIST-LATEST-001")
    _seed_service_request(engine, case_context.service_request.id)

    first_result = run_assessment(case_context, MockAssessmentLLMAdapter(mode="invalid_status"))
    persist_assessment_run(
        service_request_id=case_context.service_request.id,
        recorded_status_snapshot=case_context.service_request.recorded_status,
        result=first_result,
        engine=engine,
    )

    second_result = run_assessment(case_context, MockAssessmentLLMAdapter(mode="valid"))
    persist_assessment_run(
        service_request_id=case_context.service_request.id,
        recorded_status_snapshot=case_context.service_request.recorded_status,
        result=second_result,
        engine=engine,
    )

    summary = get_latest_assessment_summary(case_context.service_request.id, engine=engine)

    assert summary is not None
    assert summary.service_request_id == case_context.service_request.id
    assert summary.assessment_status == "success"
    assert summary.recommended_status == "accepted_paid"
    assert summary.total_cost == Decimal("0.000445")
