"""neutral survey wording

Survey texts from v1 had masculine forms ("Kupiłeś…", "żeby narysował…", "co robiłem").
This data migration rewrites them in gender-neutral forms (2nd person, present tense for
questions). The meaning and the V / A / K style of every answer stay the same.

Revision ID: c3a91f2d7b40
Revises: 2e7cf4c0d9fc
Create Date: 2026-11-09 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3a91f2d7b40"
down_revision: str | Sequence[str] | None = "2e7cf4c0d9fc"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# (question position, old text, new text)
QUESTIONS = [
    (
        2,
        "Kupiłeś nowe urządzenie. Co robisz najpierw?",
        "Kupujesz nowe urządzenie. Co robisz najpierw?",
    ),
]

# (question position, answer style, old text, new text)
ANSWERS = [
    (
        2,
        "A",
        "Proszę kogoś, żeby mi wyjaśnił, jak to działa",
        "Proszę kogoś o wyjaśnienie, jak to działa",
    ),
    (
        3,
        "K",
        "idziesz kawałek razem z nim i pokazujesz, gdzie skręcić",
        "idziesz kawałek razem z tą osobą i pokazujesz, gdzie skręcić",
    ),
    (
        13,
        "A",
        "żeby ktoś opowiedział Ci krok po kroku, co robić",
        "słuchać instrukcji krok po kroku, co robić",
    ),
    (
        14,
        "K",
        "To, co robiłem: wędrówkę, zwiedzanie, atrakcje",
        "To, co robisz na miejscu: wędrówki, zwiedzanie, atrakcje",
    ),
    (
        15,
        "V",
        "prosisz, żeby to narysował albo pokazał",
        "prosisz o rysunek albo pokazanie tego",
    ),
    (
        15,
        "A",
        "prosisz, żeby powiedział to inaczej, prostszymi słowami",
        "prosisz o wyjaśnienie inaczej, prostszymi słowami",
    ),
    (
        15,
        "K",
        "prosisz, żeby dał Ci spróbować samemu",
        "prosisz o możliwość samodzielnej próby",
    ),
]

questions = sa.table(
    "survey_questions",
    sa.column("id", sa.Integer),
    sa.column("position", sa.Integer),
    sa.column("text", sa.String),
)
answers = sa.table(
    "survey_answers",
    sa.column("question_id", sa.Integer),
    sa.column("style", sa.String),
    sa.column("text", sa.String),
)


def _rewrite(forward: bool) -> None:
    """Change only rows that still have the expected text (texts edited by hand stay)."""
    for position, old, new in QUESTIONS:
        source, target = (old, new) if forward else (new, old)
        op.execute(
            questions.update()
            .where(questions.c.position == position, questions.c.text == source)
            .values(text=target)
        )
    for position, style, old, new in ANSWERS:
        source, target = (old, new) if forward else (new, old)
        question_ids = sa.select(questions.c.id).where(questions.c.position == position)
        op.execute(
            answers.update()
            .where(
                answers.c.question_id.in_(question_ids),
                answers.c.style == style,
                answers.c.text == source,
            )
            .values(text=target)
        )


def upgrade() -> None:
    _rewrite(forward=True)


def downgrade() -> None:
    _rewrite(forward=False)
