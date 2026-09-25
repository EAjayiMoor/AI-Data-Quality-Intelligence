"""Add note_category to interaction_notes

Revision ID: 20260920_0002
Revises: 20260920_0001
Create Date: 2026-09-20
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260920_0002"
down_revision = "20260920_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "interaction_notes",
        sa.Column(
            "note_category", sa.String(length=64), server_default="administrative", nullable=False
        ),
    )
    op.alter_column("interaction_notes", "note_category", server_default=None)


def downgrade() -> None:
    op.drop_column("interaction_notes", "note_category")
