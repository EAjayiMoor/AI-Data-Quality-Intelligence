from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from ai_data_quality_poc.services.assessment_contract import (
    AssessmentContractValidationError,
    confidence_label,
    status_label,
    validate_assessment_contract,
)
from ai_data_quality_poc.services.case_context import (
    CaseContext,
    InteractionNoteView,
    PaymentView,
    QuoteView,
    ServiceRequestView,
)


def _build_case_context() -> CaseContext:
    return CaseContext(
        service_request=ServiceRequestView(
            id="SR-1001",
            customer_name="Synthetic Customer",
            recorded_status="quoted",
            created_at=datetime(2026, 1, 1, 9, 0, tzinfo=UTC),
            updated_at=datetime(2026, 1, 2, 9, 0, tzinfo=UTC),
        ),
        interaction_notes=[
            InteractionNoteView(
                id="NOTE-1",
                service_request_id="SR-1001",
                note_timestamp=datetime(2026, 1, 2, 10, 0, tzinfo=UTC),
                note_category="customer_contact",
                note_text="Customer confirmed acceptance by phone.",
                author_role="advisor",
            )
        ],
        quotes=[
            QuoteView(
                id="Q-1",
                service_request_id="SR-1001",
                quote_timestamp=datetime(2026, 1, 2, 9, 0, tzinfo=UTC),
                quote_status="issued",
                amount=Decimal("900.00"),
            )
        ],
        payments=[
            PaymentView(
                id="PAY-1",
                service_request_id="SR-1001",
                payment_timestamp=datetime(2026, 1, 3, 9, 0, tzinfo=UTC),
                payment_status="paid",
                amount=Decimal("900.00"),
            )
        ],
    )


def test_valid_contract_passes() -> None:
    context = _build_case_context()
    raw = {
        "recommended_status": "accepted_paid",
        "confidence": "medium",
        "explanation": "Payment evidence and acceptance note support accepted paid status.",
        "evidence": [
            {
                "evidence_type": "supporting",
                "source_type": "payment",
                "source_id": "PAY-1",
                "explanation": "Payment settled after acceptance.",
            }
        ],
        "missing_evidence": [],
        "exceptions": [
            {
                "exception_type": "status_mismatch",
                "description": "Recorded status remains quoted.",
            }
        ],
    }

    result = validate_assessment_contract(raw, context)
    assert result.recommended_status == "accepted_paid"
    assert status_label(result.recommended_status) == "Accepted paid"
    assert confidence_label(result.confidence) == "Medium"


def test_invalid_status_fails() -> None:
    context = _build_case_context()
    raw = {
        "recommended_status": "done",
        "confidence": "medium",
        "explanation": "Invalid status should fail validation.",
        "evidence": [],
        "missing_evidence": [],
        "exceptions": [],
    }

    with pytest.raises(AssessmentContractValidationError):
        validate_assessment_contract(raw, context)


def test_unknown_evidence_source_id_fails() -> None:
    context = _build_case_context()
    raw = {
        "recommended_status": "accepted_paid",
        "confidence": "high",
        "explanation": "Should fail because unknown note id is referenced.",
        "evidence": [
            {
                "evidence_type": "supporting",
                "source_type": "note",
                "source_id": "NOTE-DOES-NOT-EXIST",
                "explanation": "Invalid evidence reference.",
            }
        ],
        "missing_evidence": [],
        "exceptions": [
            {
                "exception_type": "status_mismatch",
                "description": "Recorded and recommended statuses differ.",
            }
        ],
    }

    with pytest.raises(AssessmentContractValidationError):
        validate_assessment_contract(raw, context)


def test_insufficient_evidence_without_evidence_items_is_allowed() -> None:
    context = _build_case_context()
    raw = {
        "recommended_status": "insufficient_evidence",
        "confidence": "low",
        "explanation": "Available records do not support one lifecycle status with confidence.",
        "evidence": [],
        "missing_evidence": ["No reliable completion marker found."],
        "exceptions": [
            {
                "exception_type": "low_confidence",
                "description": "Evidence is sparse and conflicting.",
            },
            {
                "exception_type": "status_mismatch",
                "description": "Recorded status cannot be verified from available evidence.",
            },
        ],
    }

    result = validate_assessment_contract(raw, context)
    assert result.recommended_status == "insufficient_evidence"
