from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from ai_data_quality_poc.services.assessment_engine import run_assessment
from ai_data_quality_poc.services.assessment_persistence import (
    get_executive_metrics,
    list_assessment_run_counts,
    list_assessment_run_records,
    persist_assessment_run,
)
from ai_data_quality_poc.services.case_context import (
    CaseContext,
    InteractionNoteView,
    PaymentView,
    QuoteView,
    ServiceRequestView,
    list_interaction_note_counts,
)
from ai_data_quality_poc.services.llm_adapter import MockAssessmentLLMAdapter
from ai_data_quality_poc.storage.base import Base
from ai_data_quality_poc.storage.models import InteractionNote, ServiceRequest


def _build_case_context(service_request_id: str) -> CaseContext:
    return CaseContext(
        service_request=ServiceRequestView(
            id=service_request_id,
            customer_name=f"Customer {service_request_id}",
            recorded_status="quoted",
            created_at=datetime(2026, 6, 1, 9, 0, tzinfo=UTC),
            updated_at=datetime(2026, 6, 1, 10, 0, tzinfo=UTC),
        ),
        interaction_notes=[
            InteractionNoteView(
                id=f"NOTE-{service_request_id}",
                service_request_id=service_request_id,
                note_timestamp=datetime(2026, 6, 1, 10, 30, tzinfo=UTC),
                note_category="customer_contact",
                note_text="Customer accepted timeline and asked for progress updates.",
                author_role="advisor",
            )
        ],
        quotes=[
            QuoteView(
                id=f"Q-{service_request_id}",
                service_request_id=service_request_id,
                quote_timestamp=datetime(2026, 6, 1, 10, 0, tzinfo=UTC),
                quote_status="issued",
                amount=Decimal("650.00"),
            )
        ],
        payments=[
            PaymentView(
                id=f"PAY-{service_request_id}",
                service_request_id=service_request_id,
                payment_timestamp=datetime(2026, 6, 1, 11, 0, tzinfo=UTC),
                payment_status="paid",
                amount=Decimal("650.00"),
            )
        ],
    )


def _seed_service_request(engine, service_request_id: str) -> None:
    with Session(engine) as session:
        session.add(
            ServiceRequest(
                id=service_request_id,
                customer_name=f"Customer {service_request_id}",
                recorded_status="quoted",
                created_at=datetime(2026, 6, 1, 9, 0, tzinfo=UTC),
                updated_at=datetime(2026, 6, 1, 10, 0, tzinfo=UTC),
            )
        )
        session.add(
            InteractionNote(
                id=f"NOTE-{service_request_id}",
                service_request_id=service_request_id,
                note_timestamp=datetime(2026, 6, 1, 10, 30, tzinfo=UTC),
                note_category="customer_contact",
                note_text="Synthetic note for executive-metric coverage.",
                author_role="advisor",
            )
        )
        session.commit()


def test_get_executive_metrics_returns_zeroes_when_no_assessments() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)

    metrics = get_executive_metrics(engine=engine)

    assert metrics.total_assessments == 0
    assert metrics.total_cases_assessed == 0
    assert metrics.total_notes_assessed == 0
    assert metrics.successful_assessments == 0
    assert metrics.failed_assessments == 0
    assert metrics.total_exceptions == 0
    assert metrics.cases_with_exceptions == 0
    assert metrics.top_exception_type is None
    assert metrics.total_input_tokens == 0
    assert metrics.total_output_tokens == 0
    assert metrics.total_cost == Decimal("0")


def test_get_executive_metrics_aggregates_saved_assessments() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)

    success_context = _build_case_context("SR-EXEC-001")
    failed_context = _build_case_context("SR-EXEC-002")
    _seed_service_request(engine, success_context.service_request.id)
    _seed_service_request(engine, failed_context.service_request.id)

    success_result = run_assessment(success_context, MockAssessmentLLMAdapter(mode="valid"))
    failed_result = run_assessment(failed_context, MockAssessmentLLMAdapter(mode="invalid_status"))

    persist_assessment_run(
        service_request_id=success_context.service_request.id,
        recorded_status_snapshot=success_context.service_request.recorded_status,
        result=success_result,
        engine=engine,
    )
    persist_assessment_run(
        service_request_id=failed_context.service_request.id,
        recorded_status_snapshot=failed_context.service_request.recorded_status,
        result=failed_result,
        engine=engine,
    )

    metrics = get_executive_metrics(engine=engine)

    assert metrics.total_assessments == 2
    assert metrics.total_cases_assessed == 2
    assert metrics.total_notes_assessed == 2
    assert metrics.successful_assessments == 1
    assert metrics.failed_assessments == 1
    assert metrics.total_exceptions == 2
    assert metrics.cases_with_exceptions == 2
    assert metrics.top_exception_type == "assessment_failure"
    assert metrics.total_input_tokens == 1720
    assert metrics.total_output_tokens == 460
    assert metrics.total_cost == Decimal("0.000890")


def test_get_executive_metrics_supports_status_and_confidence_filters() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)

    success_context = _build_case_context("SR-EXEC-003")
    failed_context = _build_case_context("SR-EXEC-004")
    _seed_service_request(engine, success_context.service_request.id)
    _seed_service_request(engine, failed_context.service_request.id)

    success_result = run_assessment(success_context, MockAssessmentLLMAdapter(mode="valid"))
    failed_result = run_assessment(failed_context, MockAssessmentLLMAdapter(mode="invalid_status"))

    persist_assessment_run(
        service_request_id=success_context.service_request.id,
        recorded_status_snapshot=success_context.service_request.recorded_status,
        result=success_result,
        engine=engine,
    )
    persist_assessment_run(
        service_request_id=failed_context.service_request.id,
        recorded_status_snapshot=failed_context.service_request.recorded_status,
        result=failed_result,
        engine=engine,
    )

    success_metrics = get_executive_metrics(
        assessment_status_filter="success",
        engine=engine,
    )
    assert success_metrics.total_assessments == 1
    assert success_metrics.total_cases_assessed == 1
    assert success_metrics.total_notes_assessed == 1
    assert success_metrics.successful_assessments == 1
    assert success_metrics.failed_assessments == 0
    assert success_metrics.total_exceptions == 1
    assert success_metrics.cases_with_exceptions == 1
    assert success_metrics.top_exception_type == "status_mismatch"

    medium_confidence_metrics = get_executive_metrics(
        confidence_filter="medium",
        engine=engine,
    )
    assert medium_confidence_metrics.total_assessments == 1
    assert medium_confidence_metrics.total_cases_assessed == 1
    assert medium_confidence_metrics.total_notes_assessed == 1
    assert medium_confidence_metrics.successful_assessments == 1
    assert medium_confidence_metrics.failed_assessments == 0
    assert medium_confidence_metrics.total_exceptions == 1
    assert medium_confidence_metrics.cases_with_exceptions == 1
    assert medium_confidence_metrics.top_exception_type == "status_mismatch"


def test_list_assessment_run_records_returns_persisted_run_details() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)

    case_context = _build_case_context("SR-EXEC-005")
    _seed_service_request(engine, case_context.service_request.id)

    result = run_assessment(case_context, MockAssessmentLLMAdapter(mode="valid"))
    persist_assessment_run(
        service_request_id=case_context.service_request.id,
        recorded_status_snapshot=case_context.service_request.recorded_status,
        result=result,
        engine=engine,
    )

    records = list_assessment_run_records(
        service_request_id=case_context.service_request.id,
        engine=engine,
    )

    assert len(records) == 1
    run_record = records[0]
    assert run_record.service_request_id == case_context.service_request.id
    assert run_record.assessment_status == "success"
    assert run_record.recommended_status == "accepted_paid"
    assert run_record.evidence_count == 1
    assert run_record.exception_count == 1
    assert run_record.input_tokens == 860
    assert run_record.output_tokens == 230
    assert run_record.duration_ms == 120
    assert run_record.total_cost == Decimal("0.000445")


def test_list_assessment_run_counts_and_note_counts_are_aggregated() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)

    case_context = _build_case_context("SR-EXEC-006")
    _seed_service_request(engine, case_context.service_request.id)

    result = run_assessment(case_context, MockAssessmentLLMAdapter(mode="valid"))
    persist_assessment_run(
        service_request_id=case_context.service_request.id,
        recorded_status_snapshot=case_context.service_request.recorded_status,
        result=result,
        engine=engine,
    )

    run_counts = list_assessment_run_counts(engine=engine)
    note_counts = list_interaction_note_counts(engine=engine)

    assert run_counts[case_context.service_request.id] == 1
    assert note_counts[case_context.service_request.id] == 1
