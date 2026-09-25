from __future__ import annotations

import json
from decimal import Decimal

from ai_data_quality_poc.services.assessment_engine import run_assessment
from ai_data_quality_poc.services.assessment_persistence import persist_assessment_run
from ai_data_quality_poc.services.case_context import get_case_context, list_service_requests
from ai_data_quality_poc.services.llm_adapter import LiveAssessmentLLMAdapter

adapter = LiveAssessmentLLMAdapter.from_env()
service_requests = list_service_requests()

stats = {
    "total_cases": len(service_requests),
    "attempted": 0,
    "saved": 0,
    "success": 0,
    "failure": 0,
    "save_errors": 0,
    "input_tokens": 0,
    "output_tokens": 0,
}

records: list[dict[str, object]] = []

print(f"START total_cases={len(service_requests)}", flush=True)

for index, service_request in enumerate(service_requests, start=1):
    service_request_id = service_request.id
    stats["attempted"] += 1
    print(f"RUN {index}/{len(service_requests)} case={service_request_id}", flush=True)

    try:
        case_context = get_case_context(service_request_id)
        result = run_assessment(case_context, adapter)

        assessment_id = persist_assessment_run(
            service_request_id=service_request_id,
            recorded_status_snapshot=case_context.service_request.recorded_status,
            result=result,
        )

        stats["saved"] += 1

        if result.kind == "success":
            stats["success"] += 1
            recommended_status = result.contract.recommended_status
            confidence = result.contract.confidence
            usage = result.usage
            error_code = ""
            message = ""
        else:
            stats["failure"] += 1
            recommended_status = "insufficient_evidence"
            confidence = "low"
            usage = result.usage
            error_code = result.error_code
            message = result.message

        if usage is not None:
            stats["input_tokens"] += usage.input_tokens
            stats["output_tokens"] += usage.output_tokens
            model_name = usage.model_name
        else:
            model_name = "unavailable"

        records.append(
            {
                "service_request_id": service_request_id,
                "assessment_id": assessment_id,
                "result_kind": result.kind,
                "recommended_status": recommended_status,
                "confidence": confidence,
                "model_name": model_name,
                "error_code": error_code,
                "message": message,
            }
        )
        print(
            f"SAVED case={service_request_id} kind={result.kind} assessment_id={assessment_id}",
            flush=True,
        )
    except Exception as exc:  # noqa: BLE001
        stats["save_errors"] += 1
        records.append(
            {
                "service_request_id": service_request_id,
                "assessment_id": "",
                "result_kind": "batch_error",
                "recommended_status": "",
                "confidence": "",
                "model_name": "",
                "error_code": "batch_error",
                "message": str(exc),
            }
        )
        print(f"ERROR case={service_request_id} message={exc}", flush=True)

estimated_cost = (
    (Decimal(stats["input_tokens"]) / Decimal(1_000_000)) * Decimal("0.2500")
    + (Decimal(stats["output_tokens"]) / Decimal(1_000_000)) * Decimal("1.0000")
)

summary = {
    **stats,
    "estimated_cost_gbp": f"{estimated_cost:.6f}",
}

with open("batch_live_run_summary.json", "w", encoding="utf-8") as summary_file:
    json.dump(summary, summary_file, indent=2)

with open("batch_live_run_records.json", "w", encoding="utf-8") as records_file:
    json.dump(records, records_file, indent=2)

print("BATCH_RUN_COMPLETE", flush=True)
print(json.dumps(summary), flush=True)
