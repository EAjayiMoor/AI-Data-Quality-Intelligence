from __future__ import annotations

from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from ai_data_quality_poc.services.assessment_engine import AssessmentRunResult
from ai_data_quality_poc.services.case_context import CaseContext
from ai_data_quality_poc.services.llm_adapter import LLMUsage
from ai_data_quality_poc.storage.db import build_engine
from ai_data_quality_poc.storage.models import (
    Assessment,
    AssessmentEvidence,
    AssessmentException,
    CostTracking,
    InteractionNote,
    ServiceRequest,
)

PROMPT_VERSION = "phase8_mock_prompt_v1"
RULES_VERSION = "phase5_contract_v1"
CURRENCY = "GBP"
INPUT_PRICE_PER_MILLION = Decimal("0.2500")
OUTPUT_PRICE_PER_MILLION = Decimal("1.0000")


class SavedAssessmentSummary(BaseModel):
    assessment_id: str
    service_request_id: str
    assessment_status: Literal["success", "failed"]
    recommended_status: str
    confidence: str
    model_name: str
    created_at: datetime
    total_cost: Decimal | None


class ExecutiveMetrics(BaseModel):
    total_assessments: int
    total_cases_assessed: int
    total_notes_assessed: int
    successful_assessments: int
    status_alignment_matched_success: int
    status_alignment_total_success: int
    status_alignment_percent_success: Decimal
    failed_assessments: int
    total_exceptions: int
    cases_with_exceptions: int
    top_exception_type: str | None
    total_cost: Decimal
    total_input_tokens: int
    total_output_tokens: int


class AssessmentRerunDecision(BaseModel):
    should_run: bool
    reason: Literal[
        "forced_rerun",
        "no_prior_assessment",
        "data_changed_since_last_assessment",
        "no_data_change_detected",
    ]


class ExceptionCountItem(BaseModel):
    exception_type: str
    count: int


class ExceptionRecordItem(BaseModel):
    assessment_id: str
    service_request_id: str
    customer_name: str
    assessment_created_at: datetime
    assessment_status: Literal["success", "failed"]
    recommended_status: str
    confidence: str
    exception_type: str
    description: str


class AssessmentRunRecordItem(BaseModel):
    assessment_id: str
    service_request_id: str
    assessment_created_at: datetime
    assessment_status: Literal["success", "failed"]
    recorded_status_snapshot: str
    recommended_status: str
    confidence: str
    model_name: str
    evidence_count: int
    exception_count: int
    input_tokens: int
    output_tokens: int
    total_cost: Decimal
    duration_ms: int


def persist_assessment_run(
    service_request_id: str,
    recorded_status_snapshot: str,
    result: AssessmentRunResult,
    engine: Engine | None = None,
) -> str:
    database_engine = engine or build_engine()

    with Session(database_engine) as session:
        assessment_id = _new_id("ASM")
        usage: LLMUsage | None

        if result.kind == "success":
            session.add(
                Assessment(
                    id=assessment_id,
                    service_request_id=service_request_id,
                    recorded_status_snapshot=recorded_status_snapshot,
                    recommended_status=result.contract.recommended_status,
                    confidence=result.contract.confidence,
                    explanation=result.contract.explanation,
                    prompt_version=PROMPT_VERSION,
                    rules_version=RULES_VERSION,
                    model_name=result.usage.model_name,
                    assessment_status="success",
                    created_at=datetime.now(UTC),
                )
            )

            for evidence in result.contract.evidence:
                session.add(
                    AssessmentEvidence(
                        id=_new_id("AEV"),
                        assessment_id=assessment_id,
                        evidence_type=evidence.evidence_type,
                        source_type=evidence.source_type,
                        source_id=evidence.source_id,
                        explanation=evidence.explanation,
                    )
                )

            for exception in result.contract.exceptions:
                session.add(
                    AssessmentException(
                        id=_new_id("AEX"),
                        assessment_id=assessment_id,
                        exception_type=exception.exception_type,
                        description=exception.description,
                    )
                )

            usage = result.usage
        else:
            model_name = result.usage.model_name if result.usage is not None else "unavailable"
            session.add(
                Assessment(
                    id=assessment_id,
                    service_request_id=service_request_id,
                    recorded_status_snapshot=recorded_status_snapshot,
                    recommended_status="insufficient_evidence",
                    confidence="low",
                    explanation=result.message,
                    prompt_version=PROMPT_VERSION,
                    rules_version=RULES_VERSION,
                    model_name=model_name,
                    assessment_status="failed",
                    created_at=datetime.now(UTC),
                )
            )
            session.add(
                AssessmentException(
                    id=_new_id("AEX"),
                    assessment_id=assessment_id,
                    exception_type="assessment_failure",
                    description=f"{result.error_code}: {result.message}",
                )
            )
            usage = result.usage

        if usage is not None:
            session.add(
                CostTracking(
                    id=_new_id("CST"),
                    assessment_id=assessment_id,
                    call_sequence=1,
                    model_name=usage.model_name,
                    input_tokens=usage.input_tokens,
                    output_tokens=usage.output_tokens,
                    cached_input_tokens=usage.cached_input_tokens,
                    input_price_per_million=INPUT_PRICE_PER_MILLION,
                    output_price_per_million=OUTPUT_PRICE_PER_MILLION,
                    calculated_cost=_calculate_cost(
                        input_tokens=usage.input_tokens,
                        output_tokens=usage.output_tokens,
                    ),
                    currency=CURRENCY,
                    duration_ms=usage.duration_ms,
                    call_status=usage.call_status,
                )
            )

        session.commit()

    return assessment_id


def get_latest_assessment_summary(
    service_request_id: str,
    engine: Engine | None = None,
) -> SavedAssessmentSummary | None:
    database_engine = engine or build_engine()

    with Session(database_engine) as session:
        latest_assessment = session.scalars(
            select(Assessment)
            .where(Assessment.service_request_id == service_request_id)
            .order_by(Assessment.created_at.desc(), Assessment.id.desc())
            .limit(1)
        ).first()

        if latest_assessment is None:
            return None

        total_cost = session.scalar(
            select(func.sum(CostTracking.calculated_cost)).where(
                CostTracking.assessment_id == latest_assessment.id
            )
        )

    assessment_status: Literal["success", "failed"]
    if latest_assessment.assessment_status == "success":
        assessment_status = "success"
    else:
        assessment_status = "failed"

    return SavedAssessmentSummary(
        assessment_id=latest_assessment.id,
        service_request_id=latest_assessment.service_request_id,
        assessment_status=assessment_status,
        recommended_status=latest_assessment.recommended_status,
        confidence=latest_assessment.confidence,
        model_name=latest_assessment.model_name,
        created_at=latest_assessment.created_at,
        total_cost=total_cost,
    )


def get_executive_metrics(
    assessment_status_filter: Literal["success", "failed"] | None = None,
    confidence_filter: Literal["high", "medium", "low"] | None = None,
    engine: Engine | None = None,
) -> ExecutiveMetrics:
    database_engine = engine or build_engine()

    with Session(database_engine) as session:
        assessment_rows_stmt = select(
            Assessment.assessment_status,
            Assessment.recorded_status_snapshot,
            Assessment.recommended_status,
        )
        if assessment_status_filter is not None:
            assessment_rows_stmt = assessment_rows_stmt.where(
                Assessment.assessment_status == assessment_status_filter
            )
        if confidence_filter is not None:
            assessment_rows_stmt = assessment_rows_stmt.where(
                Assessment.confidence == confidence_filter
            )

        assessment_rows = session.execute(assessment_rows_stmt).all()
        total_assessments = len(assessment_rows)
        successful_assessments = sum(1 for row in assessment_rows if row[0] == "success")
        failed_assessments = sum(1 for row in assessment_rows if row[0] == "failed")
        status_alignment_matched_success = sum(
            1
            for row in assessment_rows
            if row[0] == "success" and row[1] == row[2]
        )
        status_alignment_total_success = successful_assessments
        if status_alignment_total_success == 0:
            status_alignment_percent_success = Decimal("0.0")
        else:
            status_alignment_percent_success = (
                Decimal(status_alignment_matched_success)
                * Decimal(100)
                / Decimal(status_alignment_total_success)
            ).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)

        total_exceptions_stmt = select(func.count(AssessmentException.id)).join(
            Assessment,
            Assessment.id == AssessmentException.assessment_id,
        )
        if assessment_status_filter is not None:
            total_exceptions_stmt = total_exceptions_stmt.where(
                Assessment.assessment_status == assessment_status_filter
            )
        if confidence_filter is not None:
            total_exceptions_stmt = total_exceptions_stmt.where(
                Assessment.confidence == confidence_filter
            )
        total_exceptions_raw = session.scalar(total_exceptions_stmt)
        total_exceptions = int(total_exceptions_raw or 0)

        total_cases_stmt = select(func.count(func.distinct(Assessment.service_request_id)))
        if assessment_status_filter is not None:
            total_cases_stmt = total_cases_stmt.where(
                Assessment.assessment_status == assessment_status_filter
            )
        if confidence_filter is not None:
            total_cases_stmt = total_cases_stmt.where(Assessment.confidence == confidence_filter)
        total_cases_raw = session.scalar(total_cases_stmt)
        total_cases_assessed = int(total_cases_raw or 0)

        filtered_case_ids_stmt = select(func.distinct(Assessment.service_request_id))
        if assessment_status_filter is not None:
            filtered_case_ids_stmt = filtered_case_ids_stmt.where(
                Assessment.assessment_status == assessment_status_filter
            )
        if confidence_filter is not None:
            filtered_case_ids_stmt = filtered_case_ids_stmt.where(
                Assessment.confidence == confidence_filter
            )

        total_notes_stmt = select(func.count(InteractionNote.id)).where(
            InteractionNote.service_request_id.in_(filtered_case_ids_stmt)
        )
        total_notes_raw = session.scalar(total_notes_stmt)
        total_notes_assessed = int(total_notes_raw or 0)

        cases_with_exceptions_stmt = select(
            func.count(func.distinct(Assessment.service_request_id))
        ).join(
            AssessmentException,
            Assessment.id == AssessmentException.assessment_id,
        )
        if assessment_status_filter is not None:
            cases_with_exceptions_stmt = cases_with_exceptions_stmt.where(
                Assessment.assessment_status == assessment_status_filter
            )
        if confidence_filter is not None:
            cases_with_exceptions_stmt = cases_with_exceptions_stmt.where(
                Assessment.confidence == confidence_filter
            )
        cases_with_exceptions_raw = session.scalar(cases_with_exceptions_stmt)
        cases_with_exceptions = int(cases_with_exceptions_raw or 0)

        top_exception_stmt = (
            select(
                AssessmentException.exception_type,
                func.count(AssessmentException.id).label("exception_count"),
            )
            .join(Assessment, Assessment.id == AssessmentException.assessment_id)
            .group_by(AssessmentException.exception_type)
            .order_by(
                func.count(AssessmentException.id).desc(), AssessmentException.exception_type.asc()
            )
            .limit(1)
        )
        if assessment_status_filter is not None:
            top_exception_stmt = top_exception_stmt.where(
                Assessment.assessment_status == assessment_status_filter
            )
        if confidence_filter is not None:
            top_exception_stmt = top_exception_stmt.where(
                Assessment.confidence == confidence_filter
            )
        top_exception_row = session.execute(top_exception_stmt).first()

        top_exception_type: str | None
        if top_exception_row is None:
            top_exception_type = None
        else:
            top_exception_type = str(top_exception_row[0])

        token_stmt = select(
            func.coalesce(func.sum(CostTracking.input_tokens), 0),
            func.coalesce(func.sum(CostTracking.output_tokens), 0),
            func.sum(CostTracking.calculated_cost),
        ).join(Assessment, Assessment.id == CostTracking.assessment_id)
        if assessment_status_filter is not None:
            token_stmt = token_stmt.where(Assessment.assessment_status == assessment_status_filter)
        if confidence_filter is not None:
            token_stmt = token_stmt.where(Assessment.confidence == confidence_filter)
        token_row = session.execute(token_stmt).one()

    total_input_tokens = int(token_row[0])
    total_output_tokens = int(token_row[1])
    total_cost = Decimal(token_row[2]) if token_row[2] is not None else Decimal("0")

    return ExecutiveMetrics(
        total_assessments=total_assessments,
        total_cases_assessed=total_cases_assessed,
        total_notes_assessed=total_notes_assessed,
        successful_assessments=successful_assessments,
        status_alignment_matched_success=status_alignment_matched_success,
        status_alignment_total_success=status_alignment_total_success,
        status_alignment_percent_success=status_alignment_percent_success,
        failed_assessments=failed_assessments,
        total_exceptions=total_exceptions,
        cases_with_exceptions=cases_with_exceptions,
        top_exception_type=top_exception_type,
        total_cost=total_cost,
        total_input_tokens=total_input_tokens,
        total_output_tokens=total_output_tokens,
    )


def list_exception_counts(
    assessment_status_filter: Literal["success", "failed"] | None = None,
    confidence_filter: Literal["high", "medium", "low"] | None = None,
    engine: Engine | None = None,
) -> list[ExceptionCountItem]:
    database_engine = engine or build_engine()

    with Session(database_engine) as session:
        stmt = select(
            AssessmentException.exception_type,
            func.count(AssessmentException.id),
        ).join(Assessment, Assessment.id == AssessmentException.assessment_id)

        if assessment_status_filter is not None:
            stmt = stmt.where(Assessment.assessment_status == assessment_status_filter)

        if confidence_filter is not None:
            stmt = stmt.where(Assessment.confidence == confidence_filter)

        rows = session.execute(stmt.group_by(AssessmentException.exception_type)).all()

    return [
        ExceptionCountItem(exception_type=exception_type, count=count)
        for exception_type, count in rows
    ]


def list_exception_records(
    exception_type_filter: str | None = None,
    assessment_status_filter: Literal["success", "failed"] | None = None,
    confidence_filter: Literal["high", "medium", "low"] | None = None,
    limit: int = 200,
    engine: Engine | None = None,
) -> list[ExceptionRecordItem]:
    database_engine = engine or build_engine()

    with Session(database_engine) as session:
        stmt = (
            select(
                Assessment.id,
                Assessment.service_request_id,
                ServiceRequest.customer_name,
                Assessment.created_at,
                Assessment.assessment_status,
                Assessment.recommended_status,
                Assessment.confidence,
                AssessmentException.exception_type,
                AssessmentException.description,
            )
            .join(AssessmentException, AssessmentException.assessment_id == Assessment.id)
            .join(ServiceRequest, ServiceRequest.id == Assessment.service_request_id)
        )

        if exception_type_filter is not None:
            stmt = stmt.where(AssessmentException.exception_type == exception_type_filter)

        if assessment_status_filter is not None:
            stmt = stmt.where(Assessment.assessment_status == assessment_status_filter)

        if confidence_filter is not None:
            stmt = stmt.where(Assessment.confidence == confidence_filter)

        rows = session.execute(
            stmt.order_by(Assessment.created_at.desc(), Assessment.id.desc()).limit(limit)
        ).all()

    return [
        ExceptionRecordItem(
            assessment_id=row[0],
            service_request_id=row[1],
            customer_name=row[2],
            assessment_created_at=row[3],
            assessment_status="success" if row[4] == "success" else "failed",
            recommended_status=row[5],
            confidence=row[6],
            exception_type=row[7],
            description=row[8],
        )
        for row in rows
    ]


def list_assessment_run_records(
    service_request_id: str,
    limit: int = 30,
    engine: Engine | None = None,
) -> list[AssessmentRunRecordItem]:
    database_engine = engine or build_engine()

    cost_subquery = (
        select(
            CostTracking.assessment_id.label("assessment_id"),
            func.coalesce(func.sum(CostTracking.input_tokens), 0).label("input_tokens"),
            func.coalesce(func.sum(CostTracking.output_tokens), 0).label("output_tokens"),
            func.coalesce(func.sum(CostTracking.calculated_cost), 0).label("total_cost"),
            func.coalesce(func.sum(CostTracking.duration_ms), 0).label("duration_ms"),
        )
        .group_by(CostTracking.assessment_id)
        .subquery()
    )

    evidence_subquery = (
        select(
            AssessmentEvidence.assessment_id.label("assessment_id"),
            func.count(AssessmentEvidence.id).label("evidence_count"),
        )
        .group_by(AssessmentEvidence.assessment_id)
        .subquery()
    )

    exception_subquery = (
        select(
            AssessmentException.assessment_id.label("assessment_id"),
            func.count(AssessmentException.id).label("exception_count"),
        )
        .group_by(AssessmentException.assessment_id)
        .subquery()
    )

    with Session(database_engine) as session:
        stmt = (
            select(
                Assessment.id,
                Assessment.service_request_id,
                Assessment.created_at,
                Assessment.assessment_status,
                Assessment.recorded_status_snapshot,
                Assessment.recommended_status,
                Assessment.confidence,
                Assessment.model_name,
                func.coalesce(evidence_subquery.c.evidence_count, 0),
                func.coalesce(exception_subquery.c.exception_count, 0),
                func.coalesce(cost_subquery.c.input_tokens, 0),
                func.coalesce(cost_subquery.c.output_tokens, 0),
                func.coalesce(cost_subquery.c.total_cost, 0),
                func.coalesce(cost_subquery.c.duration_ms, 0),
            )
            .outerjoin(
                evidence_subquery,
                evidence_subquery.c.assessment_id == Assessment.id,
            )
            .outerjoin(
                exception_subquery,
                exception_subquery.c.assessment_id == Assessment.id,
            )
            .outerjoin(
                cost_subquery,
                cost_subquery.c.assessment_id == Assessment.id,
            )
            .where(Assessment.service_request_id == service_request_id)
            .order_by(Assessment.created_at.desc(), Assessment.id.desc())
            .limit(limit)
        )
        rows = session.execute(stmt).all()

    return [
        AssessmentRunRecordItem(
            assessment_id=row[0],
            service_request_id=row[1],
            assessment_created_at=row[2],
            assessment_status="success" if row[3] == "success" else "failed",
            recorded_status_snapshot=row[4],
            recommended_status=row[5],
            confidence=row[6],
            model_name=row[7],
            evidence_count=int(row[8]),
            exception_count=int(row[9]),
            input_tokens=int(row[10]),
            output_tokens=int(row[11]),
            total_cost=Decimal(row[12]),
            duration_ms=int(row[13]),
        )
        for row in rows
    ]


def list_assessment_run_counts(engine: Engine | None = None) -> dict[str, int]:
    database_engine = engine or build_engine()

    with Session(database_engine) as session:
        rows = session.execute(
            select(
                Assessment.service_request_id,
                func.count(Assessment.id),
            ).group_by(Assessment.service_request_id)
        ).all()

    return {service_request_id: int(count) for service_request_id, count in rows}


def should_run_assessment(
    service_request_id: str,
    case_context: CaseContext,
    force_rerun: bool = False,
    engine: Engine | None = None,
) -> AssessmentRerunDecision:
    if force_rerun:
        return AssessmentRerunDecision(should_run=True, reason="forced_rerun")

    latest_saved = get_latest_assessment_summary(
        service_request_id=service_request_id, engine=engine
    )
    if latest_saved is None:
        return AssessmentRerunDecision(should_run=True, reason="no_prior_assessment")

    latest_data_timestamp = _latest_data_timestamp(case_context)
    latest_assessment_timestamp = _as_utc(latest_saved.created_at)

    if latest_data_timestamp > latest_assessment_timestamp:
        return AssessmentRerunDecision(
            should_run=True,
            reason="data_changed_since_last_assessment",
        )

    return AssessmentRerunDecision(should_run=False, reason="no_data_change_detected")


def _latest_data_timestamp(case_context: CaseContext) -> datetime:
    candidate_timestamps = [
        _as_utc(case_context.service_request.updated_at),
        *(_as_utc(note.note_timestamp) for note in case_context.interaction_notes),
        *(_as_utc(quote.quote_timestamp) for quote in case_context.quotes),
        *(_as_utc(payment.payment_timestamp) for payment in case_context.payments),
    ]
    return max(candidate_timestamps)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _calculate_cost(input_tokens: int, output_tokens: int) -> Decimal:
    input_cost = (Decimal(input_tokens) / Decimal(1_000_000)) * INPUT_PRICE_PER_MILLION
    output_cost = (Decimal(output_tokens) / Decimal(1_000_000)) * OUTPUT_PRICE_PER_MILLION
    return (input_cost + output_cost).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:12].upper()}"

