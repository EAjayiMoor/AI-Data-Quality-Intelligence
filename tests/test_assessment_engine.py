from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from ai_data_quality_poc.services.assessment_engine import run_assessment
from ai_data_quality_poc.services.case_context import (
    CaseContext,
    InteractionNoteView,
    PaymentView,
    QuoteView,
    ServiceRequestView,
)
from ai_data_quality_poc.services.llm_adapter import MockAssessmentLLMAdapter


def _build_case_context() -> CaseContext:
    return CaseContext(
        service_request=ServiceRequestView(
            id="SR-2001",
            customer_name="Synthetic Customer",
            recorded_status="quoted",
            created_at=datetime(2026, 2, 1, 9, 0, tzinfo=UTC),
            updated_at=datetime(2026, 2, 2, 9, 0, tzinfo=UTC),
        ),
        interaction_notes=[
            InteractionNoteView(
                id="NOTE-201",
                service_request_id="SR-2001",
                note_timestamp=datetime(2026, 2, 2, 11, 0, tzinfo=UTC),
                note_category="customer_contact",
                note_text="Customer confirmed acceptance in follow-up call.",
                author_role="advisor",
            )
        ],
        quotes=[
            QuoteView(
                id="Q-201",
                service_request_id="SR-2001",
                quote_timestamp=datetime(2026, 2, 2, 9, 30, tzinfo=UTC),
                quote_status="issued",
                amount=Decimal("1200.00"),
            )
        ],
        payments=[
            PaymentView(
                id="PAY-201",
                service_request_id="SR-2001",
                payment_timestamp=datetime(2026, 2, 3, 10, 0, tzinfo=UTC),
                payment_status="paid",
                amount=Decimal("1200.00"),
            )
        ],
    )


def test_run_assessment_success_with_valid_mock() -> None:
    result = run_assessment(_build_case_context(), MockAssessmentLLMAdapter(mode="valid"))

    assert result.kind == "success"
    assert result.contract.recommended_status == "accepted_paid"
    assert result.usage.call_status == "success"


def test_run_assessment_fails_on_invalid_status_contract() -> None:
    result = run_assessment(_build_case_context(), MockAssessmentLLMAdapter(mode="invalid_status"))

    assert result.kind == "failure"
    assert result.error_code == "contract_validation_failed"
    assert result.usage is not None


def test_run_assessment_fails_on_unknown_evidence_id() -> None:
    result = run_assessment(
        _build_case_context(), MockAssessmentLLMAdapter(mode="unknown_evidence")
    )

    assert result.kind == "failure"
    assert result.error_code == "contract_validation_failed"
    assert "Unknown note source_id" in result.message


def test_run_assessment_allows_insufficient_evidence_path() -> None:
    result = run_assessment(_build_case_context(), MockAssessmentLLMAdapter(mode="insufficient"))

    assert result.kind == "success"
    assert result.contract.recommended_status == "insufficient_evidence"
    assert result.contract.confidence == "low"
