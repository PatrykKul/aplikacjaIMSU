"""post-test fixes (12.11)

Course owner changes made by the admin (D56), cancelled style trials (R7a, D60) and the
form of a drawn question set (D61).

Revision ID: 7d2e9b4c1a35
Revises: 01324f58656d
Create Date: 2026-11-12 20:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7d2e9b4c1a35"
down_revision: str | Sequence[str] | None = "01324f58656d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TRIAL_RESULTS = "'helped', 'neutral', 'worse', 'no_baseline'"


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "course_owner_changes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.Column("from_owner_id", sa.Integer(), nullable=False),
        sa.Column("to_owner_id", sa.Integer(), nullable=False),
        sa.Column("changed_by_id", sa.Integer(), nullable=False),
        sa.Column(
            "changed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["course_id"],
            ["courses.id"],
            name=op.f("fk_course_owner_changes_course_id_courses"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["from_owner_id"],
            ["users.id"],
            name=op.f("fk_course_owner_changes_from_owner_id_users"),
        ),
        sa.ForeignKeyConstraint(
            ["to_owner_id"],
            ["users.id"],
            name=op.f("fk_course_owner_changes_to_owner_id_users"),
        ),
        sa.ForeignKeyConstraint(
            ["changed_by_id"],
            ["users.id"],
            name=op.f("fk_course_owner_changes_changed_by_id_users"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_course_owner_changes")),
    )
    op.create_index(
        op.f("ix_course_owner_changes_course_id"),
        "course_owner_changes",
        ["course_id"],
        unique=False,
    )

    op.drop_constraint(op.f("ck_style_trials_result"), "style_trials", type_="check")
    op.create_check_constraint(
        op.f("ck_style_trials_result"),
        "style_trials",
        f"result IS NULL OR result IN ({TRIAL_RESULTS}, 'cancelled')",
    )

    op.add_column("quiz_draws", sa.Column("form", sa.String(length=1), nullable=True))
    op.create_check_constraint(
        op.f("ck_quiz_draws_form"), "quiz_draws", "form IS NULL OR form IN ('V', 'A', 'K')"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(op.f("ck_quiz_draws_form"), "quiz_draws", type_="check")
    op.drop_column("quiz_draws", "form")

    # A cancelled trial becomes one that ended without a result (the state before R7a)
    op.execute("UPDATE style_trials SET result = NULL WHERE result = 'cancelled'")
    op.drop_constraint(op.f("ck_style_trials_result"), "style_trials", type_="check")
    op.create_check_constraint(
        op.f("ck_style_trials_result"),
        "style_trials",
        f"result IS NULL OR result IN ({TRIAL_RESULTS})",
    )

    op.drop_index(op.f("ix_course_owner_changes_course_id"), table_name="course_owner_changes")
    op.drop_table("course_owner_changes")
