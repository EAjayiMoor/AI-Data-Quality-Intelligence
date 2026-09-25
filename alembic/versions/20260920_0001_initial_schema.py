"""Initial data contract schema

Revision ID: 20260920_0001
Revises:
Create Date: 2026-09-20
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260920_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "service_requests",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("customer_name", sa.String(length=255), nullable=False),
        sa.Column("recorded_status", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "recorded_status IN ('new','quoted','accepted_unpaid','accepted_paid','in_delivery','completed','cancelled','insufficient_evidence')",
            name="ck_service_requests_recorded_status",
        ),
    )

    op.create_table(
        "interaction_notes",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column(
            "service_request_id",
            sa.String(length=64),
            sa.ForeignKey("service_requests.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("note_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("note_text", sa.Text(), nullable=False),
        sa.Column("author_role", sa.String(length=120), nullable=False),
    )

    op.create_table(
        "quotes",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column(
            "service_request_id",
            sa.String(length=64),
            sa.ForeignKey("service_requests.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("quote_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("quote_status", sa.String(length=64), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=True),
    )

    op.create_table(
        "payments",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column(
            "service_request_id",
            sa.String(length=64),
            sa.ForeignKey("service_requests.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("payment_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payment_status", sa.String(length=64), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=True),
    )

    op.create_table(
        "assessments",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column(
            "service_request_id",
            sa.String(length=64),
            sa.ForeignKey("service_requests.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("recorded_status_snapshot", sa.String(length=64), nullable=False),
        sa.Column("recommended_status", sa.String(length=64), nullable=False),
        sa.Column("confidence", sa.String(length=16), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("prompt_version", sa.String(length=64), nullable=False),
        sa.Column("rules_version", sa.String(length=64), nullable=False),
        sa.Column("model_name", sa.String(length=128), nullable=False),
        sa.Column("assessment_status", sa.String(length=16), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "recommended_status IN ('new','quoted','accepted_unpaid','accepted_paid','in_delivery','completed','cancelled','insufficient_evidence')",
            name="ck_assessments_recommended_status",
        ),
        sa.CheckConstraint(
            "confidence IN ('high','medium','low')", name="ck_assessments_confidence"
        ),
        sa.CheckConstraint(
            "assessment_status IN ('success','failed')", name="ck_assessments_status"
        ),
    )

    op.create_table(
        "assessment_evidence",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column(
            "assessment_id",
            sa.String(length=64),
            sa.ForeignKey("assessments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("evidence_type", sa.String(length=32), nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("source_id", sa.String(length=64), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.CheckConstraint(
            "evidence_type IN ('supporting','contradictory')", name="ck_assessment_evidence_type"
        ),
        sa.CheckConstraint(
            "source_type IN ('note','quote','payment')", name="ck_assessment_source_type"
        ),
    )

    op.create_table(
        "assessment_exceptions",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column(
            "assessment_id",
            sa.String(length=64),
            sa.ForeignKey("assessments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("exception_type", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
    )

    op.create_table(
        "cost_tracking",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column(
            "assessment_id",
            sa.String(length=64),
            sa.ForeignKey("assessments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("call_sequence", sa.Integer(), nullable=False),
        sa.Column("model_name", sa.String(length=128), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False),
        sa.Column("output_tokens", sa.Integer(), nullable=False),
        sa.Column("cached_input_tokens", sa.Integer(), nullable=True),
        sa.Column("input_price_per_million", sa.Numeric(12, 4), nullable=False),
        sa.Column("output_price_per_million", sa.Numeric(12, 4), nullable=False),
        sa.Column("calculated_cost", sa.Numeric(14, 6), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("call_status", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )

    op.create_index(
        "ix_interaction_notes_service_request_id_note_timestamp",
        "interaction_notes",
        ["service_request_id", "note_timestamp"],
    )
    op.create_index("ix_quotes_service_request_id", "quotes", ["service_request_id"])
    op.create_index("ix_payments_service_request_id", "payments", ["service_request_id"])
    op.create_index(
        "ix_assessments_service_request_id_created_at",
        "assessments",
        ["service_request_id", "created_at"],
    )
    op.create_index(
        "ix_assessment_exceptions_exception_type",
        "assessment_exceptions",
        ["exception_type"],
    )


def downgrade() -> None:
    op.drop_index("ix_assessment_exceptions_exception_type", table_name="assessment_exceptions")
    op.drop_index("ix_assessments_service_request_id_created_at", table_name="assessments")
    op.drop_index("ix_payments_service_request_id", table_name="payments")
    op.drop_index("ix_quotes_service_request_id", table_name="quotes")
    op.drop_index(
        "ix_interaction_notes_service_request_id_note_timestamp", table_name="interaction_notes"
    )

    op.drop_table("cost_tracking")
    op.drop_table("assessment_exceptions")
    op.drop_table("assessment_evidence")
    op.drop_table("assessments")
    op.drop_table("payments")
    op.drop_table("quotes")
    op.drop_table("interaction_notes")
    op.drop_table("service_requests")
