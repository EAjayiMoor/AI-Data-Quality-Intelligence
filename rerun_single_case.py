from ai_data_quality_poc.services.assessment_engine import run_assessment
from ai_data_quality_poc.services.assessment_persistence import persist_assessment_run
from ai_data_quality_poc.services.case_context import get_case_context
from ai_data_quality_poc.services.llm_adapter import LiveAssessmentLLMAdapter

case_id = "SR-0057"
adapter = LiveAssessmentLLMAdapter.from_env()
ctx = get_case_context(case_id)
result = run_assessment(ctx, adapter)
assessment_id = persist_assessment_run(
    service_request_id=case_id,
    recorded_status_snapshot=ctx.service_request.recorded_status,
    result=result,
)
print(f"case={case_id}")
print(f"assessment_id={assessment_id}")
print(f"result_kind={result.kind}")
if result.kind == "success":
    print(f"recommended_status={result.contract.recommended_status}")
    print(f"confidence={result.contract.confidence}")
else:
    print(f"error_code={result.error_code}")
    print(f"message={result.message}")
