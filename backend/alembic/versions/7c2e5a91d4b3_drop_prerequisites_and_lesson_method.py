"""drop prerequisites and lesson method

Revision ID: 7c2e5a91d4b3
Revises: de25ecb88fc6
Create Date: 2026-11-05 20:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7c2e5a91d4b3"
down_revision: str | Sequence[str] | None = "de25ecb88fc6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema: no prerequisite graph, one lesson per skill."""
    op.drop_index(op.f("ix_skill_prerequisites_prerequisite_id"), table_name="skill_prerequisites")
    op.drop_table("skill_prerequisites")

    # Only the common variant stays; the column's check and unique constraints go with it
    op.execute("DELETE FROM lessons WHERE method <> 'common'")
    op.drop_column("lessons", "method")
    op.create_unique_constraint(op.f("uq_lessons_skill_id"), "lessons", ["skill_id"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(op.f("uq_lessons_skill_id"), "lessons", type_="unique")
    op.add_column(
        "lessons",
        sa.Column(
            "method",
            sa.Enum(
                "common",
                "alpha",
                "beta",
                "gamma",
                "delta",
                name="lesson_method",
                native_enum=False,
                create_constraint=True,
                length=10,
            ),
            server_default="common",
            nullable=False,
        ),
    )
    op.create_unique_constraint(op.f("uq_lessons_skill_id"), "lessons", ["skill_id", "method"])

    op.create_table(
        "skill_prerequisites",
        sa.Column("skill_id", sa.Integer(), nullable=False),
        sa.Column("prerequisite_id", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "skill_id <> prerequisite_id", name=op.f("ck_skill_prerequisites_not_self")
        ),
        sa.ForeignKeyConstraint(
            ["prerequisite_id"],
            ["skills.id"],
            name=op.f("fk_skill_prerequisites_prerequisite_id_skills"),
        ),
        sa.ForeignKeyConstraint(
            ["skill_id"], ["skills.id"], name=op.f("fk_skill_prerequisites_skill_id_skills")
        ),
        sa.PrimaryKeyConstraint("skill_id", "prerequisite_id", name=op.f("pk_skill_prerequisites")),
    )
    op.create_index(
        op.f("ix_skill_prerequisites_prerequisite_id"),
        "skill_prerequisites",
        ["prerequisite_id"],
        unique=False,
    )
