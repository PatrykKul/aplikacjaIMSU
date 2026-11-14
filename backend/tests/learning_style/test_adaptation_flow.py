"""`record_quiz_result` through the quiz API: R2-R7 and the decision log.

The paths of Kuba and Marta are the contract for the demo data (docs/08, "Dane demo").
"""

from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.learning_style.models import DecisionEvent, StyleTrial
from tests.learning_style.conftest import (
    journal_types,
    last_event,
    set_form,
    survey_styles,
    take_quiz,
)

KUBA = survey_styles(9, 8, 3)  # V 45 / A 40 / K 15, style V
MARTA = survey_styles(7, 3, 10)  # K 50 / V 35 / A 15, style K


def pct(v: int, a: int, k: int) -> dict[str, int]:
    return {"V": v, "A": a, "K": k}


def lesson_ids(course: dict[str, Any]) -> list[int]:
    return [lesson["id"] for lesson in course["lessons"]]


def profile(client: TestClient) -> dict[str, Any]:
    return client.get("/profile/learning-style").json()


def kuba_until_proposal(client: TestClient, course: dict[str, Any]) -> dict[str, Any]:
    """Kuba's path from the demo data up to the proposal to switch to A."""
    l1, l2, l3 = lesson_ids(course)[:3]
    take_quiz(client, l1, 80)
    take_quiz(client, l2, 40)
    take_quiz(client, l2, 80)
    take_quiz(client, l3, 40)
    set_form(client, l3, "A")
    return take_quiz(client, l3, 80)


# --- Counting and percentages (R2) ---------------------------------------------------------------


def test_only_the_first_attempt_in_a_form_changes_the_percentages(
    client: TestClient, course, learner
):
    learner(course["id"], KUBA)
    l1 = lesson_ids(course)[0]
    first = take_quiz(client, l1, 40)["feedback"]
    assert (first["form"], first["counted"], first["passed"]) == ("V", True, False)
    assert first["percentages_before"] == pct(45, 40, 15)
    assert first["percentages_after"] == pct(35, 47, 18)
    second = take_quiz(client, l1, 80)["feedback"]
    assert (second["counted"], second["passed"]) == (False, True)
    assert second["percentages_before"] == second["percentages_after"] == pct(35, 47, 18)
    assert profile(client)["percentages"] == pct(35, 47, 18)
    # history: survey + one counted result
    assert len(client.get("/me/progress").json()["history"]) == 2


def test_form_comes_from_the_lesson_choice(client: TestClient, course, learner):
    learner(course["id"], KUBA)
    l1 = lesson_ids(course)[0]
    take_quiz(client, l1, 40)  # V, counted
    set_form(client, l1, "A")
    feedback = take_quiz(client, l1, 80)["feedback"]
    assert (feedback["form"], feedback["counted"]) == ("A", True)  # first attempt in A
    assert feedback["percentages_after"] == pct(28, 57, 15)
    set_form(client, l1, "V", "manual")
    assert take_quiz(client, l1, 100)["feedback"]["counted"] is False  # V again


def test_quiz_attempt_event_with_data(client: TestClient, course, learner):
    learner(course["id"], KUBA)
    l1, l2 = lesson_ids(course)[:2]
    draw_id = take_quiz(client, l1, 80)["draw_id"]
    event = last_event(client, "quiz_attempt")
    assert event["course"] == {"id": course["id"], "title": "Matematyka"}
    assert event["lesson"] == {"id": l1, "title": "Lekcja 1", "number": 1}
    assert event["data"] == {
        "draw_id": draw_id,
        "form": "V",
        "percent": 80,
        "passed": True,
        "counted": True,
        "percentages_before": pct(45, 40, 15),
        "percentages_after": pct(55, 33, 12),
        "unlocked_lesson": {"id": l2, "title": "Lekcja 2", "number": 2},
    }


# --- Passing: unlocking, praise, course completion (R4) ------------------------------------------


def test_pass_unlocks_next_lesson_and_completes_the_course(
    client: TestClient, quiz_course, learner
):
    course = quiz_course(lessons=("L1", "L2"))
    learner(course["id"], "V")
    l1, l2 = lesson_ids(course)
    first = take_quiz(client, l1, 80)["feedback"]
    assert first["unlocked_lesson"] == {"id": l2, "title": "L2", "number": 2}
    assert first["course_completed"] is False
    assert first["praise"] is None  # one pass only
    second = take_quiz(client, l2, 100)["feedback"]
    assert second["unlocked_lesson"] is None
    assert second["course_completed"] is True
    assert second["praise"] == {"form": "V", "streak": 2, "average": 90}
    again = take_quiz(client, l2, 100)["feedback"]
    assert again["course_completed"] is False  # already completed before
    assert again["praise"] is None  # not counted


# --- Failure: suggestion (R5) --------------------------------------------------------------------


def test_failure_suggests_the_second_survey_form(client: TestClient, course, learner):
    learner(course["id"], KUBA)
    l1, l2 = lesson_ids(course)[:2]
    take_quiz(client, l1, 80)
    feedback = take_quiz(client, l2, 40)["feedback"]
    expected = {
        "failed": {
            "form": "V",
            "percent": 40,
            "previous": {"lesson_id": l1, "lesson_title": "Lekcja 1", "percent": 80},
        },
        "suggested": {
            "form": "A",
            "reason": "survey",
            "percent": 40,
            "survey_percent": 40,
            "best": None,
        },
        "strength": "soft",  # lesson 1 in V was passed
    }
    assert feedback["suggestion"] == expected
    assert feedback["proposal"] is None
    event = last_event(client, "retry_suggestion")
    assert event["data"] == expected
    assert event["lesson"]["id"] == l2


def test_suggestion_of_a_confirmed_form(client: TestClient, course, learner):
    learner(course["id"], KUBA)
    l1, l2 = lesson_ids(course)[:2]
    set_form(client, l1, "K", "manual")
    take_quiz(client, l1, 100)  # K confirmed
    suggestion = take_quiz(client, l2, 20)["feedback"]["suggestion"]
    assert suggestion["suggested"]["form"] == "K"
    assert suggestion["suggested"]["reason"] == "confirmed"
    assert suggestion["suggested"]["best"] == {
        "lesson_id": l1,
        "lesson_title": "Lekcja 1",
        "percent": 100,
    }
    assert suggestion["failed"]["previous"] is None  # no earlier V result


# --- Proposal to switch (R6): Kuba ---------------------------------------------------------------


def test_kuba_path_to_the_proposal_and_trial(client: TestClient, course, learner):
    learner(course["id"], KUBA)
    l1, l2, l3, l4 = lesson_ids(course)
    assert take_quiz(client, l1, 80)["feedback"]["percentages_after"] == pct(55, 33, 12)
    second = take_quiz(client, l2, 40)["feedback"]
    assert second["percentages_after"] == pct(45, 40, 15)
    assert second["suggestion"]["suggested"]["form"] == "A"  # ignored by Kuba
    retry = take_quiz(client, l2, 80)["feedback"]
    assert (retry["counted"], retry["percentages_after"]) == (False, pct(45, 40, 15))
    assert retry["unlocked_lesson"]["id"] == l3
    # "just before the suggestion": lesson 3 in V fails
    third = take_quiz(client, l3, 40)["feedback"]
    assert third["percentages_after"] == pct(35, 47, 18)
    assert third["suggestion"] == {
        "failed": {
            "form": "V",
            "percent": 40,
            "previous": {"lesson_id": l2, "lesson_title": "Lekcja 2", "percent": 40},
        },
        "suggested": {
            "form": "A",
            "reason": "survey",
            "percent": 47,
            "survey_percent": 40,
            "best": None,
        },
        "strength": "strong",  # the counted V result of lesson 2 failed too
    }
    study = set_form(client, l3, "A")
    assert (study["form"], study["form_source"]) == ("A", "choice")
    assert last_event(client, "lesson_form_changed")["data"] == {
        "from": "V",
        "to": "A",
        "source": "suggestion",
    }
    # lesson 3 in A passes: proposal with evidence from the results
    fourth = take_quiz(client, l3, 80)["feedback"]
    assert (fourth["form"], fourth["counted"]) == ("A", True)
    assert fourth["percentages_after"] == pct(28, 57, 15)
    assert fourth["unlocked_lesson"]["id"] == l4
    proposal = fourth["proposal"]
    assert (proposal["kind"], proposal["from"], proposal["to"]) == ("switch", "V", "A")
    assert proposal["evidence"] == {
        "from": {"form": "V", "lessons": 3, "average": 53, "percent": 28},
        "to": {"form": "A", "lessons": 1, "average": 80, "percent": 57},
    }
    created = last_event(client, "proposal_created")["data"]
    assert created["proposal_id"] == proposal["id"]
    assert created["evidence"] == proposal["evidence"]
    current = profile(client)
    assert current["open_proposal"]["id"] == proposal["id"]
    assert current["forms"]["A"] == {"confirmed": True, "lessons": 1, "average": 80}
    assert current["forms"]["V"] == {"confirmed": True, "lessons": 3, "average": 53}
    # accepted: style A, trial against the last two V results (40, 40)
    accepted = client.post(f"/profile/learning-style/proposals/{proposal['id']}/accept").json()
    assert (accepted["style"], accepted["style_source"]) == ("A", "proposal")
    assert accepted["percentages"] == pct(28, 57, 15)
    assert accepted["open_proposal"] is None
    trial = accepted["trial"]
    assert (trial["from"], trial["to"], trial["source"]) == ("V", "A", "proposal")
    assert (trial["before_average"], trial["done"], trial["needed"]) == (40, 0, 2)
    assert trial["result"] is None and trial["finished_at"] is None
    assert last_event(client, "proposal_accepted")["data"] == {
        "proposal_id": proposal["id"],
        "kind": "switch",
        "from": "V",
        "to": "A",
        "cleared_lessons": [],  # lesson 3 is passed: its choice stays
    }
    assert last_event(client, "trial_started")["data"] == {
        "trial_id": trial["id"],
        "from": "V",
        "to": "A",
        "source": "proposal",
        "before_average": 40,
        "replaced_trial_id": None,
    }
    assert journal_types(client) == [
        "survey_completed",
        "quiz_attempt",
        "quiz_attempt",
        "retry_suggestion",
        "quiz_attempt",
        "quiz_attempt",
        "retry_suggestion",
        "lesson_form_changed",
        "quiz_attempt",
        "proposal_created",
        "proposal_accepted",
        "trial_started",
    ]
    assert client.get(f"/lessons/{l4}/study").json()["form"] == "A"


def test_no_proposal_for_an_unconfirmed_form(client: TestClient, course, learner):
    learner(course["id"], KUBA)
    l1, l2 = lesson_ids(course)[:2]
    take_quiz(client, l1, 40)  # V 35, A 47: A higher, but never passed
    assert take_quiz(client, l1, 80)["feedback"]["proposal"] is None
    assert take_quiz(client, l2, 40)["feedback"]["proposal"] is None


def test_rejected_proposal_returns_after_two_new_counted_results(
    client: TestClient, course, learner
):
    learner(course["id"], KUBA)
    l4 = lesson_ids(course)[3]
    proposal = kuba_until_proposal(client, course)["feedback"]["proposal"]
    rejected = client.post(f"/profile/learning-style/proposals/{proposal['id']}/reject").json()
    assert rejected["style"] == "V" and rejected["open_proposal"] is None
    assert last_event(client, "proposal_rejected")["data"] == {
        "proposal_id": proposal["id"],
        "kind": "switch",
        "from": "V",
        "to": "A",
    }
    first = take_quiz(client, l4, 80)["feedback"]  # 1 new counted result: V 38 / A 49
    assert first["percentages_after"] == pct(38, 49, 13)
    assert first["proposal"] is None
    set_form(client, l4, "K", "manual")
    second = take_quiz(client, l4, 40)["feedback"]  # 2 new counted results
    assert second["percentages_after"] == pct(41, 54, 5)
    assert second["proposal"]["to"] == "A"
    assert second["proposal"]["id"] != proposal["id"]
    # deciding twice is not possible
    again = client.post(f"/profile/learning-style/proposals/{proposal['id']}/accept")
    assert (again.status_code, again.json()) == (409, {"code": "PROPOSAL_NOT_OPEN"})


def test_open_proposal_expires_when_its_condition_ends(client: TestClient, quiz_course, learner):
    course = quiz_course(lessons=("Lekcja 1", "Lekcja 2", "Lekcja 3", "Lekcja 4", "Lekcja 5"))
    learner(course["id"], KUBA)
    l4, l5 = lesson_ids(course)[3:]
    proposal = kuba_until_proposal(client, course)["feedback"]["proposal"]
    same = take_quiz(client, l4, 100)["feedback"]  # V 38 / A 49: still the same proposal
    assert same["proposal"]["id"] == proposal["id"]
    gone = take_quiz(client, l5, 100)["feedback"]  # V 48 / A 41
    assert gone["percentages_after"] == pct(48, 41, 11)
    assert gone["proposal"] is None
    assert last_event(client, "proposal_expired")["data"]["proposal_id"] == proposal["id"]
    response = client.post(f"/profile/learning-style/proposals/{proposal['id']}/accept")
    assert response.json() == {"code": "PROPOSAL_NOT_OPEN"}


def test_proposal_of_another_student_is_not_found(client: TestClient, course, learner):
    learner(course["id"], KUBA)
    proposal = kuba_until_proposal(client, course)["feedback"]["proposal"]
    learner(course["id"], KUBA)
    response = client.post(f"/profile/learning-style/proposals/{proposal['id']}/accept")
    assert (response.status_code, response.json()) == (404, {"code": "PROPOSAL_NOT_FOUND"})
    assert client.post("/profile/learning-style/proposals/999999/reject").status_code == 404


# --- Trial period (R7): Marta and going back -----------------------------------------------------


def test_marta_trial_helped(client: TestClient, quiz_course, learner):
    course = quiz_course(title="Programowanie")
    learner(course["id"], MARTA)
    l1, l2, l3 = lesson_ids(course)[:3]
    assert profile(client)["percentages"] == pct(35, 15, 50)
    failed = take_quiz(client, l1, 40)["feedback"]
    assert failed["suggestion"]["suggested"]["form"] == "V"
    assert failed["suggestion"]["suggested"]["survey_percent"] == 35
    set_form(client, l1, "V")
    passed = take_quiz(client, l1, 80)["feedback"]
    assert passed["percentages_after"] == pct(52, 15, 33)
    proposal = passed["proposal"]
    assert (proposal["from"], proposal["to"]) == ("K", "V")
    assert proposal["evidence"] == {
        "from": {"form": "K", "lessons": 1, "average": 40, "percent": 33},
        "to": {"form": "V", "lessons": 1, "average": 80, "percent": 52},
    }
    trial = client.post(f"/profile/learning-style/proposals/{proposal['id']}/accept").json()[
        "trial"
    ]
    assert trial["before_average"] == 40
    second = take_quiz(client, l2, 100)["feedback"]
    assert (second["form"], second["trial"]["done"], second["trial"]["result"]) == ("V", 1, None)
    assert second["praise"] == {"form": "V", "streak": 2, "average": 90}
    third = take_quiz(client, l3, 80)["feedback"]
    assert third["trial"]["result"] == "helped"
    assert (third["trial"]["before_average"], third["trial"]["after_average"]) == (40, 90)
    assert third["trial"]["done"] == 2
    assert third["trial"]["finished_at"] is not None
    assert third["praise"] == {"form": "V", "streak": 3, "average": 87}
    praise_event = last_event(client, "praise")
    assert praise_event["data"] == {"form": "V", "streak": 3, "average": 87}
    assert praise_event["lesson"]["id"] == lesson_ids(course)[2]
    assert praise_event["course"]["id"] == course["id"]
    assert third["proposal"] is None
    assert last_event(client, "trial_finished")["data"] == {
        "trial_id": trial["id"],
        "from": "K",
        "to": "V",
        "before_average": 40,
        "after_average": 90,
        "result": "helped",
    }
    # the finished trial stays in the profile; the next attempt no longer reports it
    assert profile(client)["trial"]["result"] == "helped"
    assert take_quiz(client, l3, 100)["feedback"]["trial"] is None


def test_worse_trial_proposes_going_back_without_a_new_trial(client: TestClient, course, learner):
    learner(course["id"], "V")  # V 90 / A 5 / K 5
    l1, l2, l3, l4 = lesson_ids(course)
    take_quiz(client, l1, 100)
    take_quiz(client, l2, 100)
    changed = client.put("/profile/learning-style", json={"style": "A"}).json()
    assert changed["trial"]["before_average"] == 100
    take_quiz(client, l3, 80)
    feedback = take_quiz(client, l4, 80)["feedback"]
    assert (feedback["trial"]["result"], feedback["trial"]["after_average"]) == ("worse", 80)
    revert = feedback["proposal"]
    assert (revert["kind"], revert["from"], revert["to"]) == ("revert", "A", "V")
    assert revert["evidence"]["before_average"] == 100
    assert revert["evidence"]["after_average"] == 80
    accepted = client.post(f"/profile/learning-style/proposals/{revert['id']}/accept").json()
    assert (accepted["style"], accepted["style_source"]) == ("V", "proposal")
    assert accepted["trial"]["result"] == "worse"  # no new trial after going back
    assert journal_types(client)[-3:] == ["trial_finished", "proposal_created", "proposal_accepted"]


def test_trial_without_baseline(client: TestClient, course, learner):
    learner(course["id"], "V")
    l1, l2 = lesson_ids(course)[:2]
    changed = client.put("/profile/learning-style", json={"style": "K"}).json()
    assert changed["trial"]["before_average"] is None
    take_quiz(client, l1, 80)
    feedback = take_quiz(client, l2, 100)["feedback"]
    assert (feedback["trial"]["result"], feedback["trial"]["after_average"]) == ("no_baseline", 90)


def test_results_in_another_form_do_not_count_for_the_trial(client: TestClient, course, learner):
    learner(course["id"], "V")
    l1 = lesson_ids(course)[0]
    client.put("/profile/learning-style", json={"style": "A"})
    set_form(client, l1, "K", "manual")
    feedback = take_quiz(client, l1, 80)["feedback"]
    assert feedback["form"] == "K"
    assert feedback["trial"]["done"] == 0


# --- Manual style change -------------------------------------------------------------------------


def test_manual_change_supersedes_the_proposal_and_starts_a_trial(
    client: TestClient, course, learner
):
    learner(course["id"], KUBA)
    proposal = kuba_until_proposal(client, course)["feedback"]["proposal"]
    changed = client.put("/profile/learning-style", json={"style": "K"}).json()
    assert (changed["style"], changed["style_source"]) == ("K", "manual")
    assert changed["percentages"] == pct(28, 57, 15)  # percentages do not change
    assert changed["open_proposal"] is None
    assert (changed["trial"]["from"], changed["trial"]["to"]) == ("V", "K")
    assert changed["trial"]["source"] == "manual"
    assert changed["trial"]["before_average"] == 40
    assert last_event(client, "manual_style_change")["data"] == {
        "from": "V",
        "to": "K",
        "cleared_lessons": [],
        "superseded_proposal_id": proposal["id"],
    }
    response = client.post(f"/profile/learning-style/proposals/{proposal['id']}/accept")
    assert response.json() == {"code": "PROPOSAL_NOT_OPEN"}
    history = client.get("/me/progress").json()["history"]
    assert history[-1]["style"] == "K"


def test_manual_change_after_a_counted_lesson_starts_a_new_trial(
    client: TestClient, db: Session, course, learner
):
    learner(course["id"], "V")
    first = client.put("/profile/learning-style", json={"style": "A"}).json()["trial"]
    take_quiz(client, lesson_ids(course)[0], 80)  # counted in A: the change was tried
    second = client.put("/profile/learning-style", json={"style": "K"}).json()["trial"]
    assert second["id"] != first["id"]
    assert (second["from"], second["to"], second["finished_at"]) == ("A", "K", None)
    assert second["before_average"] == 80  # last results in A
    assert journal_types(client).count("trial_started") == 2
    assert last_event(client, "trial_started")["data"]["replaced_trial_id"] is None
    old = db.get(StyleTrial, first["id"])
    assert old is not None and old.finished_at is not None
    assert old.result is None  # interrupted without a result, as before R7a


# --- R7a: style change before the first lesson of a trial ----------------------------------------

STYLE_A = survey_styles(6, 10, 4)  # V 30 / A 50 / K 20, style A


def two_lessons_in_a(client: TestClient, course) -> None:
    l1, l2 = lesson_ids(course)[:2]
    take_quiz(client, l1, 100)
    take_quiz(client, l2, 100)


def trials(db: Session, user_id: int) -> list[StyleTrial]:
    query = select(StyleTrial).where(StyleTrial.user_id == user_id).order_by(StyleTrial.id)
    return list(db.scalars(query))


def test_going_back_before_a_lesson_undoes_the_change(
    client: TestClient, db: Session, course, learner
):
    # Patryk's path: A (2 lessons, 100%) -> V -> back to A without any lesson in V
    student = learner(course["id"], STYLE_A)
    two_lessons_in_a(client, course)
    to_v = client.put("/profile/learning-style", json={"style": "V"}).json()["trial"]
    assert (to_v["from"], to_v["to"], to_v["before_average"]) == ("A", "V", 100)

    back = client.put("/profile/learning-style", json={"style": "A"})

    assert back.status_code == 200
    body = back.json()
    assert (body["style"], body["style_source"]) == ("A", "manual")
    assert body["trial"] is None  # no "V -> A" trial and no message without a baseline
    [cancelled] = trials(db, student.id)
    assert (cancelled.id, cancelled.result) == (to_v["id"], "cancelled")
    assert cancelled.finished_at is not None
    assert journal_types(client)[-3:] == [
        "manual_style_change",
        "trial_started",
        "style_change_reverted",
    ]
    assert last_event(client, "style_change_reverted")["data"] == {
        "from": "V",
        "to": "A",
        "trial_id": to_v["id"],
        "source": "manual",
        "cleared_lessons": [],
    }
    history = client.get("/me/progress").json()["history"]
    assert [point["style"] for point in history[-2:]] == ["V", "A"]
    # The next lesson in A is a normal result, not a trial lesson
    feedback = take_quiz(client, lesson_ids(course)[2], 100)["feedback"]
    assert feedback["trial"] is None


def test_third_style_before_a_lesson_keeps_the_baseline(
    client: TestClient, db: Session, course, learner
):
    # A -> V -> K without any lesson in V: trial "A -> K" compared with the results in A
    student = learner(course["id"], STYLE_A)
    two_lessons_in_a(client, course)
    to_v = client.put("/profile/learning-style", json={"style": "V"}).json()["trial"]

    to_k = client.put("/profile/learning-style", json={"style": "K"}).json()

    trial = to_k["trial"]
    assert (trial["from"], trial["to"], trial["source"]) == ("A", "K", "manual")
    assert (trial["before_average"], trial["done"], trial["finished_at"]) == (100, 0, None)
    replaced, running = trials(db, student.id)
    assert (replaced.id, replaced.result) == (to_v["id"], "cancelled")
    assert running.id == trial["id"]
    assert last_event(client, "trial_started")["data"] == {
        "trial_id": trial["id"],
        "from": "A",
        "to": "K",
        "source": "manual",
        "before_average": 100,
        "replaced_trial_id": to_v["id"],
    }
    assert last_event(client, "manual_style_change")["data"]["from"] == "V"
    assert "style_change_reverted" not in journal_types(client)
    # Two lessons in K finish the trial against the baseline from A
    l3, l4 = lesson_ids(course)[2:4]
    take_quiz(client, l3, 100)
    finished = take_quiz(client, l4, 100)["feedback"]["trial"]
    assert (finished["before_average"], finished["after_average"]) == (100, 100)
    assert finished["result"] == "neutral"


def test_going_back_after_an_accepted_proposal(client: TestClient, db: Session, course, learner):
    # Kuba accepts V -> A and goes back to V before any lesson in A: undone as well
    student = learner(course["id"], KUBA)
    proposal = kuba_until_proposal(client, course)["feedback"]["proposal"]
    client.post(f"/profile/learning-style/proposals/{proposal['id']}/accept")

    back = client.put("/profile/learning-style", json={"style": "V"}).json()

    assert (back["style"], back["trial"]) == ("V", None)
    [trial] = trials(db, student.id)
    assert (trial.from_style, trial.to_style, trial.source, trial.result) == (
        "V",
        "A",
        "proposal",
        "cancelled",
    )
    data = last_event(client, "style_change_reverted")["data"]
    assert (data["from"], data["to"], data["source"]) == ("A", "V", "manual")


def test_manual_change_errors(client: TestClient, login, student, fill_survey):
    login(student)
    response = client.put("/profile/learning-style", json={"style": "V"})
    assert (response.status_code, response.json()) == (403, {"code": "SURVEY_REQUIRED"})
    fill_survey(student, "V")
    response = client.put("/profile/learning-style", json={"style": "V"})
    assert (response.status_code, response.json()) == (409, {"code": "SAME_STYLE"})
    assert client.put("/profile/learning-style", json={"style": "X"}).status_code == 422


# --- Clearing lesson form choices on a style change (R6) -----------------------------------------


def test_style_change_clears_choices_in_lessons_not_passed(client: TestClient, course, learner):
    learner(course["id"], "V")
    l1, l2 = lesson_ids(course)[:2]
    set_form(client, l1, "A")
    take_quiz(client, l1, 80)  # passed in A: the choice stays
    set_form(client, l2, "K", "manual")  # not passed: cleared
    changed = client.put("/profile/learning-style", json={"style": "A"})
    assert changed.status_code == 200
    assert last_event(client, "manual_style_change")["data"]["cleared_lessons"] == [
        {"lesson_id": l2, "lesson_title": "Lekcja 2", "form": "K"}
    ]
    assert client.get(f"/lessons/{l2}/study").json()["form_source"] == "style"
    assert client.get(f"/lessons/{l2}/study").json()["form"] == "A"
    # the choice in the passed lesson stays, but it equals the new style: "your style" (D57)
    kept = client.get(f"/lessons/{l1}/study").json()
    assert (kept["form"], kept["form_source"]) == ("A", "style")


def test_accepted_proposal_clears_choices(client: TestClient, course, learner):
    learner(course["id"], KUBA)
    l4 = lesson_ids(course)[3]
    proposal = kuba_until_proposal(client, course)["feedback"]["proposal"]
    set_form(client, l4, "K", "manual")
    client.post(f"/profile/learning-style/proposals/{proposal['id']}/accept")
    assert last_event(client, "proposal_accepted")["data"]["cleared_lessons"] == [
        {"lesson_id": l4, "lesson_title": "Lekcja 4", "form": "K"}
    ]
    study = client.get(f"/lessons/{l4}/study").json()
    assert (study["form"], study["form_source"]) == ("A", "style")


# --- Strength of the suggestion (R5) -------------------------------------------------------------


def test_suggestion_strength_in_feedback_event_and_study(client: TestClient, course, learner):
    learner(course["id"], KUBA)
    l1, l2 = lesson_ids(course)[:2]
    take_quiz(client, l1, 80)
    first = take_quiz(client, l2, 40)["feedback"]["suggestion"]
    assert first["strength"] == "soft"  # the previous counted V result passed
    assert last_event(client, "retry_suggestion")["data"]["strength"] == "soft"
    assert client.get(f"/lessons/{l2}/study").json()["suggestion"]["strength"] == "soft"
    # a not counted retry in V: the previous counted V result is lesson 2's 40%
    retry = take_quiz(client, l2, 60)["feedback"]
    assert (retry["counted"], retry["suggestion"]["strength"]) == (False, "strong")
    assert last_event(client, "retry_suggestion")["data"]["strength"] == "strong"


def test_suggestion_strength_without_a_previous_result_is_strong(
    client: TestClient, course, learner
):
    learner(course["id"], KUBA)
    feedback = take_quiz(client, lesson_ids(course)[0], 20)["feedback"]
    assert feedback["suggestion"]["strength"] == "strong"


def test_study_suggestion_of_an_old_event_reads_as_strong(
    client: TestClient, course, learner, db: Session
):
    learner(course["id"], KUBA)
    l1 = lesson_ids(course)[0]
    take_quiz(client, l1, 20)
    event = db.scalar(select(DecisionEvent).where(DecisionEvent.type == "retry_suggestion"))
    assert event is not None
    event.data = {key: value for key, value in event.data.items() if key != "strength"}
    db.commit()
    assert client.get(f"/lessons/{l1}/study").json()["suggestion"]["strength"] == "strong"


# --- A run of failures (R12) ---------------------------------------------------------------------


def attention_events(client: TestClient) -> list[dict[str, Any]]:
    return [
        entry for entry in client.get("/me/journal").json() if entry["type"] == "attention_needed"
    ]


def test_attention_after_three_counted_failures(client: TestClient, course, learner):
    learner(course["id"], KUBA)
    l1, l2 = lesson_ids(course)[:2]
    assert take_quiz(client, l1, 40)["feedback"]["attention"] is None
    set_form(client, l1, "A")
    assert take_quiz(client, l1, 20)["feedback"]["attention"] is None  # 2 failures
    assert attention_events(client) == []
    set_form(client, l1, "K")
    third = take_quiz(client, l1, 60)["feedback"]
    expected = {
        "streak": 3,
        "results": [
            {"lesson_id": l1, "lesson_title": "Lekcja 1", "form": "V", "percent": 40},
            {"lesson_id": l1, "lesson_title": "Lekcja 1", "form": "A", "percent": 20},
            {"lesson_id": l1, "lesson_title": "Lekcja 1", "form": "K", "percent": 60},
        ],
    }
    assert third["attention"] == expected
    (event,) = attention_events(client)
    assert event["data"] == expected
    assert (event["course"]["id"], event["lesson"]["id"]) == (course["id"], l1)

    # not counted attempts change nothing and log nothing more
    assert take_quiz(client, l1, 0)["feedback"]["attention"] == expected
    assert take_quiz(client, l1, 80)["feedback"]["attention"] == expected  # passed, not counted
    # a fourth counted failure: streak 4, no second event for the same run
    fourth = take_quiz(client, l2, 40)["feedback"]["attention"]
    assert fourth["streak"] == 4
    assert [item["percent"] for item in fourth["results"]] == [20, 60, 40]
    assert len(attention_events(client)) == 1
    # a counted pass ends the run
    set_form(client, l2, "A")
    assert take_quiz(client, l2, 80)["feedback"]["attention"] is None
    assert len(attention_events(client)) == 1
