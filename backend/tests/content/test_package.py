from pathlib import Path

import pytest

from app.modules.content.models import LessonMethod
from app.modules.content.package import PackageError, load_package
from tests.content.builders import lesson, number_question, write_package


def errors_of(path: Path) -> list[str]:
    with pytest.raises(PackageError) as error:
        load_package(path)
    return error.value.errors


def test_valid_package(tmp_path: Path):
    lessons = [lesson("base"), lesson("base", "beta"), lesson("advanced")]
    package = load_package(write_package(tmp_path, lessons=lessons))
    assert package.course.key == "test-course"
    assert [(item.skill, item.method) for item in package.lessons] == [
        ("advanced", LessonMethod.COMMON),
        ("base", LessonMethod.BETA),
        ("base", LessonMethod.COMMON),
    ]


def test_numbers_may_be_written_without_quotes(tmp_path: Path):
    text = """\
skill: base
method: common
title: Lekcja
steps:
  - key: q
    type: question
    prompt: Ile?
    answer:
      type: number
      value: 30
      feedback:
        - when: 90
          message: To cena po rabacie.
    explanation: Bo tak.
"""
    path = write_package(
        tmp_path, lessons=[lesson("advanced")], files={"lessons/base.common.yaml": text}
    )
    answer = (
        next(item for item in load_package(path).lessons if item.skill == "base").steps[0].answer
    )
    assert (answer.value, answer.feedback[0].when) == ("30", "90")


def test_decimal_without_quotes_is_rejected(tmp_path: Path):
    bad = lesson("base", steps=[number_question(value=0.25)])
    [message] = errors_of(write_package(tmp_path, lessons=[bad, lesson("advanced")]))
    assert message.startswith("lessons/base.common.yaml: steps.0.question.answer.number.value")
    assert "quotes" in message


def test_missing_course_file(tmp_path: Path):
    assert errors_of(write_package(tmp_path, course=None)) == ["course.yaml: file not found"]


def test_invalid_yaml(tmp_path: Path):
    path = write_package(tmp_path, files={"lessons/base.common.yaml": "title: [unclosed"})
    [message] = errors_of(path)
    assert message.startswith("lessons/base.common.yaml: invalid YAML")


def test_top_level_must_be_a_mapping(tmp_path: Path):
    path = write_package(tmp_path, files={"course.yaml": "- just\n- a list\n"})
    assert errors_of(path) == ["course.yaml: expected key: value pairs at the top level"]


def test_lesson_for_unknown_skill(tmp_path: Path):
    lessons = [lesson("base"), lesson("advanced"), lesson("ghost")]
    assert errors_of(write_package(tmp_path, lessons=lessons)) == [
        "lessons/ghost.common.yaml: unknown skill ghost"
    ]


def test_every_skill_needs_a_common_lesson(tmp_path: Path):
    lessons = [lesson("base"), lesson("advanced", "beta")]
    assert errors_of(write_package(tmp_path, lessons=lessons)) == [
        "course.yaml: skill advanced has no lesson lessons/advanced.common.yaml"
    ]


def test_file_name_must_match_content(tmp_path: Path):
    path = write_package(tmp_path, lessons=[lesson("advanced")])
    (path / "lessons" / "base.common.yaml").write_text(
        (path / "lessons" / "advanced.common.yaml").read_text(encoding="utf-8"), encoding="utf-8"
    )
    assert errors_of(path) == [
        "lessons/base.common.yaml: file name must match its content: advanced.common.yaml"
    ]


def test_errors_from_all_files_are_reported(tmp_path: Path):
    lessons = [lesson("base", title=""), lesson("advanced", steps=[])]
    messages = errors_of(write_package(tmp_path, lessons=lessons))
    assert any(m.startswith("lessons/advanced.common.yaml: steps") for m in messages)
    assert any(m.startswith("lessons/base.common.yaml: title") for m in messages)
