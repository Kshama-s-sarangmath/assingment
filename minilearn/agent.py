from __future__ import annotations

import asyncio
import json
import logging
import os

from minilearn.models.responses import LearningResponse, fallback_response
from minilearn.runtime import stream_learning_turn

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger(__name__)


async def run_repl() -> None:
    session_id = os.getenv("MINILEARN_SESSION_ID", "cli-demo")
    print("MiniLearn CLI. Type 'exit' to quit.")
    while True:
        prompt = input("you> ").strip()
        if not prompt:
            continue
        if prompt.lower() in {"exit", "quit"}:
            break

        final_response: LearningResponse | None = None
        print("assistant> ", end="", flush=True)
        try:
            async for event in stream_learning_turn(session_id, prompt):
                if event["type"] == "chunk":
                    print(event["text"], end="", flush=True)
                elif event["type"] == "tool":
                    print(f"\n[tool: {event['name']}]\n", end="", flush=True)
                elif event["type"] == "result":
                    final_response = LearningResponse.model_validate(event["response"])
            print()
        except Exception:
            logger.exception("CLI turn failed")
            final_response = fallback_response(
                "I could not complete that turn. Verify your model credentials and local data files."
            )
            print()

        if final_response is not None:
            print(json.dumps(final_response.model_dump(), indent=2))


if __name__ == "__main__":
    asyncio.run(run_repl())
