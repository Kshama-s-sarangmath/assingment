from __future__ import annotations

from typing import Any

from strands import tool

from minilearn.config.settings import get_settings
from minilearn.utils.catalog import CatalogDataError, course_to_summary, load_catalog, search_catalog


@tool
def search_courses(
    query: str,
    learning_type: str | None = None,
    provider: str | None = None,
    level: str | None = None,
    max_duration_hours: float | None = None,
) -> dict[str, Any]:
    """Search the published learning catalog using a topical query plus optional strict filters.

    Use this tool whenever the learner asks to find, browse, compare, or refine courses, lessons,
    concepts, programs, or learning paths. Keep `query` focused on the topic or skill. Put exact
    filters into the dedicated arguments instead of burying them in the free-text query.

    Args:
        query: Topic, goal, or skill the learner wants to study.
        learning_type: Exact learning type filter when the learner specifies one.
        provider: Exact provider filter when the learner names a provider.
        level: Exact level filter when the learner asks for beginner, intermediate, or advanced.
        max_duration_hours: Maximum duration in hours when the learner asks for a time limit.

    Returns:
        A JSON object with the strict filters applied and up to 30 ranked published matches.
    """

    settings = get_settings()
    try:
        catalog = load_catalog(settings.catalog_path)
        results = search_catalog(
            catalog,
            query=query,
            learning_type=learning_type,
            provider=provider,
            level=level,
            max_duration_hours=max_duration_hours,
        )
    except CatalogDataError as exc:
        return {"status": "error", "message": str(exc), "results": []}

    return {
        "status": "success",
        "query": query,
        "filters": {
            "learning_type": learning_type,
            "provider": provider,
            "level": level,
            "max_duration_hours": max_duration_hours,
        },
        "count": len(results),
        "results": [course_to_summary(course) for course in results],
    }
