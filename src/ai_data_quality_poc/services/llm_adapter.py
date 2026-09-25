from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from collections.abc import Mapping
from typing import Literal, Protocol, cast

from pydantic import BaseModel, Field

from ai_data_quality_poc.services.case_context import CaseContext


class LLMUsage(BaseModel):
    model_name: str
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    cached_input_tokens: int | None = Field(default=None, ge=0)
    duration_ms: int = Field(ge=0)
    call_status: Literal["success", "failed"]


class AdapterResponse(BaseModel):
    payload: dict[str, object]
    usage: LLMUsage


class AssessmentLLMAdapter(Protocol):
    def assess(self, case_context: CaseContext) -> AdapterResponse: ...


MockAdapterMode = Literal["valid", "invalid_status", "unknown_evidence", "insufficient"]

AZURE_MODEL = "gpt-5.3-codex-Emmanuel-Ajayi"
AZURE_MODEL_PROVIDER = "azure"
AZURE_MODEL_REASONING_EFFORT = "medium"

ALLOWED_STATUSES = {
    "new",
    "quoted",
    "accepted_unpaid",
    "accepted_paid",
    "in_delivery",
    "completed",
    "cancelled",
    "insufficient_evidence",
}
ALLOWED_CONFIDENCE = {"high", "medium", "low"}
ALLOWED_EXCEPTION_TYPES = {
    "status_mismatch",
    "missing_payment_evidence",
    "contradictory_evidence",
    "low_confidence",
    "insufficient_evidence",
    "context_truncated",
    "assessment_failure",
}

STATUS_ALIASES: dict[str, str] = {
    "pending_customer_confirmation": "quoted",
    "pending": "quoted",
    "withdrawn": "cancelled",
    "completed_pending_closure": "completed",
    "cancellation_requested": "cancelled",
}


def is_live_llm_configured() -> bool:
    api_key = os.getenv("AZURE_OPENAI_API_KEY", "").strip()
    base_url = os.getenv("AZURE_OPENAI_BASE_URL", "").strip()
    return bool(api_key and base_url)


class MockAssessmentLLMAdapter:
    def __init__(self, mode: MockAdapterMode = "valid") -> None:
        self.mode = mode

    def assess(self, case_context: CaseContext) -> AdapterResponse:
        usage = LLMUsage(
            model_name="mock-llm-v1",
            input_tokens=860,
            output_tokens=230,
            cached_input_tokens=0,
            duration_ms=120,
            call_status="success",
        )

        if self.mode == "invalid_status":
            invalid_payload: dict[str, object] = {}
            invalid_payload["recommended_status"] = "done"
            invalid_payload["confidence"] = "medium"
            invalid_payload["explanation"] = "Invalid status output for contract-failure testing."
            invalid_payload["evidence"] = []
            invalid_payload["missing_evidence"] = []
            invalid_payload["exceptions"] = []
            return AdapterResponse(payload=invalid_payload, usage=usage)

        if self.mode == "unknown_evidence":
            unknown_payload: dict[str, object] = {
                "recommended_status": "accepted_paid",
                "confidence": "high",
                "explanation": "Unknown evidence reference for validation-path testing.",
                "evidence": [
                    {
                        "evidence_type": "supporting",
                        "source_type": "note",
                        "source_id": "NOTE-UNKNOWN",
                        "explanation": "This should fail ID validation.",
                    }
                ],
                "missing_evidence": [],
                "exceptions": [
                    {
                        "exception_type": "status_mismatch",
                        "description": "Recorded status differs from recommendation.",
                    }
                ],
            }
            return AdapterResponse(payload=unknown_payload, usage=usage)

        if self.mode == "insufficient":
            insufficient_payload: dict[str, object] = {
                "recommended_status": "insufficient_evidence",
                "confidence": "low",
                "explanation": (
                    "Sparse and conflicting evidence prevents reliable lifecycle recommendation."
                ),
                "evidence": [],
                "missing_evidence": ["No reliable completion marker found."],
                "exceptions": [
                    {
                        "exception_type": "low_confidence",
                        "description": "Evidence quality is low across timeline and records.",
                    },
                    {
                        "exception_type": "status_mismatch",
                        "description": "Recorded status cannot be validated with confidence.",
                    },
                ],
            }
            return AdapterResponse(payload=insufficient_payload, usage=usage)

        evidence_source_type = "payment" if case_context.payments else "note"
        evidence_source_id = (
            case_context.payments[0].id
            if case_context.payments
            else case_context.interaction_notes[0].id
        )

        valid_payload: dict[str, object] = {
            "recommended_status": "accepted_paid" if case_context.payments else "quoted",
            "confidence": "medium",
            "explanation": (
                "Structured evidence supports the recommended status with moderate confidence."
            ),
            "evidence": [
                {
                    "evidence_type": "supporting",
                    "source_type": evidence_source_type,
                    "source_id": evidence_source_id,
                    "explanation": "Primary supporting signal from connected records.",
                }
            ],
            "missing_evidence": [],
            "exceptions": [
                {
                    "exception_type": "status_mismatch",
                    "description": "Recorded status differs from recommended status.",
                }
            ],
        }
        return AdapterResponse(payload=valid_payload, usage=usage)


class LiveAssessmentLLMAdapter:
    def __init__(
        self,
        api_key: str,
        model: str,
        endpoint_url: str,
        timeout_seconds: int,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.endpoint_url = endpoint_url
        self.timeout_seconds = timeout_seconds

    @classmethod
    def from_env(cls) -> LiveAssessmentLLMAdapter:
        api_key = os.getenv("AZURE_OPENAI_API_KEY", "").strip()
        if not api_key:
            raise ValueError("AZURE_OPENAI_API_KEY is required for live LLM mode.")

        base_url = os.getenv("AZURE_OPENAI_BASE_URL", "").strip()
        if not base_url:
            raise ValueError("AZURE_OPENAI_BASE_URL is required for live LLM mode.")

        model = AZURE_MODEL
        endpoint_url = base_url.rstrip("/")
        if not endpoint_url.endswith("/responses"):
            endpoint_url = f"{endpoint_url}/responses"

        timeout_raw = os.getenv("LLM_TIMEOUT_SECONDS", "30").strip()
        try:
            timeout_seconds = max(5, int(timeout_raw))
        except ValueError as exc:
            raise ValueError("LLM_TIMEOUT_SECONDS must be an integer value.") from exc

        return cls(
            api_key=api_key,
            model=model,
            endpoint_url=endpoint_url,
            timeout_seconds=timeout_seconds,
        )

    def assess(self, case_context: CaseContext) -> AdapterResponse:
        request_payload = self._build_request_payload(case_context)

        request_body = json.dumps(request_payload).encode("utf-8")
        request = urllib.request.Request(
            self.endpoint_url,
            data=request_body,
            method="POST",
            headers={
                "api-key": self.api_key,
                "Content-Type": "application/json",
            },
        )

        started_at = time.perf_counter()
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as http_response:
                raw_response_body = http_response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            response_body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"Live adapter request failed with HTTP {exc.code}: {response_body}"
            ) from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Live adapter request failed: {exc}") from exc

        duration_ms = int((time.perf_counter() - started_at) * 1000)
        response_object = json.loads(raw_response_body)
        if not isinstance(response_object, dict):
            raise RuntimeError("Live adapter returned a non-object response payload.")

        output_text = self._extract_output_text(response_object)
        parsed_payload = json.loads(output_text)
        if not isinstance(parsed_payload, dict):
            raise RuntimeError("Live adapter output JSON must be an object.")

        normalized_payload = normalize_live_payload(
            cast(dict[str, object], parsed_payload),
            case_context,
        )

        usage = self._extract_usage(response_object, duration_ms)
        return AdapterResponse(payload=normalized_payload, usage=usage)

    def _build_request_payload(self, case_context: CaseContext) -> dict[str, object]:
        system_prompt = (
            "You are an assessment engine for service lifecycle status. "
            "Return only a JSON object with keys: recommended_status, confidence, explanation, "
            "evidence, missing_evidence, exceptions. "
            "evidence MUST be a list of objects with keys: "
            "evidence_type, source_type, source_id, explanation. "
            "exceptions MUST be a list of objects with keys: exception_type, description. "
            "Do not return strings inside evidence/exceptions."
        )

        case_context_payload = case_context.model_dump(mode="json")
        user_prompt = (
            "Assess the following case context and return the required JSON object only:\n"
            f"{json.dumps(case_context_payload, ensure_ascii=False)}"
        )

        payload: dict[str, object] = {
            "model": self.model,
            "input": [
                {
                    "role": "system",
                    "content": [{"type": "input_text", "text": system_prompt}],
                },
                {
                    "role": "user",
                    "content": [{"type": "input_text", "text": user_prompt}],
                },
            ],
        }
        payload["reasoning"] = {"effort": AZURE_MODEL_REASONING_EFFORT}
        return payload

    def _extract_usage(self, response_object: dict[str, object], duration_ms: int) -> LLMUsage:
        usage_object = response_object.get("usage")
        usage_map: Mapping[str, object]
        if isinstance(usage_object, dict):
            usage_map = usage_object
        else:
            usage_map = {}

        return LLMUsage(
            model_name=str(response_object.get("model") or self.model),
            input_tokens=self._coerce_int(usage_map.get("input_tokens")),
            output_tokens=self._coerce_int(usage_map.get("output_tokens")),
            cached_input_tokens=self._coerce_optional_int(usage_map.get("cached_input_tokens")),
            duration_ms=max(duration_ms, 0),
            call_status="success",
        )

    def _extract_output_text(self, response_object: dict[str, object]) -> str:
        direct_output_text = response_object.get("output_text")
        if isinstance(direct_output_text, str) and direct_output_text.strip():
            return direct_output_text

        output_value = response_object.get("output")
        if not isinstance(output_value, list):
            raise RuntimeError("Live adapter response missing output text.")

        output_fragments: list[str] = []
        for item in output_value:
            if not isinstance(item, dict):
                continue
            content_value = item.get("content")
            if not isinstance(content_value, list):
                continue
            for content_item in content_value:
                if not isinstance(content_item, dict):
                    continue
                text_value = content_item.get("text")
                if isinstance(text_value, str) and text_value.strip():
                    output_fragments.append(text_value)

        if not output_fragments:
            raise RuntimeError("Live adapter response did not contain parseable output text.")

        return "\n".join(output_fragments)

    def _coerce_int(self, value: object) -> int:
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        if isinstance(value, str) and value.strip():
            try:
                return int(value)
            except ValueError:
                return 0
        return 0

    def _coerce_optional_int(self, value: object) -> int | None:
        if value is None:
            return None
        return self._coerce_int(value)


def normalize_live_payload(
    raw_payload: dict[str, object],
    case_context: CaseContext,
) -> dict[str, object]:
    normalized: dict[str, object] = dict(raw_payload)

    recommended_status = _normalize_recommended_status(raw_payload.get("recommended_status"))
    if recommended_status is not None:
        normalized["recommended_status"] = recommended_status

    confidence_normalized = _normalize_confidence_value(raw_payload.get("confidence"))
    if confidence_normalized is not None:
        normalized["confidence"] = confidence_normalized

    explanation_raw = raw_payload.get("explanation")
    if not isinstance(explanation_raw, str) or len(explanation_raw.strip()) < 10:
        normalized["explanation"] = "Live model response did not include a usable explanation."
    else:
        normalized["explanation"] = explanation_raw.strip()

    missing_evidence_raw = raw_payload.get("missing_evidence")
    normalized_missing_evidence: list[str] = []
    if isinstance(missing_evidence_raw, list):
        for item in missing_evidence_raw:
            if isinstance(item, str) and item.strip():
                normalized_missing_evidence.append(item.strip())
    normalized["missing_evidence"] = normalized_missing_evidence

    normalized["evidence"] = _normalize_evidence(raw_payload.get("evidence"), case_context)
    normalized["exceptions"] = _normalize_exceptions(raw_payload.get("exceptions"))

    return normalized


def _normalize_evidence(raw_evidence: object, case_context: CaseContext) -> list[dict[str, object]]:
    if not isinstance(raw_evidence, list):
        return []

    note_ids = [note.id for note in case_context.interaction_notes]
    quote_ids = [quote.id for quote in case_context.quotes]
    payment_ids = [payment.id for payment in case_context.payments]

    normalized_items: list[dict[str, object]] = []
    for item in raw_evidence:
        if isinstance(item, dict):
            normalized = _normalize_evidence_dict(item, note_ids, quote_ids, payment_ids)
            if normalized is not None:
                normalized_items.append(normalized)
            continue

        if isinstance(item, str) and item.strip():
            inferred = _normalize_evidence_text(item.strip(), note_ids, quote_ids, payment_ids)
            if inferred is not None:
                normalized_items.append(inferred)

    return normalized_items


def _normalize_evidence_dict(
    item: Mapping[str, object],
    note_ids: list[str],
    quote_ids: list[str],
    payment_ids: list[str],
) -> dict[str, object] | None:
    evidence_type_raw = str(item.get("evidence_type", "supporting")).strip().lower()
    evidence_type = "contradictory" if evidence_type_raw == "contradictory" else "supporting"

    source_type_raw = str(item.get("source_type", "")).strip().lower()
    source_id_raw = str(item.get("source_id", "")).strip()

    if source_type_raw == "note" and source_id_raw in note_ids:
        source_type = "note"
        source_id = source_id_raw
    elif source_type_raw == "quote" and source_id_raw in quote_ids:
        source_type = "quote"
        source_id = source_id_raw
    elif source_type_raw == "payment" and source_id_raw in payment_ids:
        source_type = "payment"
        source_id = source_id_raw
    else:
        inferred = _infer_source_from_text(
            f"{source_type_raw} {source_id_raw}", note_ids, quote_ids, payment_ids
        )
        if inferred is None:
            return None
        source_type, source_id = inferred

    explanation_raw = str(item.get("explanation", "")).strip()
    if not explanation_raw:
        explanation_raw = f"Inferred evidence from {source_type}:{source_id}."

    return {
        "evidence_type": evidence_type,
        "source_type": source_type,
        "source_id": source_id,
        "explanation": explanation_raw[:500],
    }


def _normalize_evidence_text(
    item: str,
    note_ids: list[str],
    quote_ids: list[str],
    payment_ids: list[str],
) -> dict[str, object] | None:
    inferred = _infer_source_from_text(item, note_ids, quote_ids, payment_ids)
    if inferred is None:
        return None

    source_type, source_id = inferred
    item_lower = item.lower()
    evidence_type = "contradictory" if "contradict" in item_lower else "supporting"

    return {
        "evidence_type": evidence_type,
        "source_type": source_type,
        "source_id": source_id,
        "explanation": item[:500],
    }


def _infer_source_from_text(
    text: str,
    note_ids: list[str],
    quote_ids: list[str],
    payment_ids: list[str],
) -> tuple[str, str] | None:
    text_upper = text.upper()

    for note_id in note_ids:
        if note_id.upper() in text_upper:
            return "note", note_id

    for quote_id in quote_ids:
        if quote_id.upper() in text_upper:
            return "quote", quote_id

    for payment_id in payment_ids:
        if payment_id.upper() in text_upper:
            return "payment", payment_id

    found_note = re.search(r"NOTE-[A-Z0-9-]+", text_upper)
    if found_note and note_ids:
        return "note", note_ids[0]

    found_quote = re.search(r"Q-[A-Z0-9-]+", text_upper)
    if found_quote and quote_ids:
        return "quote", quote_ids[0]

    found_payment = re.search(r"PAY-[A-Z0-9-]+", text_upper)
    if found_payment and payment_ids:
        return "payment", payment_ids[0]

    if "payment" in text.lower() and payment_ids:
        return "payment", payment_ids[0]
    if "quote" in text.lower() and quote_ids:
        return "quote", quote_ids[0]
    if note_ids:
        return "note", note_ids[0]

    return None


def _normalize_exceptions(raw_exceptions: object) -> list[dict[str, object]]:
    if not isinstance(raw_exceptions, list):
        return []

    normalized_items: list[dict[str, object]] = []
    for item in raw_exceptions:
        if isinstance(item, dict):
            exception_type_raw = str(item.get("exception_type", "")).strip().lower()
            if exception_type_raw not in ALLOWED_EXCEPTION_TYPES:
                exception_type_raw = _infer_exception_type(str(item.get("description", "")))
            description_raw = str(item.get("description", "")).strip()
            if not description_raw:
                description_raw = "Live model returned an exception without description."
            normalized_items.append(
                {
                    "exception_type": exception_type_raw,
                    "description": description_raw[:500],
                }
            )
            continue

        if isinstance(item, str) and item.strip():
            normalized_items.append(
                {
                    "exception_type": _infer_exception_type(item),
                    "description": item[:500],
                }
            )

    return normalized_items



def _normalize_confidence_value(value: object) -> str | None:
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in ALLOWED_CONFIDENCE:
            return lowered
        try:
            numeric = float(lowered)
        except ValueError:
            return None
        return _map_confidence_numeric(numeric)

    if isinstance(value, int | float):
        return _map_confidence_numeric(float(value))

    return None


def _normalize_recommended_status(value: object) -> str | None:
    if not isinstance(value, str):
        return None

    normalized = value.strip().lower().replace(" ", "_").replace("-", "_")
    canonical = STATUS_ALIASES.get(normalized, normalized)

    if canonical in ALLOWED_STATUSES:
        return canonical
    return None


def _map_confidence_numeric(numeric: float) -> str:
    if numeric >= 0.8:
        return "high"
    if numeric >= 0.5:
        return "medium"
    return "low"


def _infer_exception_type(text: str) -> str:
    lowered = text.lower()
    if "low confidence" in lowered or "uncertain" in lowered:
        return "low_confidence"
    if "missing payment" in lowered:
        return "missing_payment_evidence"
    if "contradict" in lowered:
        return "contradictory_evidence"
    if "truncated" in lowered:
        return "context_truncated"
    if "insufficient" in lowered:
        return "insufficient_evidence"
    if "failure" in lowered or "error" in lowered:
        return "assessment_failure"
    return "status_mismatch"


