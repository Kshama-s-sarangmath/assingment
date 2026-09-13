from __future__ import annotations

from typing import Any

from strands import tool

from minilearn.config.settings import get_settings
from minilearn.utils.catalog import CatalogDataError, course_to_detail, get_course_by_id, load_catalog


@tool
def get_course_details(learning_id: str) -> dict[str, Any]:
    """Retrieve the full published catalog record for one learning item by learning ID.

    Use this tool when the learner asks for more detail about a specific result, wants prerequisites,
    duration, provider, skills, or any other record field for a single known learning ID.

    Args:
        learning_id: Exact learning ID such as LRN-00123.

    Returns:
        A JSON object containing either the published course details or a not_found status.
    """

    settings = get_settings()
    try:
        catalog = load_catalog(settings.catalog_path)
    except CatalogDataError as exc:
        return {"status": "error", "message": str(exc)}

    course = get_course_by_id(catalog, learning_id)
    if course is None:
        return {
            "status": "not_found",
            "message": f"No published learning item was found for {learning_id}.",
        }
    return {"status": "success", "course": course_to_detail(course)}
