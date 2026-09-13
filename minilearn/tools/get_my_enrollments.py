from __future__ import annotations

from typing import Any

from strands import tool

from minilearn.config.settings import get_settings
from minilearn.utils.catalog import CatalogDataError, course_to_summary, get_course_by_id, load_catalog
from minilearn.utils.store import EnrollmentStoreError, list_enrollment_ids


@tool
def get_my_enrollments() -> dict[str, Any]:
    """List the learner's current enrollments using published catalog details.

    Use this tool whenever the learner asks what they are enrolled in, wants to review current
    learning items, or needs context before deciding what to drop next.

    Returns:
        A JSON object containing the learner's enrolled published items in stored order.
    """

    settings = get_settings()
    try:
        catalog = load_catalog(settings.catalog_path)
        enrollment_ids = list_enrollment_ids(settings.enrollments_path)
    except (CatalogDataError, EnrollmentStoreError) as exc:
        return {"status": "error", "message": str(exc), "results": []}

    results = []
    for learning_id in enrollment_ids:
        course = get_course_by_id(catalog, learning_id)
        if course is not None:
            results.append(course_to_summary(course))

    return {
        "status": "success",
        "count": len(results),
        "results": results,
    }
