import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.learning_style.models import SurveyAnswer, SurveyQuestion

# Masculine past forms ("Kupiłeś", "robiłem") and phrases that assume a man
GENDERED = re.compile(r"\w+łe[śm]\b|\bsamemu\b|\bz nim\b|żeby (?:mi )?\w+ł\b", re.IGNORECASE)


def _texts(db: Session) -> list[str]:
    questions = db.scalars(select(SurveyQuestion.text)).all()
    answers = db.scalars(select(SurveyAnswer.text)).all()
    return [*questions, *answers]


def test_survey_has_no_gendered_forms(db: Session):
    offending = [text for text in _texts(db) if GENDERED.search(text)]
    assert offending == []


def test_rewritten_texts_keep_their_styles(db: Session):
    question = db.scalar(select(SurveyQuestion).where(SurveyQuestion.position == 2))
    assert question.text == "Kupujesz nowe urządzenie. Co robisz najpierw?"
    styles = {answer.style: answer.text for answer in question.answers}
    assert styles["A"] == "Proszę kogoś o wyjaśnienie, jak to działa"
    last = db.scalar(select(SurveyQuestion).where(SurveyQuestion.position == 15))
    assert {a.style: a.text for a in last.answers} == {
        "V": "prosisz o rysunek albo pokazanie tego",
        "A": "prosisz o wyjaśnienie inaczej, prostszymi słowami",
        "K": "prosisz o możliwość samodzielnej próby",
    }


def test_survey_size_and_styles_unchanged(answer_key):
    assert len(answer_key) == 20
    assert all(set(by_style) == {"V", "A", "K"} for by_style in answer_key.values())
