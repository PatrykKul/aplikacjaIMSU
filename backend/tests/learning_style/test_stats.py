"""Statistics aggregates (pure functions)."""

from datetime import UTC, datetime

from app.modules.learning_style.rules import FORMS, CourseResult, Result, is_passed
from app.modules.learning_style.stats import (
    Attempt,
    FormEffect,
    FormGap,
    FormMean,
    FormTableRow,
    LessonInfo,
    LessonRef,
    LessonResult,
    LessonStatsRow,
    MatrixCell,
    MatrixRow,
    StudentSummary,
    counted_average,
    form_effectiveness,
    form_gaps,
    form_table,
    hardest_lesson,
    lesson_form_matrix,
    lesson_results,
    lesson_stats,
    mean_tenths,
    student_summary,
    style_distribution,
)


def test_form_effectiveness():
    results = [
        CourseResult(1, "A", 80, True),
        CourseResult(1, "A", 100, False),
        CourseResult(2, "A", 61, True),
        CourseResult(3, "V", 40, True),
    ]
    effects = form_effectiveness(results)
    assert effects["A"] == FormEffect(average=71, counted_results=2, attempts=3, students=2)
    assert effects["V"] == FormEffect(average=40, counted_results=1, attempts=1, students=1)
    assert effects["K"] == FormEffect(average=None, counted_results=0, attempts=0, students=0)


def test_style_distribution_counts_missing_styles_as_none():
    assert style_distribution(["V", "A", "A", None]) == {"V": 1, "A": 2, "K": 0, "none": 1}
    assert style_distribution([]) == {"V": 0, "A": 0, "K": 0, "none": 0}


def test_counted_average_ignores_retries():
    results = [CourseResult(1, "V", 40, True), CourseResult(1, "V", 100, False)]
    assert counted_average(results) == 40
    assert counted_average([]) is None


def test_lesson_results_only_attempted_lessons_in_order():
    at = datetime(2026, 11, 12, tzinfo=UTC)
    lessons = [
        LessonInfo(1, "Matematyka", 10, "Lekcja 1", 1),
        LessonInfo(1, "Matematyka", 11, "Lekcja 2", 2),
        LessonInfo(1, "Matematyka", 12, "Lekcja 3", None),
    ]
    attempts = [
        Attempt(12, at, "A", 80, True, True),
        Attempt(10, at, "V", 40, False, True),
        Attempt(10, at, "V", 80, True, False),
    ]
    rows = lesson_results(lessons, attempts, passed_ids={10})
    assert [(row["lesson_id"], row["passed"], row["number"]) for row in rows] == [
        (10, True, 1),
        (12, False, None),
    ]
    assert rows[0]["attempts"] == [
        {"at": at, "form": "V", "percent": 40, "passed": False, "counted": True},
        {"at": at, "form": "V", "percent": 80, "passed": True, "counted": False},
    ]
    assert rows[0]["course_title"] == "Matematyka"


# --- Rounding helpers ----------------------------------------------------------------------------


def test_mean_tenths_one_decimal_half_up():
    assert mean_tenths([1, 2]) == 1.5
    assert mean_tenths([1, 1, 2]) == 1.3  # 1.333
    assert mean_tenths([1, 2, 2]) == 1.7  # 1.667
    assert mean_tenths([1] * 19 + [2]) == 1.1  # 1.05 -> 1.1
    assert mean_tenths([3]) == 3.0
    assert mean_tenths([]) is None


# --- Student summary -----------------------------------------------------------------------------


def res(lesson_id: int, form: str, percent: int, counted: bool = True) -> Result:
    return Result(lesson_id, f"Lekcja {lesson_id}", form, percent, is_passed(percent), counted)


def test_student_summary():
    results = [
        res(1, "V", 40),
        res(1, "V", 80, counted=False),
        res(2, "V", 80),
        res(3, "A", 100),
        res(3, "A", 20, counted=False),  # a failed retry does not break the streak
    ]
    assert student_summary(results) == StudentSummary(attempts=5, average=73, counted=3, streak=2)


def test_student_summary_streak_stops_at_a_counted_failure():
    results = [res(1, "V", 80), res(2, "V", 80), res(3, "V", 40)]
    assert student_summary(results).streak == 0
    assert student_summary(results[:2]).streak == 2


def test_student_summary_without_results():
    assert student_summary([]) == StudentSummary(attempts=0, average=None, counted=0, streak=0)


# --- Form table ----------------------------------------------------------------------------------


def test_form_table():
    results = [
        res(1, "V", 40),
        res(1, "V", 60, counted=False),
        res(1, "A", 80),
        res(2, "A", 60),
        res(2, "V", 100),
        res(3, "A", 100),
        res(3, "A", 40, counted=False),
    ]
    table = form_table(results, {"V": 30, "A": 60, "K": 10})
    assert table["V"] == FormTableRow(
        lessons=2,
        attempts=3,
        passed_lessons=1,
        first_try_lessons=2,
        first_try_passed=1,
        first_try_rate=50,
        average=70,
        best=100,
        confirmed=True,
        percent=30,
    )
    assert table["A"] == FormTableRow(
        lessons=3,
        attempts=4,
        passed_lessons=2,
        first_try_lessons=3,
        first_try_passed=2,
        first_try_rate=67,
        average=80,
        best=100,
        confirmed=True,
        percent=60,
    )
    assert table["K"] == FormTableRow(
        lessons=0,
        attempts=0,
        passed_lessons=0,
        first_try_lessons=0,
        first_try_passed=0,
        first_try_rate=None,
        average=None,
        best=None,
        confirmed=False,
        percent=10,
    )


def test_form_table_first_try_rate_needs_two_lessons():
    table = form_table([res(1, "V", 80)], None)
    assert (table["V"].first_try_lessons, table["V"].first_try_rate) == (1, None)
    assert table["V"].percent is None  # without a profile
    table = form_table([res(1, "V", 80), res(2, "V", 40)], None)
    assert table["V"].first_try_rate == 50


def test_form_table_confirmed_by_a_not_counted_pass():
    row = form_table([res(1, "K", 40), res(1, "K", 80, counted=False)], None)["K"]
    assert (row.confirmed, row.passed_lessons, row.first_try_passed) == (True, 1, 0)
    assert (row.average, row.best) == (40, 80)


# --- Course: lesson statistics and the hardest lesson --------------------------------------------

L1 = LessonRef(10, "Lekcja 1", 1)
L2 = LessonRef(11, "Lekcja 2", 2)
L3 = LessonRef(12, "Lekcja 3", 3)


def lr(student: int, lesson: int, form: str, percent: int, counted: bool = True) -> LessonResult:
    return LessonResult(student, lesson, form, percent, is_passed(percent), counted)


def test_lesson_stats():
    results = [
        lr(1, 10, "V", 40),
        lr(1, 10, "V", 60, counted=False),
        lr(1, 10, "A", 80),  # passed in the 3rd attempt
        lr(2, 10, "V", 80),  # passed in the 1st attempt
        lr(3, 10, "A", 20),  # not passed
        lr(1, 11, "V", 100),
    ]
    rows = lesson_stats([L1, L2, L3], results)
    assert rows[0] == LessonStatsRow(
        lesson_id=10,
        title="Lekcja 1",
        number=1,
        started=3,
        passed=2,
        pass_rate=67,
        first_average=55,  # 40, 80, 80, 20
        first_results=4,
        attempts_to_pass=2.0,  # (3 + 1) / 2
    )
    # one student only: the shares are hidden, the counts stay
    assert rows[1] == LessonStatsRow(11, "Lekcja 2", 2, 1, 1, None, None, 1, 1.0)
    # no attempts at all
    assert rows[2] == LessonStatsRow(12, "Lekcja 3", 3, 0, 0, None, None, 0, None)


def test_lesson_stats_threshold_of_three_students():
    two = [lr(1, 10, "V", 80), lr(2, 10, "V", 40)]
    row = lesson_stats([L1], two)[0]
    assert (row.started, row.pass_rate, row.first_average) == (2, None, None)
    row = lesson_stats([L1], [*two, lr(3, 10, "V", 100)])[0]
    assert (row.started, row.pass_rate, row.first_average) == (3, 67, 73)


def test_attempts_to_pass_one_decimal():
    results = [
        lr(1, 10, "V", 80),
        lr(2, 10, "V", 40),
        lr(2, 10, "V", 80, counted=False),
        lr(3, 10, "V", 40),
        lr(3, 10, "A", 80),
        lr(3, 10, "A", 100, counted=False),  # after the first pass: not counted in
    ]
    assert lesson_stats([L1], results)[0].attempts_to_pass == 1.7  # (1 + 2 + 2) / 3


def row_of(lesson: LessonRef, pass_rate: int | None, first_average: int | None) -> LessonStatsRow:
    return LessonStatsRow(
        lesson.lesson_id, lesson.title, lesson.number, 3, 0, pass_rate, first_average, 3, None
    )


def test_hardest_lesson_lowest_pass_rate():
    rows = [row_of(L1, 67, 60), row_of(L2, 33, 70), row_of(L3, 100, 90)]
    assert hardest_lesson(rows) == rows[1]


def test_hardest_lesson_ties():
    # equal pass rate: the lower first average, then the earlier lesson
    rows = [row_of(L1, 33, 60), row_of(L2, 33, 50), row_of(L3, 33, 50)]
    assert hardest_lesson(rows) == rows[1]
    rows = [row_of(L1, 50, 60), row_of(L2, 50, 60)]
    assert hardest_lesson(rows) == rows[0]


def test_no_hardest_lesson():
    # no lesson with enough students, or every such lesson passed by everyone
    assert hardest_lesson([row_of(L1, None, None), row_of(L2, None, None)]) is None
    rows = [row_of(L1, 100, 90), row_of(L2, 100, 80), row_of(L3, None, None)]
    assert hardest_lesson(rows) is None
    assert hardest_lesson([]) is None


# --- Course: lesson x form matrix and form gaps --------------------------------------------------


def test_lesson_form_matrix():
    results = [
        lr(1, 10, "V", 80),
        lr(2, 10, "V", 100),
        lr(2, 10, "V", 40, counted=False),  # retries do not count
        lr(3, 10, "A", 40),
        lr(4, 11, "K", 60),
        lr(5, 11, "K", 60),
    ]
    matrix = lesson_form_matrix([L1, L2], results)
    assert matrix[0] == MatrixRow(
        10,
        "Lekcja 1",
        1,
        {"V": MatrixCell(90, 2), "A": MatrixCell(None, 1), "K": MatrixCell(None, 0)},
    )
    assert matrix[1].cells == {
        "V": MatrixCell(None, 0),
        "A": MatrixCell(None, 0),
        "K": MatrixCell(60, 2),
    }


def matrix_row(lesson: LessonRef, **cells: tuple[int | None, int]) -> MatrixRow:
    all_cells = {form: MatrixCell(*cells.get(form, (None, 0))) for form in FORMS}
    return MatrixRow(lesson.lesson_id, lesson.title, lesson.number, all_cells)


def test_form_gaps_from_twenty_points():
    matrix = [
        matrix_row(L1, V=(90, 3), A=(70, 2), K=(None, 1)),  # 20: a gap
        matrix_row(L2, V=(90, 3), A=(71, 2)),  # 19: none
        matrix_row(L3, V=(50, 2), A=(80, 2), K=(55, 4)),
    ]
    assert form_gaps(matrix) == [
        FormGap(10, "Lekcja 1", 1, FormMean("V", 90, 3), FormMean("A", 70, 2)),
        FormGap(12, "Lekcja 3", 3, FormMean("A", 80, 2), FormMean("V", 50, 2)),
    ]


def test_form_gaps_need_two_forms_with_enough_results():
    # K has no average (1 result): not compared
    assert form_gaps([matrix_row(L1, V=(40, 2), K=(None, 1))]) == []
    assert form_gaps([]) == []


def test_form_gaps_ties_go_in_v_a_k_order():
    gap = form_gaps([matrix_row(L1, V=(90, 2), A=(60, 2), K=(90, 2))])[0]
    assert (gap.best.form, gap.worst.form) == ("V", "A")
    gap = form_gaps([matrix_row(L1, V=(90, 2), A=(60, 2), K=(60, 2))])[0]
    assert (gap.best.form, gap.worst.form) == ("V", "A")
