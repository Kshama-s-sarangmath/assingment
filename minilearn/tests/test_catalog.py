from __future__ import annotations

from pathlib import Path

import pytest

from minilearn.config.settings import get_settings
from minilearn.utils.catalog import CatalogDataError, load_catalog, popular_courses, search_catalog


def test_machine_learning_search_ranks_intro_course_first() -> None:
    catalog = load_catalog(get_settings().catalog_path)
    results = search_catalog(catalog, query="machine learning")
    assert results
    assert results[0].learningId == "LRN-00102"


@pytest.mark.parametrize(
    ("kwargs", "expected_field", "expected_value"),
    [
        ({"learning_type": "lesson"}, "learningType", "lesson"),
        ({"provider": "AWS Builder"}, "provider", "AWS Builder"),
        ({"level": "beginner"}, "level", "beginner"),
    ],
)
def test_search_applies_strict_filters(
    kwargs: dict[str, str], expected_field: str, expected_value: str
) -> None:
    catalog = load_catalog(get_settings().catalog_path)
    results = search_catalog(catalog, query="cloud", **kwargs)
    assert results
    assert all(getattr(item, expected_field) == expected_value for item in results)


def test_search_respects_max_duration() -> None:
    catalog = load_catalog(get_settings().catalog_path)
    results = search_catalog(catalog, query="machine learning", max_duration_hours=5)
    assert results
    assert all(item.durationHours <= 5 for item in results)


def test_unpublished_courses_never_returned() -> None:
    catalog = load_catalog(get_settings().catalog_path)
    results = search_catalog(catalog, query="fraud detection")
    assert results == []


def test_popular_courses_respects_learning_type() -> None:
    catalog = load_catalog(get_settings().catalog_path)
    results = popular_courses(catalog, learning_type="course")
    assert results
    assert all(item.learningType == "course" for item in results)


def test_malformed_catalog_file_raises(tmp_path: Path) -> None:
    bad_file = tmp_path / "catalog.json"
    bad_file.write_text("{not valid json", encoding="utf-8")
    with pytest.raises(CatalogDataError):
        load_catalog(bad_file)
