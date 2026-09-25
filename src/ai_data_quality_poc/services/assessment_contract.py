from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, ValidationError

from ai_data_quality_poc.services.case_context import CaseContext

LifecycleStatus = Literal[
    "new",
    "quoted",
    "accepted_unpaid",
    "accepted_paid",
    "in_delivery",
    "completed",
    "cancelled",
    "insufficient_evidence",
]

ConfidenceValue = Literal["high", "medium", "low"]
EvidenceType = Literal["supporting", "contradictory"]
EvidenceSourceType = Literal["note", "quote", "payment"]
ExceptionType = Literal[
    "status_mismatch",
    "missing_payment_evidence",
    "contradictory_evidence",
    "low_confidence",
    "insufficient_evidence",
    "context_truncated",
    "assessment_failure",
]


class AssessmentContractValidationError(ValueError):
    pass


class EvidenceReference(BaseModel):
    evidence_type: EvidenceType
    source_type: EvidenceSourceType
    source_id: str = Field(min_length=1)
    explanation: str = Field(min_length=5, max_length=500)


class AssessmentExceptionItem(BaseModel):
    exception_type: ExceptionType
    description: str = Field(min_length=3, max_length=500)


class AssessmentContract(BaseModel):
    recommended_status: LifecycleStatus
    confidence: ConfidenceValue
    explanation: str = Field(min_length=10, max_length=1000)
    evidence: list[EvidenceReference] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
    exceptions: list[AssessmentExceptionItem] = Field(default_factory=list)


def validate_assessment_contract(
    raw: dict[str, object], case_context: CaseContext
) -> AssessmentContract:
    try:
        contract = AssessmentContract.model_validate(raw)
    except ValidationError as exc:
        raise AssessmentContractValidationError(str(exc)) from exc

    _validate_evidence_source_ids(contract, case_context)
    _validate_insufficient_evidence_rule(contract)
    _validate_low_confidence_rule(contract)
    _validate_status_mismatch_rule(contract, case_context.service_request.recorded_status)
    return contract


def status_label(status: LifecycleStatus) -> str:
    label_map = {
        "new": "New",
        "quoted": "Quoted",
        "accepted_unpaid": "Accepted unpaid",
        "accepted_paid": "Accepted paid",
        "in_delivery": "In delivery",
        "completed": "Completed",
        "cancelled": "Cancelled",
        "insufficient_evidence": "Insufficient evidence",
    }
    return label_map[status]


def confidence_label(confidence: ConfidenceValue) -> str:
    label_map = {"high": "High", "medium": "Medium", "low": "Low"}
    return label_map[confidence]


def _validate_evidence_source_ids(contract: AssessmentContract, case_context: CaseContext) -> None:
    valid_note_ids = {note.id for note in case_context.interaction_notes}
    valid_quote_ids = {quote.id for quote in case_context.quotes}
    valid_payment_ids = {payment.id for payment in case_context.payments}

    for evidence in contract.evidence:
        if evidence.source_type == "note" and evidence.source_id not in valid_note_ids:
            raise AssessmentContractValidationError(
                f"Unknown note source_id in evidence: {evidence.source_id}"
            )
        if evidence.source_type == "quote" and evidence.source_id not in valid_quote_ids:
            raise AssessmentContractValidationError(
                f"Unknown quote source_id in evidence: {evidence.source_id}"
            )
        if evidence.source_type == "payment" and evidence.source_id not in valid_payment_ids:
            raise AssessmentContractValidationError(
                f"Unknown payment source_id in evidence: {evidence.source_id}"
            )


def _validate_insufficient_evidence_rule(contract: AssessmentContract) -> None:
    if contract.recommended_status == "insufficient_evidence":
        return

    if len(contract.evidence) == 0:
        raise AssessmentContractValidationError(
            "At least one evidence item is required unless recommended_status "
            "is insufficient_evidence."
        )


def _validate_low_confidence_rule(contract: AssessmentContract) -> None:
    if contract.confidence != "low":
        return

    has_low_confidence_exception = any(
        item.exception_type == "low_confidence" for item in contract.exceptions
    )
    if not has_low_confidence_exception:
        raise AssessmentContractValidationError(
            "Low confidence assessments must include a low_confidence exception item."
        )


def _validate_status_mismatch_rule(contract: AssessmentContract, recorded_status: str) -> None:
    if contract.recommended_status == recorded_status:
        return

    has_status_mismatch = any(
        item.exception_type == "status_mismatch" for item in contract.exceptions
    )
    if not has_status_mismatch:
        raise AssessmentContractValidationError(
            "Status mismatch requires a status_mismatch exception item."
        )
