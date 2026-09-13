# MiniLearn Design

## Overview

MiniLearn is split into a thin agent layer, a pure utility layer, and a React UI. The Strands agent is responsible for tool selection, conversation carry-over, and producing a validated `LearningResponse`. All catalog search and enrollment persistence live outside the LLM path so they are deterministic and directly testable.

## Tool boundaries

Each tool owns one clear intent boundary.

- `search_courses` handles discovery and refinement only.
- `get_course_details` retrieves one published record.
- `enroll_in_course` mutates the enrollment store after catalog validation.
- `unenroll_from_course` removes an enrollment after catalog validation.
- `get_my_enrollments` joins stored enrollment IDs back to published catalog entries.
- `get_popular_courses` exposes non-query-based recommendations.

The tools are intentionally thin wrappers. They read configuration, call utility functions, and convert exceptions into learner-safe JSON results. This keeps the LLM-facing schema readable and the business logic independent from Strands.

## Ranking formula

`search_courses` uses a BM25-style relevance score instead of simple substring matching. The query is tokenized and scored against four fields.

- Title weight: `4.2`
- Skills weight: `3.1`
- Tags weight: `2.5`
- Description weight: `1.6`

These weights are justified by how users search in an LMS.

- Title is the strongest signal because it usually contains the explicit topic name.
- Skills are next because they represent structured curriculum intent.
- Tags add recall for shorter aliases such as `ml`, `genai`, or `ui`.
- Description has broader context, but it is noisier, so it gets the lowest weight.

The final ranking uses:

```text
score = weighted_bm25 + phrase_bonus + popularity_tiebreak
```

- `weighted_bm25` is the sum of per-field BM25 contributions.
- `phrase_bonus` rewards exact phrase matches in title and description.
- `popularity_tiebreak` adds a small normalized lift so equally relevant items prefer stronger social proof.

Strict filters are applied before scoring. `publishedStatus=false` items are removed before any ranking happens.

## Session and persistence model

Conversation state is handled with `FileSessionManager`, keyed by `session_id`. That allows multi-turn interactions such as "enroll me in the second one" to work across HTTP requests and survive restarts. Enrollment mutations are persisted independently in `data/enrollments.json`, which means a restarted process still reflects prior enrollments even if the model session history changes.

## Error handling

The backend follows two rules.

- Utility and storage failures raise typed exceptions.
- Agent and API layers log stack traces with `logger.exception(...)` and return learner-safe fallback messages.

That prevents raw tracebacks from leaking into the CLI or UI while keeping enough operational detail in logs.

## React UI choices

The frontend is intentionally lightweight.

- `fetch()` streams newline-delimited JSON from the FastAPI endpoint.
- The UI keeps a stable `sessionId` in local storage so the same learner conversation continues across refreshes.
- The assistant panel shows streaming text immediately, then replaces it with the final validated `LearningResponse` content.

## Path to AWS Bedrock AgentCore + OpenSearch

To move this design onto AWS later, the seams are already in place.

1. Replace local catalog search with OpenSearch. The current `utils/catalog.py` interface can become a query adapter that maps strict filters to OpenSearch filters and field weights to an OpenSearch BM25 query.
2. Swap `GeminiModel` or `LiteLLMModel` for a Bedrock-backed provider or AgentCore-hosted agent without changing the tools.
3. Replace local file persistence with DynamoDB or Aurora for enrollments and S3-backed session storage.
4. Add structured logging, traces, and metrics exporters for production observability.

The current split keeps that migration mostly infrastructural rather than architectural.
