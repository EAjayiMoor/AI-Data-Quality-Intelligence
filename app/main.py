from __future__ import annotations

from decimal import Decimal
from html import escape
from pathlib import Path
from typing import Literal

import streamlit as st

from ai_data_quality_poc.services.assessment_contract import confidence_label, status_label
from ai_data_quality_poc.services.assessment_engine import AssessmentRunResult, run_assessment
from ai_data_quality_poc.services.assessment_persistence import (
    get_executive_metrics,
    get_latest_assessment_summary,
    list_assessment_run_counts,
    list_assessment_run_records,
    list_exception_counts,
    list_exception_records,
    persist_assessment_run,
    should_run_assessment,
)
from ai_data_quality_poc.services.case_context import (
    CaseContextNotFoundError,
    ServiceRequestSummary,
    get_case_context,
    list_interaction_note_counts,
    list_service_requests,
)
from ai_data_quality_poc.services.llm_adapter import (
    LiveAssessmentLLMAdapter,
    MockAdapterMode,
    MockAssessmentLLMAdapter,
    is_live_llm_configured,
)

NAV_OPTIONS = [
    "Executive summary",
    "Assessment Approach",
    "AI Assessment",
    "Exceptions",
    "Chat",
]

METHODOLOGY_DIAGRAM_PATH = (
    Path(__file__).resolve().parent / "assets" / "assessment_methodology_overview.png"
)


def _apply_moorhouse_theme() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');

        :root {
            --mh-font-sans: "Poppins", "Segoe UI", Arial, sans-serif;
            --mh-brand: #3c1053;
            --mh-brand-accent: #00ab8e;
            --mh-brand-purple: #5c068c;
            --mh-brand-orange: #e48949;
            --mh-brand-muted: #bdb6b9;
            --mh-brand-ocean: #186e7e;
            --mh-text: #111827;
            --mh-text-muted: #4b5563;
            --mh-surface: #ffffff;
            --mh-surface-muted: #f8fafc;
            --mh-border: #e5e7eb;
            --mh-danger: #b91c1c;
        }

        html, body,
        [data-testid="stAppViewContainer"],
        [data-testid="stAppViewContainer"] *,
        [data-testid="stSidebar"] *,
        [data-testid="stMetric"],
        [data-testid="stDataFrameResizable"],
        [data-testid="stDataFrameResizable"] * {
            font-family: var(--mh-font-sans) !important;
        }

        .material-icons,
        .material-symbols,
        .material-symbols-rounded,
        .material-symbols-outlined,
        .material-symbols-sharp,
        span[class^="material-symbols"],
        [data-testid="stIconMaterial"] {
            font-family: "Material Symbols Rounded" !important;
            font-variation-settings: "FILL" 0, "wght" 400, "GRAD" 0, "opsz" 24;
        }

        .stApp {
            background: var(--mh-surface-muted);
            color: var(--mh-text);
        }

        h1, h2, h3,
        [data-testid="stMarkdownContainer"] h1,
        [data-testid="stMarkdownContainer"] h2,
        [data-testid="stMarkdownContainer"] h3 {
            color: var(--mh-brand);
            letter-spacing: -0.01em;
            font-weight: 600;
        }

        h4, h5, h6,
        [data-testid="stMarkdownContainer"] h4,
        [data-testid="stMarkdownContainer"] h5,
        [data-testid="stMarkdownContainer"] h6 {
            color: var(--mh-brand-purple);
            letter-spacing: -0.01em;
        }

        [data-testid="stCaptionContainer"],
        [data-testid="stCaptionContainer"] p {
            color: var(--mh-text-muted) !important;
        }

        [data-testid="stSidebar"] {
            background: var(--mh-surface);
            border-right: 1px solid var(--mh-border);
        }

        section[data-testid="stSidebar"] {
            background: var(--mh-surface);
            border-right: 1px solid var(--mh-border);
        }

        section[data-testid="stSidebar"] * {
            color: var(--mh-text) !important;
        }

        [data-testid="stSidebar"] [role="radiogroup"] label:hover {
            border-color: rgba(0, 171, 142, 0.35);
            background: rgba(0, 171, 142, 0.08);
        }

        [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
            border-color: rgba(60, 16, 83, 0.35);
            background: rgba(60, 16, 83, 0.08);
        }

        [data-testid="stSidebarNav"] { display: none; }

        a,
        a:visited {
            color: var(--mh-brand-ocean);
        }

        a:hover {
            color: var(--mh-brand-accent);
        }

        [data-testid="stMetric"] {
            background: var(--mh-surface);
            border: 1px solid var(--mh-border);
            border-radius: 12px;
            padding: 8px 10px;
        }

        [data-testid="stButton"] > button {
            border-radius: 10px;
            border: 1px solid var(--mh-brand);
            color: var(--mh-brand);
            background: #ffffff;
            font-weight: 600;
            letter-spacing: -0.01em;
        }

        [data-testid="stButton"] > button:hover {
            color: #ffffff !important;
            background: var(--mh-brand-purple);
            border-color: var(--mh-brand-purple);
        }

        button[kind="primary"] {
            background: var(--mh-brand) !important;
            color: #ffffff !important;
            border-color: var(--mh-brand) !important;
        }

        button[kind="primary"]:hover {
            background: var(--mh-brand-purple) !important;
            color: #ffffff !important;
            border-color: var(--mh-brand-purple) !important;
        }

        button:focus-visible,
        input:focus-visible,
        select:focus-visible,
        textarea:focus-visible {
            outline: 3px solid rgba(0, 171, 142, 0.35) !important;
            outline-offset: 2px !important;
        }

        .mh-card {
            background: var(--mh-surface);
            border: 1px solid var(--mh-border);
            border-radius: 12px;
            padding: 12px 14px;
            min-height: 90px;
        }

        .mh-card__label {
            font-size: 0.78rem;
            color: var(--mh-text-muted);
            margin-bottom: 4px;
            letter-spacing: 0.01em;
        }

        .mh-card__value {
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--mh-text);
            line-height: 1.2;
        }

        .mh-card__meta {
            margin-top: 6px;
            color: var(--mh-text-muted);
            font-size: 0.78rem;
        }

        .mh-pill {
            display: inline-block;
            padding: 2px 10px;
            border-radius: 999px;
            border: 1px solid var(--mh-border);
            font-size: 0.74rem;
            font-weight: 600;
            letter-spacing: 0.01em;
            margin-right: 6px;
            margin-top: 4px;
            color: var(--mh-text);
            background: #ffffff;
        }

        .mh-pill--ok {
            border-color: rgba(0, 171, 142, 0.45);
            background: rgba(0, 171, 142, 0.08);
            color: #0f766e;
        }

        .mh-pill--warn {
            border-color: rgba(228, 137, 73, 0.45);
            background: rgba(228, 137, 73, 0.08);
            color: #9a3412;
        }

        .mh-pill--risk {
            border-color: rgba(185, 28, 28, 0.45);
            background: rgba(185, 28, 28, 0.08);
            color: #991b1b;
        }

        .mh-callout {
            background: var(--mh-surface);
            border: 1px solid var(--mh-border);
            border-left: 6px solid var(--mh-brand-accent);
            border-radius: 12px;
            padding: 12px 16px;
            margin: 10px 0;
            color: var(--mh-text);
        }

        .mh-callout--amber { border-left-color: var(--mh-brand-orange); }
        .mh-callout--red { border-left-color: var(--mh-danger); }

        [data-testid="stAppViewContainer"] p,
        [data-testid="stAppViewContainer"] li,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] li {
            color: var(--mh-text);
            line-height: 1.5;
            font-size: 0.95rem;
        }

        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] h4,
        [data-testid="stSidebar"] h5,
        [data-testid="stSidebar"] h6 {
            color: var(--mh-brand);
            letter-spacing: -0.01em;
        }

        [data-testid="stSidebar"] [role="radiogroup"] label {
            border: 1px solid var(--mh-border);
            border-radius: 10px;
            padding: 6px 10px;
            margin-bottom: 6px;
        }

        [data-testid="stSelectbox"],
        [data-testid="stTextInput"],
        [data-testid="stCheckbox"] {
            background: var(--mh-surface);
            border-radius: 10px;
        }

        [data-testid="stDataFrame"] {
            border: 1px solid var(--mh-border);
            border-radius: 12px;
            overflow: hidden;
        }

        [data-testid="stDataFrame"] th {
            background: rgba(60, 16, 83, 0.06);
            color: var(--mh-brand);
            font-weight: 600;
        }

        [data-testid="stAlert"] {
            border-radius: 12px;
            border: 1px solid var(--mh-border);
        }

        @media (prefers-reduced-motion: reduce) {
            * {
                animation-duration: 0s !important;
                transition-duration: 0s !important;
                scroll-behavior: auto !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _format_currency(amount: Decimal | None) -> str:
    if amount is None:
        return "-"
    return f"£{amount:,.2f}"


def _format_request_option(service_request: ServiceRequestSummary) -> str:
    recorded = service_request.recorded_status.replace("_", " ").title()
    return f"{service_request.id} | {service_request.customer_name} | recorded: {recorded}"


def _render_card(label: str, value: str, meta: str | None = None) -> None:
    meta_html = "" if meta is None else f"<div class='mh-card__meta'>{escape(meta)}</div>"
    st.markdown(
        (
            "<div class='mh-card'>"
            f"<div class='mh-card__label'>{escape(label)}</div>"
            f"<div class='mh-card__value'>{escape(value)}</div>"
            f"{meta_html}</div>"
        ),
        unsafe_allow_html=True,
    )


def _render_pill(label: str, tone: Literal["ok", "warn", "risk"] = "ok") -> None:
    st.markdown(
        f"<span class='mh-pill mh-pill--{tone}'>{escape(label)}</span>",
        unsafe_allow_html=True,
    )


def _navigate_to(page: str) -> None:
    st.session_state["nav_page_override"] = page
    st.rerun()


def _render_result(result: AssessmentRunResult, recorded_status: str) -> None:
    st.subheader("Assessment output")

    if result.kind == "failure":
        st.error("Assessment failed validation and was not accepted as a valid recommendation.")
        st.write(f"Failure code: `{result.error_code}`")
        st.write(f"Message: {result.message}")
        _render_pill("Failure recorded", tone="risk")
        if result.usage is not None:
            with st.expander("Technical usage details"):
                st.write(result.usage.model_dump())
        return

    contract = result.contract
    usage = result.usage

    card_col_1, card_col_2, card_col_3, card_col_4 = st.columns(4)
    with card_col_1:
        _render_card("Recorded status", status_label(recorded_status))
    with card_col_2:
        _render_card("AI recommendation", status_label(contract.recommended_status))
    with card_col_3:
        _render_card("Confidence", confidence_label(contract.confidence))
    with card_col_4:
        _render_card(
            "Token usage",
            f"{usage.input_tokens + usage.output_tokens}",
            meta=f"{usage.duration_ms} ms",
        )

    st.write("Recommendation explanation")
    st.write(contract.explanation)

    st.write("Supporting evidence")
    if contract.evidence:
        supporting = [item for item in contract.evidence if item.evidence_type == "supporting"]
        contradictory = [
            item for item in contract.evidence if item.evidence_type == "contradictory"
        ]

        for item in supporting:
            st.markdown(f"- `{item.source_type}:{item.source_id}` — {item.explanation}")

        st.write("Contradictory evidence")
        if contradictory:
            for item in contradictory:
                st.markdown(f"- `{item.source_type}:{item.source_id}` — {item.explanation}")
        else:
            st.write("No contradictory evidence returned.")
    else:
        st.write("No evidence entries were returned.")

    st.write("Missing evidence")
    if contract.missing_evidence:
        for missing in contract.missing_evidence:
            st.markdown(f"- {missing}")
    else:
        st.write("No explicit missing evidence reported.")

    st.write("Exceptions")
    if contract.exceptions:
        for exception in contract.exceptions:
            st.markdown(f"- `{exception.exception_type}` — {exception.description}")
    else:
        st.write("No exceptions reported.")


def _render_latest_saved_summary(service_request_id: str) -> None:
    latest_saved = get_latest_assessment_summary(service_request_id)
    if latest_saved is None:
        st.caption("No saved assessments yet for this service request.")
        return

    st.caption(
        f"Latest saved assessment: {latest_saved.assessment_id} "
        f"({latest_saved.created_at:%Y-%m-%d %H:%M:%S})"
    )

    card_col_1, card_col_2, card_col_3, card_col_4 = st.columns(4)
    with card_col_1:
        _render_card("Saved status", latest_saved.assessment_status.title())
    with card_col_2:
        _render_card("Saved recommendation", status_label(latest_saved.recommended_status))
    with card_col_3:
        _render_card("Saved confidence", confidence_label(latest_saved.confidence))
    with card_col_4:
        _render_card("Saved cost", _format_currency(latest_saved.total_cost))


def _render_assessment_output_history(service_request_id: str) -> None:
    st.subheader("Saved assessment outputs")
    st.caption(
        "Persisted runs for this case, including AI recommendation, exceptions, cost and run time."
    )

    records = list_assessment_run_records(service_request_id=service_request_id, limit=30)
    if not records:
        st.info("No saved runs yet for this case.")
        return

    sort_option = st.selectbox(
        "Sort saved runs",
        options=["Newest first", "Oldest first", "Highest cost", "Longest duration"],
        key=f"assessment_output_sort_{service_request_id}",
    )

    if sort_option == "Oldest first":
        sorted_records = sorted(records, key=lambda record: record.assessment_created_at)
    elif sort_option == "Highest cost":
        sorted_records = sorted(records, key=lambda record: record.total_cost, reverse=True)
    elif sort_option == "Longest duration":
        sorted_records = sorted(records, key=lambda record: record.duration_ms, reverse=True)
    else:
        sorted_records = sorted(
            records,
            key=lambda record: (record.assessment_created_at, record.assessment_id),
            reverse=True,
        )

    total_runs = len(records)
    success_runs = sum(1 for record in records if record.assessment_status == "success")
    failed_runs = total_runs - success_runs
    total_tokens = sum(record.input_tokens + record.output_tokens for record in records)
    total_cost = sum((record.total_cost for record in records), Decimal("0"))
    avg_duration_ms = int(sum(record.duration_ms for record in records) / total_runs)

    metric_col_1, metric_col_2, metric_col_3, metric_col_4, metric_col_5 = st.columns(5)
    with metric_col_1:
        _render_card("Runs", str(total_runs))
    with metric_col_2:
        _render_card("Successful", str(success_runs))
    with metric_col_3:
        _render_card("Failed", str(failed_runs))
    with metric_col_4:
        _render_card("Total tokens", f"{total_tokens}")
    with metric_col_5:
        _render_card("Total cost", _format_currency(total_cost))

    st.caption(f"Average run time: {avg_duration_ms} ms")

    table_rows = [
        {
            "created_at": record.assessment_created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "assessment_id": record.assessment_id,
            "run_status": record.assessment_status,
            "recorded_status": status_label(record.recorded_status_snapshot),
            "ai_recommendation": status_label(record.recommended_status),
            "confidence": confidence_label(record.confidence),
            "evidence_count": record.evidence_count,
            "exception_count": record.exception_count,
            "input_tokens": record.input_tokens,
            "output_tokens": record.output_tokens,
            "duration_ms": record.duration_ms,
            "cost_gbp": f"{record.total_cost:.6f}",
            "model": record.model_name,
        }
        for record in sorted_records
    ]

    st.dataframe(table_rows, hide_index=True, width="stretch")

    csv_header = [
        "created_at",
        "assessment_id",
        "run_status",
        "recorded_status",
        "ai_recommendation",
        "confidence",
        "evidence_count",
        "exception_count",
        "input_tokens",
        "output_tokens",
        "duration_ms",
        "cost_gbp",
        "model",
    ]
    csv_lines = [",".join(csv_header)]
    for row in table_rows:
        csv_values = [str(row[column]).replace(",", " ") for column in csv_header]
        csv_lines.append(",".join(csv_values))

    st.download_button(
        "Download saved runs CSV",
        data="\n".join(csv_lines),
        file_name=f"{service_request_id}_saved_assessment_outputs.csv",
        mime="text/csv",
        key=f"assessment_output_csv_{service_request_id}",
    )


AssessmentStatusFilter = Literal["success", "failed"] | None
ConfidenceFilter = Literal["high", "medium", "low"] | None


def _parse_status_filter(value: str) -> AssessmentStatusFilter:
    if value == "success":
        return "success"
    if value == "failed":
        return "failed"
    return None


def _parse_confidence_filter(value: str) -> ConfidenceFilter:
    if value == "high":
        return "high"
    if value == "medium":
        return "medium"
    if value == "low":
        return "low"
    return None


def _render_shared_sidebar_filters() -> tuple[AssessmentStatusFilter, ConfidenceFilter]:
    st.sidebar.markdown("### Global Filters")
    status_option = st.sidebar.selectbox(
        "Assessment status",
        options=["All", "success", "failed"],
        key="global_filter_status",
    )
    confidence_option = st.sidebar.selectbox(
        "Confidence",
        options=["All", "high", "medium", "low"],
        key="global_filter_confidence",
    )
    return _parse_status_filter(status_option), _parse_confidence_filter(confidence_option)


def _render_filter_scope_hint(
    assessment_status_filter: AssessmentStatusFilter,
    confidence_filter: ConfidenceFilter,
) -> None:
    status_text = assessment_status_filter or "all"
    confidence_text = confidence_filter or "all"
    st.caption(f"Global filter scope -> status: {status_text} | confidence: {confidence_text}")


def _render_executive_page(
    assessment_status_filter: AssessmentStatusFilter,
    confidence_filter: ConfidenceFilter,
) -> None:
    st.subheader("Executive summary")
    st.caption("Operational snapshot of outcomes, risk and cost from persisted assessments.")
    _render_filter_scope_hint(assessment_status_filter, confidence_filter)

    metrics = get_executive_metrics(
        assessment_status_filter=assessment_status_filter,
        confidence_filter=confidence_filter,
    )

    kpi_col_1, kpi_col_2, kpi_col_3, kpi_col_4, kpi_col_5 = st.columns(5)
    with kpi_col_1:
        _render_card("Cases assessed", str(metrics.total_cases_assessed))
    with kpi_col_2:
        _render_card("Notes assessed", str(metrics.total_notes_assessed))
    with kpi_col_3:
        _render_card(
            "Status alignment",
            f"{metrics.status_alignment_percent_success}%",
            meta=(
                f"{metrics.status_alignment_matched_success}/"
                f"{metrics.status_alignment_total_success} successful runs"
            ),
        )
    with kpi_col_4:
        _render_card("Total cost", _format_currency(metrics.total_cost))
    with kpi_col_5:
        _render_card("Top exception", metrics.top_exception_type or "None")

    detail_col_1, detail_col_2, detail_col_3 = st.columns(3)
    with detail_col_1:
        _render_card("Assessment runs", str(metrics.total_assessments))
    with detail_col_2:
        _render_card("Cases with exceptions", str(metrics.cases_with_exceptions))
    with detail_col_3:
        _render_card(
            "Token usage",
            f"{metrics.total_input_tokens + metrics.total_output_tokens}",
            meta=f"input {metrics.total_input_tokens} | output {metrics.total_output_tokens}",
        )

    if metrics.total_assessments == 0:
        callout_class = "mh-callout"
        callout_text = (
            "No assessments match the current filters yet. "
            "Adjust filters or run additional AI assessments."
        )
    elif (
        metrics.failed_assessments > 0
        or metrics.cases_with_exceptions >= metrics.total_cases_assessed
    ):
        callout_class = "mh-callout mh-callout--red"
        callout_text = (
            "High-risk profile. Review exception-heavy or failed assessments "
            "in Exceptions before sharing externally."
        )
    elif metrics.cases_with_exceptions > 0:
        callout_class = "mh-callout mh-callout--amber"
        callout_text = (
            "Moderate-risk profile. Monitor exception themes and confirm whether "
            "status mismatches need operational follow-up."
        )
    else:
        callout_class = "mh-callout"
        callout_text = (
            "Stable profile. Exceptions are limited and most assessments complete successfully."
        )

    st.markdown(
        f"<div class='{callout_class}'>{escape(callout_text)}</div>", unsafe_allow_html=True
    )

    st.write("Current risk signal")
    if (
        metrics.failed_assessments > 0
        or metrics.cases_with_exceptions >= metrics.total_cases_assessed
    ):
        _render_pill("High risk", tone="risk")
    elif metrics.cases_with_exceptions > 0:
        _render_pill("Moderate risk", tone="warn")
    else:
        _render_pill("Stable", tone="ok")

    st.write("Quick actions")
    action_col_1, action_col_2 = st.columns(2)
    if action_col_1.button("View exceptions"):
        _navigate_to("Exceptions")
    if action_col_2.button("Open assessment workflow"):
        _navigate_to("AI Assessment")

    recent_exception_records = list_exception_records(
        assessment_status_filter=assessment_status_filter,
        confidence_filter=confidence_filter,
        limit=5,
    )
    if recent_exception_records:
        st.write("Recent exception records")
        st.dataframe(
            [
                {
                    "service_request_id": record.service_request_id,
                    "customer_name": record.customer_name,
                    "created_at": record.assessment_created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "assessment_status": record.assessment_status,
                    "exception_type": record.exception_type,
                }
                for record in recent_exception_records
            ],
            hide_index=True,
            width="stretch",
        )

def _render_assessment_approach_page() -> None:
    st.subheader("Assessment Approach")
    st.caption("How the AI recommendation is produced, validated and governed.")

    st.markdown(
        """
        <div class='mh-callout'>
        This page explains the method end-to-end so decisions are auditable, repeatable,
        and easier to trust before operational use.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if METHODOLOGY_DIAGRAM_PATH.exists():
        st.image(
            str(METHODOLOGY_DIAGRAM_PATH),
            caption="AI Data Quality PoC methodology overview",
            use_container_width=True,
            output_format="PNG",
        )
    else:
        st.warning("Methodology diagram file not found in app/assets.")

    st.markdown("### 1) Inputs used")
    st.write(
        "Each run uses a connected case context: service request baseline, interaction notes, "
        "quotes and payment signals."
    )

    st.markdown("### 2) Decision logic")
    st.write(
        "The model receives structured context and returns a recommended lifecycle status, "
        "confidence level, and rationale."
    )

    st.markdown("### 3) Validation and exceptions")
    st.write(
        "Outputs are validated against the contract. Invalid or inconsistent outputs are recorded "
        "as exceptions for triage rather than silently accepted."
    )

    st.markdown("### 4) Persistence and transparency")
    st.write(
        "Every accepted run is persisted with status, confidence, explanation, and usage metadata "
        "so executive and exceptions views remain evidence-backed."
    )

    st.markdown("### 5) Cost and rerun guard")
    st.write(
        "The app checks for an existing assessment summary first and avoids unnecessary re-runs "
        "unless the user explicitly forces a refresh."
    )

    st.markdown("### 6) Filter strategy")
    st.write(
        "Global and page-level filters should stay consistent "
        "as users move from executive view to case-level "
        "and exception-level analysis without metric mismatch."
    )

    st.markdown("### 7) PostgreSQL persistence and connections")
    st.write(
        "PostgreSQL is the system-of-record for this PoC. "
        "Source context is read from PostgreSQL, assessment outputs are written back "
        "to PostgreSQL, and summary pages only read persisted records."
    )
    st.write(
        "Connection flow: UI -> service layer -> repository/SQL -> PostgreSQL. "
        "This keeps logic in Python services while the database remains the audit trail."
    )



def _render_assessment_page(
    service_requests: list[ServiceRequestSummary],
    assessment_status_filter: AssessmentStatusFilter,
    confidence_filter: ConfidenceFilter,
) -> None:
    _render_filter_scope_hint(assessment_status_filter, confidence_filter)

    with st.expander("What this page is doing (plain English)", expanded=True):
        st.write(
            "This page is structured in three levels: run-set metrics, full SR output table, "
            "then deep-dive into an individual SR."
        )
        st.write(
            "You can use the table to compare all cases quickly, then drill into one case to "
            "inspect notes/quotes/payments and run or rerun assessment."
        )

    st.markdown("### 1) Run-set metrics")
    metrics = get_executive_metrics(
        assessment_status_filter=assessment_status_filter,
        confidence_filter=confidence_filter,
    )

    metric_col_1, metric_col_2, metric_col_3, metric_col_4, metric_col_5, metric_col_6 = st.columns(6)
    with metric_col_1:
        _render_card("Assessment runs", str(metrics.total_assessments))
    with metric_col_2:
        _render_card("Cases assessed", str(metrics.total_cases_assessed))
    with metric_col_3:
        _render_card(
            "Status alignment",
            f"{metrics.status_alignment_percent_success}%",
            meta=(
                f"{metrics.status_alignment_matched_success}/"
                f"{metrics.status_alignment_total_success} successful runs"
            ),
        )
    with metric_col_4:
        _render_card("Total tokens", str(metrics.total_input_tokens + metrics.total_output_tokens))
    with metric_col_5:
        _render_card("Total cost", _format_currency(metrics.total_cost))
    with metric_col_6:
        _render_card("Cases with exceptions", str(metrics.cases_with_exceptions))

    st.markdown("### 2) Full SR output table")

    run_counts = list_assessment_run_counts()
    note_counts = list_interaction_note_counts()

    table_rows: list[dict[str, str | int]] = []
    for service_request in service_requests:
        latest_saved = get_latest_assessment_summary(service_request.id)
        if latest_saved is None:
            run_status = "not_run"
            ai_status = "-"
            confidence = "-"
            latest_cost = "-"
            latest_run_at = "-"
            saved_model = "-"
            latest_assessment_status = None
            latest_confidence = None
        else:
            run_status = latest_saved.assessment_status
            ai_status = status_label(latest_saved.recommended_status)
            confidence = confidence_label(latest_saved.confidence)
            latest_cost = _format_currency(latest_saved.total_cost)
            latest_run_at = latest_saved.created_at.strftime("%Y-%m-%d %H:%M:%S")
            saved_model = latest_saved.model_name
            latest_assessment_status = latest_saved.assessment_status
            latest_confidence = latest_saved.confidence

        if (
            assessment_status_filter is not None
            and latest_assessment_status != assessment_status_filter
        ):
            continue
        if confidence_filter is not None and latest_confidence != confidence_filter:
            continue

        table_rows.append(
            {
                "service_request_id": service_request.id,
                "customer_name": service_request.customer_name,
                "recorded_status": status_label(service_request.recorded_status),
                "ai_status": ai_status,
                "confidence": confidence,
                "notes": note_counts.get(service_request.id, 0),
                "runs": run_counts.get(service_request.id, 0),
                "latest_run_status": run_status,
                "latest_cost": latest_cost,
                "latest_run_at": latest_run_at,
                "model": saved_model,
            }
        )

    if not table_rows:
        st.info("No SR rows match current filters.")
        return

    st.dataframe(table_rows, hide_index=True, width="stretch")

    selectable_case_ids = [row["service_request_id"] for row in table_rows]

    st.markdown("### 3) SR deep dive")
    selected_service_request_id = st.selectbox(
        "Select SR to inspect",
        options=selectable_case_ids,
        key="assessment_deep_dive_sr",
    )

    selected_request = next(
        request for request in service_requests if request.id == selected_service_request_id
    )

    live_llm_ready = is_live_llm_configured()
    live_mode_label = "Live LLM" if live_llm_ready else "Live LLM (Configuration required)"

    assessment_engine_mode = st.selectbox(
        "Assessment mode",
        options=["Mock (Demo/QA)", live_mode_label],
        help=(
            "Use Mock mode for deterministic demos and QA. "
            "Live mode uses provider configuration from environment variables."
        ),
    )
    is_live_mode = assessment_engine_mode == live_mode_label

    mock_mode: MockAdapterMode = "valid"
    if not is_live_mode:
        mock_mode = st.selectbox(
            "Mock response profile",
            options=["valid", "insufficient", "invalid_status", "unknown_evidence"],
            help="Choose a deterministic mock profile for QA coverage.",
        )
    elif not live_llm_ready:
        st.warning(
            "Live LLM mode requires AZURE_OPENAI_API_KEY and AZURE_OPENAI_BASE_URL. "
            "Switch to Mock mode or configure live credentials."
        )
    else:
        st.success("Live LLM mode is configured and ready.")

    force_rerun = st.checkbox(
        "Force rerun",
        value=False,
        help="Run again even when no source-data changes are detected.",
    )

    if (
        st.session_state.get("assessment_service_request_id") == selected_request.id
        and st.session_state.get("assessment_result") is not None
    ):
        st.warning("Re-running assessment will replace current in-session result for this case.")

    try:
        case_context = get_case_context(selected_request.id)
    except CaseContextNotFoundError as exc:
        st.error(str(exc))
        return

    st.session_state["selected_service_request_id"] = selected_request.id

    summary_col_1, summary_col_2, summary_col_3, summary_col_4 = st.columns(4)
    with summary_col_1:
        _render_card("Recorded status", status_label(case_context.service_request.recorded_status))
    with summary_col_2:
        _render_card("Notes", str(len(case_context.interaction_notes)))
    with summary_col_3:
        _render_card("Quotes", str(len(case_context.quotes)))
    with summary_col_4:
        _render_card("Payments", str(len(case_context.payments)))

    _render_latest_saved_summary(selected_request.id)
    _render_assessment_output_history(selected_request.id)

    context_col_1, context_col_2 = st.columns([1.5, 1.0])

    with context_col_1:
        st.subheader("Interaction notes")
        for note in case_context.interaction_notes:
            with st.expander(
                f"{note.note_timestamp:%Y-%m-%d %H:%M} | {note.note_category} | {note.author_role}",
                expanded=False,
            ):
                st.write(note.note_text)
                st.caption(f"Source ID: {note.id}")

    with context_col_2:
        st.subheader("Quotes")
        if case_context.quotes:
            for quote in case_context.quotes:
                st.markdown(
                    f"- `{quote.id}` | {quote.quote_timestamp:%Y-%m-%d} | "
                    f"{quote.quote_status} | {_format_currency(quote.amount)}"
                )
        else:
            st.write("No quotes available.")

        st.subheader("Payments")
        if case_context.payments:
            for payment in case_context.payments:
                st.markdown(
                    f"- `{payment.id}` | {payment.payment_timestamp:%Y-%m-%d} | "
                    f"{payment.payment_status} | {_format_currency(payment.amount)}"
                )
        else:
            st.write("No payments available.")

    run_button_label = "Run assessment"
    run_button_disabled = False
    if is_live_mode and not live_llm_ready:
        run_button_label = "Run assessment (Configure Live LLM first)"
        run_button_disabled = True

    if st.button(run_button_label, type="primary", disabled=run_button_disabled):
        rerun_decision = should_run_assessment(
            service_request_id=selected_request.id,
            case_context=case_context,
            force_rerun=force_rerun,
        )

        if not rerun_decision.should_run:
            st.info(
                "No source-data changes detected since latest saved assessment. "
                "Skipped rerun to avoid unnecessary token cost."
            )
        else:
            if is_live_mode:
                try:
                    adapter = LiveAssessmentLLMAdapter.from_env()
                except ValueError as exc:
                    st.error(f"Live LLM configuration error: {exc}")
                    return
            else:
                adapter = MockAssessmentLLMAdapter(mode=mock_mode)

            result = run_assessment(case_context, adapter)

            try:
                persisted_assessment_id = persist_assessment_run(
                    service_request_id=selected_request.id,
                    recorded_status_snapshot=case_context.service_request.recorded_status,
                    result=result,
                )
                st.success(f"Assessment saved: {persisted_assessment_id}")
                st.caption(f"Rerun reason: {rerun_decision.reason}")
            except Exception as exc:
                st.error(f"Assessment generated but failed to save: {exc}")

            st.session_state["assessment_result"] = result
            st.session_state["assessment_service_request_id"] = selected_request.id
            st.session_state["assessment_mode"] = assessment_engine_mode

    if (
        st.session_state.get("assessment_service_request_id") == selected_request.id
        and st.session_state.get("assessment_result") is not None
    ):
        st.caption(
            f"Latest in-session result mode: {st.session_state.get('assessment_mode', 'unknown')}"
        )
        _render_result(
            st.session_state["assessment_result"], case_context.service_request.recorded_status
        )


def _render_chat_page(
    assessment_status_filter: AssessmentStatusFilter,
    confidence_filter: ConfidenceFilter,
) -> None:
    st.subheader("Chat")
    st.caption("Governed conversational summary over persisted assessment outcomes.")
    _render_filter_scope_hint(assessment_status_filter, confidence_filter)

    metrics = get_executive_metrics(
        assessment_status_filter=assessment_status_filter,
        confidence_filter=confidence_filter,
    )
    exception_records = list_exception_records(
        assessment_status_filter=assessment_status_filter,
        confidence_filter=confidence_filter,
        limit=50,
    )

    summary_col_1, summary_col_2, summary_col_3 = st.columns(3)
    with summary_col_1:
        _render_card("Assessments in scope", str(metrics.total_assessments))
    with summary_col_2:
        _render_card("Exceptions in scope", str(metrics.total_exceptions))
    with summary_col_3:
        _render_card("Top exception", metrics.top_exception_type or "None")

    if metrics.total_assessments == 0:
        st.info(
            "No persisted assessments match the current global filters. "
            "Adjust filters to enable governed chat outputs."
        )
        return

    question = st.text_input(
        "Ask a question about the filtered assessment outcomes",
        placeholder="e.g. What is the key risk in this filtered scope?",
    )

    if st.button("Generate governed response"):
        lowered = question.strip().lower()
        response_lines = [
            f"The current scope contains {metrics.total_assessments} assessments.",
            (
                "Status mix is "
                f"{metrics.successful_assessments} successful "
                f"and {metrics.failed_assessments} failed."
            ),
            (
                "Cases with exceptions: "
                f"{metrics.cases_with_exceptions} out of {metrics.total_cases_assessed}."
            ),
        ]

        if "cost" in lowered or "token" in lowered:
            response_lines.append(
                f"Token usage is {metrics.total_input_tokens + metrics.total_output_tokens} "
                f"with total estimated cost {_format_currency(metrics.total_cost)}."
            )
        elif "risk" in lowered or "exception" in lowered:
            response_lines.append(
                f"Top exception in this scope is {metrics.top_exception_type or 'None'}."
            )
        elif "confidence" in lowered:
            response_lines.append(
                "Confidence distribution follows the active global confidence filter scope."
            )
        else:
            response_lines.append(
                "Use targeted prompts (risk, cost, exceptions, confidence) for sharper responses."
            )

        st.markdown("### Governed response")
        for line in response_lines:
            st.markdown(f"- {line}")

    if exception_records:
        st.markdown("### Evidence snapshot (recent exceptions)")
        st.dataframe(
            [
                {
                    "service_request_id": record.service_request_id,
                    "assessment_status": record.assessment_status,
                    "confidence": record.confidence,
                    "exception_type": record.exception_type,
                    "created_at": record.assessment_created_at.strftime("%Y-%m-%d %H:%M:%S"),
                }
                for record in exception_records[:10]
            ],
            hide_index=True,
            width="stretch",
        )



def _render_exceptions_page(
    assessment_status_filter: AssessmentStatusFilter,
    confidence_filter: ConfidenceFilter,
) -> None:
    st.subheader("Exceptions")
    st.caption("Persisted assessment exceptions, with filters and quick drill-back to assessment.")
    _render_filter_scope_hint(assessment_status_filter, confidence_filter)

    exception_counts = list_exception_counts(
        assessment_status_filter=assessment_status_filter,
        confidence_filter=confidence_filter,
    )
    exception_records_total = sum(item.count for item in exception_counts)

    if not exception_counts:
        st.info("No exceptions match the current global filters.")
        return

    unique_exception_types = len(exception_counts)
    count_col_1, count_col_2 = st.columns(2)
    with count_col_1:
        _render_card("Total exception records", str(exception_records_total))
    with count_col_2:
        _render_card("Exception types", str(unique_exception_types))

    st.write("Exception counts by type")
    for item in sorted(exception_counts, key=lambda value: value.count, reverse=True):
        st.markdown(f"- `{item.exception_type}`: {item.count}")

    all_exception_types = sorted(item.exception_type for item in exception_counts)
    exception_filter_label = st.selectbox(
        "Filter by exception type",
        options=["All", *all_exception_types],
    )

    exception_filter = None if exception_filter_label == "All" else exception_filter_label

    records = list_exception_records(
        exception_type_filter=exception_filter,
        assessment_status_filter=assessment_status_filter,
        confidence_filter=confidence_filter,
        limit=300,
    )

    if not records:
        st.info("No exception records match the selected filters.")
        return

    st.write(f"Showing {len(records)} record(s)")
    st.dataframe(
        [
            {
                "assessment_id": record.assessment_id,
                "service_request_id": record.service_request_id,
                "customer_name": record.customer_name,
                "created_at": record.assessment_created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "assessment_status": record.assessment_status,
                "recommended_status": record.recommended_status,
                "confidence": record.confidence,
                "exception_type": record.exception_type,
                "description": record.description,
            }
            for record in records
        ],
        hide_index=True,
        width="stretch",
    )

    case_options = sorted({record.service_request_id for record in records})
    target_case_id = st.selectbox("Open case in AI Assessment page", options=case_options)
    if st.button("Open selected case"):
        st.session_state["selected_service_request_id"] = target_case_id
        _navigate_to("AI Assessment")

def main() -> None:
    st.set_page_config(page_title="AI Data Quality PoC", layout="wide")
    _apply_moorhouse_theme()

    st.title("AI Data Quality PoC")
    st.caption(
        "Evidence-backed lifecycle recommendation from connected synthetic operational data."
    )
    st.info("Synthetic data only — no client-derived records are used in this PoC.")

    service_requests = list_service_requests()
    if not service_requests:
        st.warning("No service requests found. Seed the synthetic dataset, then reload this page.")
        return

    if "nav_page_selected" not in st.session_state:
        st.session_state["nav_page_selected"] = NAV_OPTIONS[0]

    override_page = st.session_state.pop("nav_page_override", None)
    if isinstance(override_page, str) and override_page in NAV_OPTIONS:
        st.session_state["nav_page_selected"] = override_page

    selected_page = st.session_state.get("nav_page_selected", NAV_OPTIONS[0])
    default_index = NAV_OPTIONS.index(selected_page) if selected_page in NAV_OPTIONS else 0

    nav_page = st.sidebar.radio(
        "Navigation",
        options=NAV_OPTIONS,
        index=default_index,
        key="nav_page_widget",
    )
    st.session_state["nav_page_selected"] = nav_page

    assessment_status_filter, confidence_filter = _render_shared_sidebar_filters()

    if nav_page == "Executive summary":
        _render_executive_page(assessment_status_filter, confidence_filter)
    elif nav_page == "Assessment Approach":
        _render_assessment_approach_page()
    elif nav_page == "AI Assessment":
        _render_assessment_page(
            service_requests,
            assessment_status_filter,
            confidence_filter,
        )
    elif nav_page == "Exceptions":
        _render_exceptions_page(assessment_status_filter, confidence_filter)
    else:
        _render_chat_page(assessment_status_filter, confidence_filter)


if __name__ == "__main__":
    main()



















