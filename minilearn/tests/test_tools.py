from __future__ import annotations

from pathlib import Path

from minilearn.tools.enroll_in_course import enroll_in_course
from minilearn.tools.get_course_details import get_course_details
from minilearn.tools.get_my_enrollments import get_my_enrollments
from minilearn.tools.get_popular_courses import get_popular_courses
from minilearn.tools.search_courses import search_courses
from minilearn.tools.unenroll_from_course import unenroll_from_course


def test_search_tool_returns_ranked_payload() -> None:
    result = search_courses(query="machine learning", level="beginner")
    assert result["status"] == "success"
    assert result["results"]
    assert result["results"][0]["learningId"] == "LRN-00102"


def test_course_details_reports_unknown_id() -> None:
    result = get_course_details("LRN-99999")
    assert result["status"] == "not_found"


def test_enrollment_tools_round_trip(temp_data_dir: Path) -> None:
    enrolled = enroll_in_course("LRN-00102")
    assert enrolled["status"] == "enrolled"

    duplicate = enroll_in_course("LRN-00102")
    assert duplicate["status"] == "already_enrolled"

    listing = get_my_enrollments()
    assert listing["count"] == 1
    assert listing["results"][0]["learningId"] == "LRN-00102"

    removed = unenroll_from_course("LRN-00102")
    assert removed["status"] == "unenrolled"


def test_popular_tool_uses_published_results_only() -> None:
    result = get_popular_courses(learning_type="course")
    assert result["status"] == "success"
    assert result["results"]
    assert all(item["learningType"] == "course" for item in result["results"])
