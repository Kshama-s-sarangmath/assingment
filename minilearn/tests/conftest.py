from __future__ import annotations

from pathlib import Path
import shutil

import pytest

from minilearn.config.settings import reset_settings_cache


@pytest.fixture
def temp_data_dir(tmp_path: Path) -> Path:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    source_dir = Path(__file__).resolve().parents[1] / "data"
    shutil.copy(source_dir / "catalog.json", data_dir / "catalog.json")
    shutil.copy(source_dir / "enrollments.json", data_dir / "enrollments.json")
    return data_dir


@pytest.fixture(autouse=True)
def configure_test_env(monkeypatch: pytest.MonkeyPatch, temp_data_dir: Path):
    monkeypatch.setenv("MINILEARN_DATA_DIR", str(temp_data_dir))
    reset_settings_cache()
    yield
    reset_settings_cache()
