from __future__ import annotations

from pathlib import Path

import pytest

from minilearn.utils.store import (
    EnrollmentStoreError,
    enroll_course,
    list_enrollment_ids,
    load_enrollments,
    unenroll_course,
)


def test_missing_store_is_initialized(tmp_path: Path) -> None:
    store_path = tmp_path / "enrollments.json"
    assert list_enrollment_ids(store_path) == []
    assert store_path.exists()


def test_enroll_idempotency(temp_data_dir: Path) -> None:
    store_path = temp_data_dir / "enrollments.json"
    assert enroll_course(store_path, "LRN-00102") is True
    assert enroll_course(store_path, "LRN-00102") is False
    assert list_enrollment_ids(store_path) == ["LRN-00102"]


def test_unenroll_missing_course_returns_false(temp_data_dir: Path) -> None:
    store_path = temp_data_dir / "enrollments.json"
    assert unenroll_course(store_path, "LRN-00999") is False


def test_unenroll_removes_existing_course(temp_data_dir: Path) -> None:
    store_path = temp_data_dir / "enrollments.json"
    enroll_course(store_path, "LRN-00102")
    assert unenroll_course(store_path, "LRN-00102") is True
    assert list_enrollment_ids(store_path) == []


def test_malformed_store_raises(tmp_path: Path) -> None:
    store_path = tmp_path / "enrollments.json"
    store_path.write_text("[]", encoding="utf-8")
    with pytest.raises(EnrollmentStoreError):
        load_enrollments(store_path)
