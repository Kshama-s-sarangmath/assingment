from __future__ import annotations

from collections import Counter
from math import log, log1p
from pathlib import Path
import json
import re
from typing import Any, Iterable, Literal, Sequence

from pydantic import BaseModel, ValidationError


LearningType = Literal["program", "concept", "learning path", "course", "lesson"]
Provider = Literal["MS Learn", "Cognizant", "Skillsoft", "AWS Builder"]
Level = Literal["beginner", "intermediate", "advanced"]

FIELD_WEIGHTS: dict[str, float] = {
    "title": 4.2,
    "skills": 3.1,
    "tags": 2.5,
    "description": 1.6,
}
TOKEN_RE = re.compile(r"[a-z0-9]+")


class CatalogDataError(RuntimeError):
    """Raised when the catalog file cannot be loaded or validated."""


class CatalogRecord(BaseModel):
    learningId: str
    title: str
    description: str
    learningType: LearningType
    provider: Provider
    skills: list[str]
    level: Level
    durationHours: float
    prerequisiteNames: list[str]
    publishedStatus: bool
    rating: float
    enrollmentCount: int
    tags: list[str]


def tokenize(value: str | Sequence[str]) -> list[str]:
    if isinstance(value, str):
        source = value.lower()
    else:
        source = " ".join(value).lower()
    return TOKEN_RE.findall(source)


def load_catalog(path: Path) -> list[CatalogRecord]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CatalogDataError(f"Catalog file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CatalogDataError(f"Catalog JSON is malformed: {exc}") from exc

    if not isinstance(payload, list):
        raise CatalogDataError("Catalog JSON must be a list of course records.")

    try:
        return [CatalogRecord.model_validate(item) for item in payload]
    except ValidationError as exc:
        raise CatalogDataError(f"Catalog JSON failed validation: {exc}") from exc


def course_to_summary(course: CatalogRecord) -> dict[str, Any]:
    return {
        "learningId": course.learningId,
        "title": course.title,
        "learningType": course.learningType,
        "provider": course.provider,
        "level": course.level,
        "durationHours": course.durationHours,
        "rating": course.rating,
        "enrollmentCount": course.enrollmentCount,
        "skills": course.skills,
        "tags": course.tags,
    }


def course_to_detail(course: CatalogRecord) -> dict[str, Any]:
    detail = course.model_dump()
    return detail


def get_course_by_id(
    catalog: Iterable[CatalogRecord], learning_id: str, published_only: bool = True
) -> CatalogRecord | None:
    for course in catalog:
        if course.learningId == learning_id and (course.publishedStatus or not published_only):
            return course
    return None


def popularity_score(course: CatalogRecord) -> float:
    return log1p(course.enrollmentCount) * 0.8 + course.rating * 1.6


def popular_courses(
    catalog: Sequence[CatalogRecord], learning_type: str | None = None, limit: int = 10
) -> list[CatalogRecord]:
    filtered = [course for course in catalog if course.publishedStatus]
    if learning_type is not None:
        filtered = [course for course in filtered if course.learningType == learning_type]
    return sorted(
        filtered,
        key=lambda course: (popularity_score(course), course.rating, course.enrollmentCount),
        reverse=True,
    )[:limit]


def _apply_filters(
    catalog: Iterable[CatalogRecord],
    learning_type: str | None,
    provider: str | None,
    level: str | None,
    max_duration_hours: float | None,
) -> list[CatalogRecord]:
    filtered = [course for course in catalog if course.publishedStatus]
    if learning_type is not None:
        filtered = [course for course in filtered if course.learningType == learning_type]
    if provider is not None:
        filtered = [course for course in filtered if course.provider == provider]
    if level is not None:
        filtered = [course for course in filtered if course.level == level]
    if max_duration_hours is not None:
        filtered = [course for course in filtered if course.durationHours <= max_duration_hours]
    return filtered


def _field_tokens(course: CatalogRecord) -> dict[str, list[str]]:
    return {
        "title": tokenize(course.title),
        "skills": tokenize(course.skills),
        "tags": tokenize(course.tags),
        "description": tokenize(course.description),
    }


def _average_field_lengths(courses: Sequence[CatalogRecord]) -> dict[str, float]:
    averages: dict[str, float] = {}
    tokenized = [_field_tokens(course) for course in courses]
    for field_name in FIELD_WEIGHTS:
        total = sum(len(item[field_name]) for item in tokenized)
        averages[field_name] = total / max(len(tokenized), 1)
    return averages


def _inverse_document_frequency(courses: Sequence[CatalogRecord]) -> dict[str, float]:
    documents = []
    for course in courses:
        field_terms = set()
        for tokens in _field_tokens(course).values():
            field_terms.update(tokens)
        documents.append(field_terms)

    doc_count = len(documents)
    frequencies: Counter[str] = Counter()
    for terms in documents:
        frequencies.update(terms)

    return {
        term: log((doc_count - frequency + 0.5) / (frequency + 0.5) + 1.0)
        for term, frequency in frequencies.items()
    }


def _bm25(tf: int, doc_len: int, avg_len: float, idf: float, k1: float = 1.5, b: float = 0.75) -> float:
    if tf == 0:
        return 0.0
    norm = tf + k1 * (1 - b + b * (doc_len / max(avg_len, 1e-6)))
    return idf * ((tf * (k1 + 1)) / norm)


def _text_score(
    course: CatalogRecord,
    query_terms: list[str],
    idf_map: dict[str, float],
    avg_lengths: dict[str, float],
) -> float:
    if not query_terms:
        return 0.0

    field_map = _field_tokens(course)
    score = 0.0
    for field_name, weight in FIELD_WEIGHTS.items():
        terms = field_map[field_name]
        counts = Counter(terms)
        for term in query_terms:
            score += weight * _bm25(
                tf=counts.get(term, 0),
                doc_len=len(terms),
                avg_len=avg_lengths[field_name],
                idf=idf_map.get(term, 0.0),
            )

    query_phrase = " ".join(query_terms)
    title_text = course.title.lower()
    description_text = course.description.lower()
    if query_phrase and query_phrase in title_text:
        score += 4.0
    if query_phrase and query_phrase in description_text:
        score += 1.6
    return score


def search_catalog(
    catalog: Sequence[CatalogRecord],
    query: str,
    learning_type: str | None = None,
    provider: str | None = None,
    level: str | None = None,
    max_duration_hours: float | None = None,
    limit: int = 30,
) -> list[CatalogRecord]:
    filtered = _apply_filters(catalog, learning_type, provider, level, max_duration_hours)
    query_terms = tokenize(query)
    published = [course for course in catalog if course.publishedStatus]

    if not filtered:
        return []

    if not query_terms:
        ranked = sorted(
            filtered,
            key=lambda course: (popularity_score(course), course.rating),
            reverse=True,
        )
    else:
        avg_lengths = _average_field_lengths(published)
        idf_map = _inverse_document_frequency(published)
        scored: list[tuple[float, CatalogRecord]] = []
        for course in filtered:
            score = _text_score(course, query_terms, idf_map, avg_lengths)
            if score > 0:
                score += popularity_score(course) * 0.02
                scored.append((score, course))
        ranked = [course for _, course in sorted(scored, key=lambda item: item[0], reverse=True)]

    deduped: list[CatalogRecord] = []
    seen: set[str] = set()
    for course in ranked:
        if course.learningId in seen:
            continue
        seen.add(course.learningId)
        deduped.append(course)
        if len(deduped) >= limit:
            break
    return deduped
