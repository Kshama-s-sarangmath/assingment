from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import os

import certifi
from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    base_dir: Path
    data_dir: Path
    catalog_path: Path
    enrollments_path: Path
    sessions_dir: Path
    logs_dir: Path
    gemini_model_id: str
    google_api_key: str | None
    temperature: float
    max_output_tokens: int
    allowed_origins: list[str]


def _base_dir() -> Path:
    return Path(__file__).resolve().parents[1]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    base_dir = _base_dir()
    load_dotenv(base_dir.parent / ".env")
    os.environ.setdefault("SSL_CERT_FILE", certifi.where())
    os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())
    configured_data_dir = os.getenv("MINILEARN_DATA_DIR")
    data_dir = Path(configured_data_dir or base_dir / "data").resolve()
    sessions_dir = base_dir / ".sessions"
    logs_dir = base_dir / ".logs"
    origins = os.getenv("MINILEARN_ALLOWED_ORIGINS", "http://localhost:5173")
    return Settings(
        base_dir=base_dir,
        data_dir=data_dir,
        catalog_path=data_dir / "catalog.json",
        enrollments_path=data_dir / "enrollments.json",
        sessions_dir=sessions_dir,
        logs_dir=logs_dir,
        gemini_model_id=os.getenv("GEMINI_MODEL_ID", "gemini-3.6-flash"),
        google_api_key=os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"),
        temperature=float(os.getenv("MODEL_TEMPERATURE", "0.2")),
        max_output_tokens=int(os.getenv("MAX_OUTPUT_TOKENS", "1200")),
        allowed_origins=[origin.strip() for origin in origins.split(",") if origin.strip()],
    )


def reset_settings_cache() -> None:
    get_settings.cache_clear()
