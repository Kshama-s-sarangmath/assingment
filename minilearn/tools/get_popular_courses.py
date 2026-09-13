from __future__ import annotations

from typing import Any

from strands import tool

from minilearn.config.settings import get_settings
from minilearn.utils.catalog import CatalogDataError, course_to_summary, load_catalog, popular_courses


@tool
def get_popular_courses(learning_type: str | None = None) -> dict[str, Any]:
    """Return trending published learning items ranked by enrollment count and rating.

    Use this tool when the learner asks what is trending, popular, hot, widely taken, or generally
    recommended. Apply `learning_type` only when the learner asks for trending items within one type.

    Args:
        learning_type: Optional exact learning type filter.

    Returns:
        A JSON object containing the most popular published learning items.
    """

    settings = get_settings()
    try:
        catalog = load_catalog(settings.catalog_path)
        results = popular_courses(catalog, learning_type=learning_type)
    except CatalogDataError as exc:
        return {"status": "error", "message": str(exc), "results": []}

    return {
        "status": "success",
        "learning_type": learning_type,
        "count": len(results),
        "results": [course_to_summary(course) for course in results],
    }
