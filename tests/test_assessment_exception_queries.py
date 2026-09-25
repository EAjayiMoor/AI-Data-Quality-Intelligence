from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from ai_data_quality_poc.services.assessment_engine import run_assessment
from ai_data_quality_poc.services.assessment_persistence import (
    list_exception_counts,
    list_exception_records,
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
from ai_data_quality_poc.storage.models import ServiceRequest


def _build_case_context(service_request_id: str) -> CaseContext:
    return CaseContext(
        service_request=ServiceRequestView(
            id=service_request_id,
            customer_name=f"Customer {service_request_id}",
            recorded_status="quoted",
            created_at=datetime(2026, 5, 1, 9, 0, tzinfo=UTC),
            updated_at=datetime(2026, 5, 1, 10, 0, tzinfo=UTC),
        ),
        interaction_notes=[
            InteractionNoteView(
                id=f"NOTE-{service_request_id}",
                service_request_id=service_request_id,
                note_timestamp=datetime(2026, 5, 1, 10, 30, tzinfo=UTC),
                note_category="customer_contact",
                note_text="Customer requested update and pricing confirmation.",
                author_role="advisor",
            )
        ],
        quotes=[
            QuoteView(
                id=f"Q-{service_request_id}",
                service_request_id=service_request_id,
                quote_timestamp=datetime(2026, 5, 1, 10, 0, tzinfo=UTC),
                quote_status="issued",
                amount=Decimal("500.00"),
            )
        ],
        payments=[
            PaymentView(
                id=f"PAY-{service_request_id}",
                service_request_id=service_request_id,
                payment_timestamp=datetime(2026, 5, 1, 11, 0, tzinfo=UTC),
                payment_status="paid",
                amount=Decimal("500.00"),
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
                created_at=datetime(2026, 5, 1, 9, 0, tzinfo=UTC),
                updated_at=datetime(2026, 5, 1, 10, 0, tzinfo=UTC),
            )
        )
        session.commit()


def test_list_exception_counts_returns_grouped_values() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)

    success_context = _build_case_context("SR-EX-001")
    failed_context = _build_case_context("SR-EX-002")
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

    counts = list_exception_counts(engine=engine)
    count_map = {item.exception_type: item.count for item in counts}

    assert count_map["status_mismatch"] == 1
    assert count_map["assessment_failure"] == 1


def test_list_exception_records_supports_filters() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)

    success_context = _build_case_context("SR-EX-003")
    failed_context = _build_case_context("SR-EX-004")
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

    failed_records = list_exception_records(assessment_status_filter="failed", engine=engine)
    assert len(failed_records) == 1
    assert failed_records[0].exception_type == "assessment_failure"
    assert failed_records[0].assessment_status == "failed"

    mismatch_records = list_exception_records(
        exception_type_filter="status_mismatch",
        confidence_filter="medium",
        engine=engine,
    )
    assert len(mismatch_records) == 1
    assert mismatch_records[0].service_request_id == "SR-EX-003"
    assert mismatch_records[0].assessment_status == "success"


def test_list_exception_counts_supports_status_and_confidence_filters() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)

    success_context = _build_case_context("SR-EX-005")
    failed_context = _build_case_context("SR-EX-006")
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

    failed_counts = list_exception_counts(
        assessment_status_filter="failed",
        engine=engine,
    )
    failed_count_map = {item.exception_type: item.count for item in failed_counts}
    assert failed_count_map == {"assessment_failure": 1}

    medium_counts = list_exception_counts(
        confidence_filter="medium",
        engine=engine,
    )
    medium_count_map = {item.exception_type: item.count for item in medium_counts}
    assert medium_count_map == {"status_mismatch": 1}
