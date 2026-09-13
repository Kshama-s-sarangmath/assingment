from __future__ import annotations

from pathlib import Path
from threading import RLock
import json


class EnrollmentStoreError(RuntimeError):
    """Raised when the enrollment store cannot be read or written safely."""


DEFAULT_ENROLLMENTS = {"learnerId": "demo-learner", "learningIds": []}
_FILE_LOCK = RLock()


def _validate_payload(payload: object) -> dict[str, object]:
    if not isinstance(payload, dict):
        raise EnrollmentStoreError("Enrollment JSON must be an object.")
    learner_id = payload.get("learnerId")
    learning_ids = payload.get("learningIds")
    if not isinstance(learner_id, str):
        raise EnrollmentStoreError("Enrollment JSON must contain a string learnerId.")
    if not isinstance(learning_ids, list) or not all(isinstance(item, str) for item in learning_ids):
        raise EnrollmentStoreError("Enrollment JSON must contain a learningIds string list.")
    return {"learnerId": learner_id, "learningIds": list(learning_ids)}


def _write_payload(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(".tmp")
    temp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    temp_path.replace(path)


def load_enrollments(path: Path) -> dict[str, object]:
    with _FILE_LOCK:
        if not path.exists():
            _write_payload(path, DEFAULT_ENROLLMENTS)
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise EnrollmentStoreError(f"Enrollment JSON is malformed: {exc}") from exc
        return _validate_payload(payload)


def list_enrollment_ids(path: Path) -> list[str]:
    payload = load_enrollments(path)
    return list(payload["learningIds"])


def enroll_course(path: Path, learning_id: str) -> bool:
    with _FILE_LOCK:
        payload = load_enrollments(path)
        learning_ids = list(payload["learningIds"])
        if learning_id in learning_ids:
            return False
        learning_ids.append(learning_id)
        _write_payload(path, {"learnerId": payload["learnerId"], "learningIds": learning_ids})
        return True


def unenroll_course(path: Path, learning_id: str) -> bool:
    with _FILE_LOCK:
        payload = load_enrollments(path)
        learning_ids = list(payload["learningIds"])
        if learning_id not in learning_ids:
            return False
        learning_ids.remove(learning_id)
        _write_payload(path, {"learnerId": payload["learnerId"], "learningIds": learning_ids})
        return True
