from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from ai_data_quality_poc.services.case_context import (
    CaseContext,
    InteractionNoteView,
    PaymentView,
    QuoteView,
    ServiceRequestView,
)
from ai_data_quality_poc.services.llm_adapter import (
    LiveAssessmentLLMAdapter,
    is_live_llm_configured,
    normalize_live_payload,
)


def _build_case_context() -> CaseContext:
    return CaseContext(
        service_request=ServiceRequestView(
            id="SR-LIVE-001",
            customer_name="Customer Live",
            recorded_status="quoted",
            created_at=datetime(2026, 1, 1, 9, 0, tzinfo=UTC),
            updated_at=datetime(2026, 1, 1, 10, 0, tzinfo=UTC),
        ),
        interaction_notes=[
            InteractionNoteView(
                id="NOTE-1001",
                service_request_id="SR-LIVE-001",
                note_timestamp=datetime(2026, 1, 1, 10, 30, tzinfo=UTC),
                note_category="customer_contact",
                note_text="Customer requested revised timeline.",
                author_role="advisor",
            )
        ],
        quotes=[
            QuoteView(
                id="Q-1001",
                service_request_id="SR-LIVE-001",
                quote_timestamp=datetime(2026, 1, 1, 11, 0, tzinfo=UTC),
                quote_status="issued",
                amount=Decimal("500.00"),
            )
        ],
        payments=[
            PaymentView(
                id="PAY-1001",
                service_request_id="SR-LIVE-001",
                payment_timestamp=datetime(2026, 1, 1, 12, 0, tzinfo=UTC),
                payment_status="paid",
                amount=Decimal("500.00"),
            )
        ],
    )


def test_is_live_llm_configured_returns_false_when_api_values_missing(monkeypatch) -> None:
    monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_BASE_URL", raising=False)

    assert is_live_llm_configured() is False


def test_is_live_llm_configured_returns_true_when_required_values_present(monkeypatch) -> None:
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("AZURE_OPENAI_BASE_URL", "https://example.test/openai/v1")

    assert is_live_llm_configured() is True


def test_live_adapter_from_env_requires_api_key(monkeypatch) -> None:
    monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("AZURE_OPENAI_BASE_URL", "https://example.test/openai/v1")

    with pytest.raises(ValueError, match="AZURE_OPENAI_API_KEY"):
        LiveAssessmentLLMAdapter.from_env()


def test_live_adapter_from_env_requires_base_url(monkeypatch) -> None:
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "test-key")
    monkeypatch.delenv("AZURE_OPENAI_BASE_URL", raising=False)

    with pytest.raises(ValueError, match="AZURE_OPENAI_BASE_URL"):
        LiveAssessmentLLMAdapter.from_env()


def test_live_adapter_from_env_builds_azure_configured_adapter(monkeypatch) -> None:
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("AZURE_OPENAI_BASE_URL", "https://example.test/openai/v1")
    monkeypatch.setenv("LLM_TIMEOUT_SECONDS", "45")

    adapter = LiveAssessmentLLMAdapter.from_env()

    assert adapter.api_key == "test-key"
    assert adapter.model == "gpt-5.3-codex-Emmanuel-Ajayi"
    assert adapter.endpoint_url == "https://example.test/openai/v1/responses"
    assert adapter.timeout_seconds == 45


def test_normalize_live_payload_converts_string_evidence_and_exceptions() -> None:
    case_context = _build_case_context()
    raw_payload = {
        "recommended_status": "quoted",
        "confidence": "medium",
        "explanation": "The notes and quote indicate the work is still at quoted stage.",
        "evidence": [
            "NOTE-1001 confirms customer still discussing schedule.",
            "Quote Q-1001 is issued and pending acceptance.",
        ],
        "missing_evidence": ["No signed acceptance artefact located."],
        "exceptions": ["Conflicting narrative requires status_mismatch review."],
    }

    normalized = normalize_live_payload(raw_payload, case_context)

    evidence = normalized["evidence"]
    assert isinstance(evidence, list)
    assert len(evidence) == 2
    assert evidence[0]["source_type"] == "note"
    assert evidence[0]["source_id"] == "NOTE-1001"
    assert evidence[1]["source_type"] == "quote"
    assert evidence[1]["source_id"] == "Q-1001"

    exceptions = normalized["exceptions"]
    assert isinstance(exceptions, list)
    assert len(exceptions) == 1
    assert exceptions[0]["exception_type"] == "status_mismatch"


def test_normalize_live_payload_maps_numeric_confidence() -> None:
    case_context = _build_case_context()
    raw_payload = {
        "recommended_status": "quoted",
        "confidence": 0.66,
        "explanation": "The record is still at quoted stage based on connected context.",
        "evidence": [
            {
                "evidence_type": "supporting",
                "source_type": "note",
                "source_id": "NOTE-1001",
                "explanation": "Recent note references quote-stage progression.",
            }
        ],
        "missing_evidence": [],
        "exceptions": [
            {
                "exception_type": "status_mismatch",
                "description": "Recorded status and recommendation differ.",
            }
        ],
    }

    normalized = normalize_live_payload(raw_payload, case_context)

    assert normalized["confidence"] == "medium"


@pytest.mark.parametrize(
    ("input_status", "expected_status"),
    [
        ("pending_customer_confirmation", "quoted"),
        ("pending", "quoted"),
        ("withdrawn", "cancelled"),
        ("completed_pending_closure", "completed"),
        ("cancellation_requested", "cancelled"),
    ],
)
def test_normalize_live_payload_maps_status_aliases(
    input_status: str,
    expected_status: str,
) -> None:
    case_context = _build_case_context()
    raw_payload = {
        "recommended_status": input_status,
        "confidence": "medium",
        "explanation": "The model output contains a status alias that should be normalized.",
        "evidence": [
            {
                "evidence_type": "supporting",
                "source_type": "note",
                "source_id": "NOTE-1001",
                "explanation": "Note supports current lifecycle interpretation.",
            }
        ],
        "missing_evidence": [],
        "exceptions": [],
    }

    normalized = normalize_live_payload(raw_payload, case_context)

    assert normalized["recommended_status"] == expected_status
