"""create learning style tables

Revision ID: ea197399889b
Revises: 908770dc9db3
Create Date: 2026-11-08 21:57:23.094403

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ea197399889b"
down_revision: str | Sequence[str] | None = "908770dc9db3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# VAK survey from v1 (legacy/backend/app/seed_ankieta.py): question, answer V, answer A, answer K
VAK_QUESTIONS: list[tuple[str, str, str, str]] = [
    (
        "Gdy uczysz się czegoś nowego, najchętniej…",
        "oglądasz schematy, ilustracje lub film",
        "słuchasz, jak ktoś to tłumaczy",
        "od razu próbujesz zrobić to samodzielnie",
    ),
    (
        "Jak najłatwiej zapamiętujesz nowy materiał?",
        "Gdy widzę go zapisany, z kolorami i wykresami",
        "Gdy powtarzam go na głos albo ktoś mi o nim opowiada",
        "Gdy przerabiam go w praktyce, na przykładach i ćwiczeniach",
    ),
    (
        "Kupiłeś nowe urządzenie. Co robisz najpierw?",
        "Oglądam rysunki w instrukcji albo film pokazowy",
        "Proszę kogoś, żeby mi wyjaśnił, jak to działa",
        "Włączam je i sprawdzam wszystko metodą prób i błędów",
    ),
    (
        "Ktoś pyta Cię o drogę. Najchętniej…",
        "rysujesz mapkę albo pokazujesz trasę na ekranie",
        "opisujesz trasę słowami",
        "idziesz kawałek razem z nim i pokazujesz, gdzie skręcić",
    ),
    (
        "Co najbardziej rozprasza Cię podczas nauki?",
        "Bałagan i ruch w zasięgu wzroku",
        "Hałas i rozmowy w tle",
        "Długie siedzenie bez ruchu",
    ),
    (
        "Na lekcji lub wykładzie najbardziej pomaga Ci…",
        "prezentacja, tablica i wykresy",
        "to, co mówi prowadzący, i dyskusja",
        "ćwiczenia, doświadczenia i zadania do wykonania",
    ),
    (
        "Jak przygotowujesz się do sprawdzianu?",
        "Robię notatki, mapy myśli i zakreślam ważne fragmenty",
        "Opowiadam materiał na głos albo omawiam go z kimś",
        "Rozwiązuję dużo zadań i testów próbnych",
    ),
    (
        "Po spotkaniu z nową osobą najdłużej pamiętasz…",
        "jej twarz i wygląd",
        "jej imię i sposób mówienia",
        "to, co razem robiliście",
    ),
    (
        "Kiedy musisz zapamiętać numer telefonu…",
        "wyobrażasz sobie, jak wygląda zapisany",
        "powtarzasz go kilka razy na głos",
        "zapamiętujesz ruch palców przy wpisywaniu",
    ),
    (
        "Gdy masz chwilę wolnego, najchętniej…",
        "oglądasz film, zdjęcia albo czytasz",
        "słuchasz muzyki lub podcastu albo rozmawiasz",
        "uprawiasz sport, majsterkujesz albo gotujesz",
    ),
    (
        "Jak sprawdzasz, czy wyraz jest poprawnie napisany?",
        "Patrzę, czy „dobrze wygląda”",
        "Wymawiam go po cichu i słucham, jak brzmi",
        "Zapisuję go i czuję, czy ręka „pisze dobrze”",
    ),
    (
        "W jaki sposób najłatwiej rozwiązujesz trudny problem?",
        "Rozrysowuję go na kartce",
        "Omawiam go z kimś albo mówię do siebie",
        "Testuję różne rozwiązania w praktyce",
    ),
    (
        "Która forma kursu online przekonałaby Cię najbardziej?",
        "Filmy, animacje i infografiki",
        "Nagrania audio i omówienia lektora",
        "Interaktywne ćwiczenia i symulacje",
    ),
    (
        "Uczysz się obsługi nowego programu. Wolisz…",
        "zrzuty ekranu i film instruktażowy",
        "żeby ktoś opowiedział Ci krok po kroku, co robić",
        "klikać samodzielnie i sprawdzać, co się stanie",
    ),
    (
        "Co najlepiej pamiętasz z ostatniej wycieczki?",
        "Widoki i to, jak wyglądały odwiedzone miejsca",
        "Rozmowy, dźwięki i opowieści przewodnika",
        "To, co robiłem: wędrówkę, zwiedzanie, atrakcje",
    ),
    (
        "Kiedy ktoś tłumaczy Ci coś zbyt długo…",
        "prosisz, żeby to narysował albo pokazał",
        "prosisz, żeby powiedział to inaczej, prostszymi słowami",
        "prosisz, żeby dał Ci spróbować samemu",
    ),
    (
        "Przepis kulinarny najchętniej poznajesz…",
        "ze zdjęć lub filmu pokazującego kolejne etapy",
        "słuchając, jak ktoś go opowiada",
        "gotując od razu i ucząc się w trakcie",
    ),
    (
        "Jak najłatwiej uczysz się słówek z języka obcego?",
        "Z fiszek, obrazków i zapisanych list",
        "Słuchając nagrań i powtarzając na głos",
        "Używając ich w rozmowie, grach i scenkach",
    ),
    (
        "Po czym poznajesz, że dobrze coś rozumiesz?",
        "Potrafię to sobie wyobrazić lub narysować",
        "Potrafię to komuś wytłumaczyć własnymi słowami",
        "Potrafię to samodzielnie wykonać",
    ),
    (
        "W jakim miejscu uczy Ci się najlepiej?",
        "W uporządkowanym, z notatkami i kolorowymi materiałami pod ręką",
        "W cichym albo z ulubioną muzyką w tle",
        "W takim, gdzie mogę wstać, chodzić i coś robić",
    ),
]


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "survey_questions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("text", sa.String(length=300), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_survey_questions")),
    )
    op.create_table(
        "learning_profiles",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("style", sa.String(length=3), nullable=False),
        sa.Column("style_source", sa.String(length=12), nullable=False),
        sa.Column("weight_v", sa.Integer(), nullable=False),
        sa.Column("weight_a", sa.Integer(), nullable=False),
        sa.Column("weight_k", sa.Integer(), nullable=False),
        sa.Column("rejected_proposal", sa.String(length=1), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "style_source IN ('survey', 'manual', 'adaptation')",
            name=op.f("ck_learning_profiles_style_source"),
        ),
        sa.CheckConstraint(
            "weight_v BETWEEN 0 AND 30 AND weight_a BETWEEN 0 AND 30 AND weight_k BETWEEN 0 AND 30",
            name=op.f("ck_learning_profiles_weights"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_learning_profiles_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("user_id", name=op.f("pk_learning_profiles")),
    )
    op.create_table(
        "survey_answers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("text", sa.String(length=300), nullable=False),
        sa.Column("style", sa.String(length=1), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.CheckConstraint("style IN ('V', 'A', 'K')", name=op.f("ck_survey_answers_style")),
        sa.ForeignKeyConstraint(
            ["question_id"],
            ["survey_questions.id"],
            name=op.f("fk_survey_answers_question_id_survey_questions"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_survey_answers")),
    )
    op.create_index(
        op.f("ix_survey_answers_question_id"), "survey_answers", ["question_id"], unique=False
    )
    op.create_table(
        "survey_results",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("points_v", sa.Integer(), nullable=False),
        sa.Column("points_a", sa.Integer(), nullable=False),
        sa.Column("points_k", sa.Integer(), nullable=False),
        sa.Column("dominant_style", sa.String(length=3), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_survey_results_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_survey_results")),
    )
    op.create_index(op.f("ix_survey_results_user_id"), "survey_results", ["user_id"], unique=False)
    op.create_table(
        "quiz_attempts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("lesson_id", sa.Integer(), nullable=False),
        sa.Column("block_id", sa.String(length=40), nullable=False),
        sa.Column("percent", sa.Integer(), nullable=False),
        sa.Column("style", sa.String(length=3), nullable=False),
        sa.Column("counted_for_weights", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("percent BETWEEN 0 AND 100", name=op.f("ck_quiz_attempts_percent")),
        sa.ForeignKeyConstraint(
            ["lesson_id"],
            ["lessons.id"],
            name=op.f("fk_quiz_attempts_lesson_id_lessons"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_quiz_attempts_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_quiz_attempts")),
    )
    op.create_index(
        "ix_quiz_attempts_user_id_lesson_id",
        "quiz_attempts",
        ["user_id", "lesson_id"],
        unique=False,
    )
    # ### end Alembic commands ###

    _insert_vak_questions()


def _insert_vak_questions() -> None:
    questions = sa.table(
        "survey_questions",
        sa.column("id", sa.Integer),
        sa.column("text", sa.String),
        sa.column("position", sa.Integer),
        sa.column("is_active", sa.Boolean),
    )
    answers = sa.table(
        "survey_answers",
        sa.column("question_id", sa.Integer),
        sa.column("text", sa.String),
        sa.column("style", sa.String),
        sa.column("position", sa.Integer),
    )
    conn = op.get_bind()
    for position, (text, *answer_texts) in enumerate(VAK_QUESTIONS):
        question_id = conn.execute(
            questions.insert()
            .values(text=text, position=position, is_active=True)
            .returning(questions.c.id)
        ).scalar_one()
        op.bulk_insert(
            answers,
            [
                {"question_id": question_id, "text": answer, "style": style, "position": index}
                for index, (style, answer) in enumerate(zip("VAK", answer_texts, strict=True))
            ],
        )


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index("ix_quiz_attempts_user_id_lesson_id", table_name="quiz_attempts")
    op.drop_table("quiz_attempts")
    op.drop_index(op.f("ix_survey_results_user_id"), table_name="survey_results")
    op.drop_table("survey_results")
    op.drop_index(op.f("ix_survey_answers_question_id"), table_name="survey_answers")
    op.drop_table("survey_answers")
    op.drop_table("learning_profiles")
    op.drop_table("survey_questions")
    # ### end Alembic commands ###
