from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from ai_data_quality_poc.services.assessment_contract import (
    AssessmentContract,
    AssessmentContractValidationError,
    validate_assessment_contract,
)
from ai_data_quality_poc.services.case_context import CaseContext
from ai_data_quality_poc.services.llm_adapter import AssessmentLLMAdapter, LLMUsage


class AssessmentRunSuccess(BaseModel):
    kind: Literal["success"]
    contract: AssessmentContract
    usage: LLMUsage


class AssessmentRunFailure(BaseModel):
    kind: Literal["failure"]
    error_code: Literal["adapter_failed", "contract_validation_failed"]
    message: str
    usage: LLMUsage | None = None


AssessmentRunResult = AssessmentRunSuccess | AssessmentRunFailure


def run_assessment(case_context: CaseContext, adapter: AssessmentLLMAdapter) -> AssessmentRunResult:
    try:
        adapter_response = adapter.assess(case_context)
    except Exception as exc:
        return AssessmentRunFailure(
            kind="failure",
            error_code="adapter_failed",
            message=f"Adapter execution failed: {exc}",
        )

    try:
        contract = validate_assessment_contract(adapter_response.payload, case_context)
    except AssessmentContractValidationError as exc:
        return AssessmentRunFailure(
            kind="failure",
            error_code="contract_validation_failed",
            message=str(exc),
            usage=adapter_response.usage,
        )

    return AssessmentRunSuccess(kind="success", contract=contract, usage=adapter_response.usage)
