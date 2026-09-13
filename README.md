# MiniLearn

MiniLearn is a local learning-discovery assistant built with the Strands Agents SDK, a Python FastAPI backend, and a React frontend. The backend uses Gemini and exposes a streaming endpoint that the UI consumes incrementally.

## Features

- Strands `Agent` with six custom `@tool` functions
- Weighted BM25-style search over title, description, skills, and tags
- Strict filters for learning type, provider, level, and maximum duration
- Persistent enroll and unenroll actions stored in local JSON
- Structured Pydantic response on every turn
- Session-backed multi-turn conversations using `FileSessionManager`
- React chat UI with streaming updates

## Project layout

```text
minilearn/
  agent.py
  api.py
  config/
  data/
  models/
  tests/
  tools/
  utils/
frontend/
```

## Setup

1. Create and activate a virtual environment.
2. Install Python dependencies:

```powershell
.\.venv\Scripts\python -m pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and set `GOOGLE_API_KEY`.
4. If your `.env` still has an older Gemini model, set `GEMINI_MODEL_ID=gemini-3.6-flash`.
5. Install frontend dependencies:

```powershell
cd frontend
npm install
cd ..
```

## Run the backend

```powershell
.\.venv\Scripts\python -m uvicorn minilearn.api:app --reload
```

## Run the CLI demo

```powershell
.\.venv\Scripts\python -m minilearn.agent
```

The CLI uses `stream_async()` and prints streamed chunks before showing the final validated `LearningResponse` JSON.

## Run the frontend

```powershell
cd frontend
npm run dev
```

Vite proxies `/api` requests to `http://localhost:8000`.

## Tests

Run the backend tests with coverage:

```powershell
.\.venv\Scripts\python -m pytest --cov=minilearn.utils --cov=minilearn.tools --cov-report=term-missing
```

## Known gaps

- The local environment here uses Python 3.14, but the code is written to remain compatible with Python 3.13 style features.
- The React UI renders the structured response and streamed chunks, but it does not yet visualize full catalog cards from intermediate tool payloads.
- Live Gemini testing requires a valid API key in `.env`.
