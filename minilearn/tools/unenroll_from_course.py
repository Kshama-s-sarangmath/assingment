from __future__ import annotations

from typing import Any

from strands import tool

from minilearn.config.settings import get_settings
from minilearn.utils.catalog import CatalogDataError, course_to_summary, get_course_by_id, load_catalog
from minilearn.utils.store import EnrollmentStoreError, unenroll_course


@tool
def unenroll_from_course(learning_id: str) -> dict[str, Any]:
    """Remove the learner from an enrolled published catalog item using its exact learning ID.

    Use this tool when the learner asks to drop, unenroll, remove, or leave a specific course.
    Resolve ambiguous references into an exact `learning_id` before calling the tool.

    Args:
        learning_id: Exact learning ID to remove from the learner's enrollments.

    Returns:
        A JSON object with unenrolled, not_enrolled, not_found, or error status.
    """

    settings = get_settings()
    try:
        catalog = load_catalog(settings.catalog_path)
        course = get_course_by_id(catalog, learning_id)
        if course is None:
            return {
                "status": "not_found",
                "message": f"No published learning item was found for {learning_id}.",
            }
        changed = unenroll_course(settings.enrollments_path, learning_id)
    except (CatalogDataError, EnrollmentStoreError) as exc:
        return {"status": "error", "message": str(exc)}

    if not changed:
        return {
            "status": "not_enrolled",
            "message": f"You were not enrolled in {course.title}.",
            "course": course_to_summary(course),
        }
    return {
        "status": "unenrolled",
        "message": f"You have been unenrolled from {course.title}.",
        "course": course_to_summary(course),
    }
