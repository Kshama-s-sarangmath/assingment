from __future__ import annotations

from typing import Any

from strands import tool

from minilearn.config.settings import get_settings
from minilearn.utils.catalog import CatalogDataError, course_to_summary, get_course_by_id, load_catalog
from minilearn.utils.store import EnrollmentStoreError, enroll_course


@tool
def enroll_in_course(learning_id: str) -> dict[str, Any]:
    """Enroll the learner in a published catalog item using its exact learning ID.

    Use this tool only when the learner clearly wants to enroll, register, add, or start a specific
    result. Resolve references like "the second one" before calling this tool so `learning_id` is exact.

    Args:
        learning_id: Exact learning ID to enroll in.

    Returns:
        A JSON object with enrolled, already_enrolled, not_found, or error status.
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
        changed = enroll_course(settings.enrollments_path, learning_id)
    except (CatalogDataError, EnrollmentStoreError) as exc:
        return {"status": "error", "message": str(exc)}

    if not changed:
        return {
            "status": "already_enrolled",
            "message": f"You are already enrolled in {course.title}.",
            "course": course_to_summary(course),
        }
    return {
        "status": "enrolled",
        "message": f"You are now enrolled in {course.title}.",
        "course": course_to_summary(course),
    }
