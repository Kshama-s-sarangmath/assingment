from __future__ import annotations

import json
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field

from minilearn.config.settings import get_settings
from minilearn.models.responses import fallback_response
from minilearn.runtime import stream_learning_turn

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger(__name__)

settings = get_settings()
app = FastAPI(title="MiniLearn API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    session_id: str = Field(alias="sessionId")
    message: str


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest) -> StreamingResponse:
    async def generate():
        try:
            async for event in stream_learning_turn(request.session_id, request.message):
                yield json.dumps(event) + "\n"
        except Exception:
            logger.exception("Chat stream failed")
            response = fallback_response(
                "I could not reach the model or local data safely. Check your configuration and try again.",
                title="MiniLearn is unavailable",
            )
            yield json.dumps({"type": "result", "response": response.model_dump()}) + "\n"

    return StreamingResponse(generate(), media_type="application/x-ndjson")
