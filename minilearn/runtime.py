from __future__ import annotations

import logging
import os
import ssl
from typing import Any

import certifi
from google.genai import errors as genai_errors
from google.genai import types
from strands import Agent
from strands.models.gemini import GeminiModel
from strands.session.file_session_manager import FileSessionManager

from minilearn.config.prompts import SYSTEM_PROMPT
from minilearn.config.settings import Settings, get_settings
from minilearn.models.responses import LearningResponse, fallback_response
from minilearn.tools import ALL_TOOLS

logger = logging.getLogger(__name__)


def _build_model(settings: Settings, *, insecure_ssl: bool = False):
    if not settings.google_api_key:
        raise RuntimeError("Set GOOGLE_API_KEY to a valid Gemini API key before running MiniLearn.")

    os.environ.setdefault("SSL_CERT_FILE", certifi.where())
    os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())

    client_args: dict[str, Any] = {"api_key": settings.google_api_key}
    if insecure_ssl:
        client_args["http_options"] = types.HttpOptions(
            async_client_args={"ssl": ssl._create_unverified_context()}
        )
    else:
        client_args["http_options"] = types.HttpOptions(
            async_client_args={"ssl": ssl.create_default_context(cafile=certifi.where())}
        )
    return GeminiModel(
        client_args=client_args,
        model_id=settings.gemini_model_id,
        params={"temperature": settings.temperature, "max_output_tokens": settings.max_output_tokens},
    )


def create_agent(session_id: str, *, insecure_ssl: bool = False) -> Agent:
    settings = get_settings()
    settings.sessions_dir.mkdir(parents=True, exist_ok=True)
    settings.logs_dir.mkdir(parents=True, exist_ok=True)
    model = _build_model(settings, insecure_ssl=insecure_ssl)
    session_manager = FileSessionManager(session_id=session_id, storage_dir=str(settings.sessions_dir))
    return Agent(
        model=model,
        tools=ALL_TOOLS,
        system_prompt=SYSTEM_PROMPT,
        structured_output_model=LearningResponse,
        structured_output_prompt="Return a valid LearningResponse object only.",
        callback_handler=None,
        session_manager=session_manager,
    )


def _is_certificate_error(exc: Exception) -> bool:
    message = str(exc).lower()
    if "certificate verify failed" in message or "clientconnectorcertificateerror" in message:
        return True
    cause = exc.__cause__ or exc.__context__
    return bool(cause and cause is not exc and _is_certificate_error(cause))


def _diagnose_model_error(exc: Exception | None) -> str:
    if exc is None:
        return "MiniLearn could not complete that request."

    message = str(exc).lower()
    if _is_certificate_error(exc):
        return (
            "MiniLearn could not verify the Gemini TLS certificate chain. "
            "Set SSL_CERT_FILE to a trusted CA bundle or keep the runtime retry enabled."
        )

    if isinstance(exc, genai_errors.ClientError):
        if "api key not valid" in message or "api_key_invalid" in message:
            return "The configured GOOGLE_API_KEY is invalid. Replace it with a valid Gemini API key."
        if "no longer available to new users" in message or "not_found" in message:
            return "Update GEMINI_MODEL_ID to a currently supported model such as gemini-3.6-flash."

    return "MiniLearn could not reach Gemini or the local catalog safely. Check your configuration and try again."


async def stream_learning_turn(session_id: str, prompt: str):
    last_error: Exception | None = None
    for insecure_ssl in (False, True):
        agent = create_agent(session_id, insecure_ssl=insecure_ssl)
        last_tool_use_id: str | None = None
        try:
            async for event in agent.stream_async(prompt, structured_output_model=LearningResponse):
                if not isinstance(event, dict):
                    continue

                chunk = event.get("data")
                if isinstance(chunk, str) and chunk:
                    yield {"type": "chunk", "text": chunk}

                tool_use = event.get("current_tool_use")
                if isinstance(tool_use, dict):
                    tool_use_id = tool_use.get("toolUseId")
                    if tool_use_id and tool_use_id != last_tool_use_id:
                        last_tool_use_id = tool_use_id
                        yield {"type": "tool", "name": tool_use.get("name", "tool")}

                result = event.get("result")
                if result is not None:
                    structured = result.structured_output or fallback_response(
                        "I could not format that answer. Please try the request again."
                    )
                    response = (
                        structured
                        if isinstance(structured, LearningResponse)
                        else LearningResponse.model_validate(structured)
                    )
                    yield {"type": "result", "response": response.model_dump()}
                    return
        except Exception as exc:
            last_error = exc
            if _is_certificate_error(exc) and not insecure_ssl:
                logger.warning("Gemini TLS verification failed; retrying once with an unverified SSL context.")
                continue
            break

    yield {
        "type": "result",
        "response": fallback_response(_diagnose_model_error(last_error)).model_dump(),
    }
