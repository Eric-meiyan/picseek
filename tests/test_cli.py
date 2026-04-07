import os
import pytest
from click.testing import CliRunner
from PIL import Image
from picseek.cli import main
from picseek.model import reset_model


@pytest.fixture(autouse=True)
def use_mock_model(monkeypatch):
    monkeypatch.setenv("PICSEEK_MOCK_MODEL", "1")
    reset_model()
    yield
    reset_model()


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def img_dir(tmp_path):
    d = tmp_path / "images"
    d.mkdir()
    for color in ["red", "green", "blue"]:
        Image.new("RGB", (64, 64), color=color).save(str(d / f"{color}.jpg"))
    return str(d)


def test_config_command(runner, tmp_path):
    config_path = str(tmp_path / "config.yaml")
    result = runner.invoke(main, ["config", "--config-path", config_path])
    assert result.exit_code == 0
    assert "formats" in result.output


def test_index_command(runner, img_dir, tmp_path):
    db_path = str(tmp_path / "test.db")
    config_path = str(tmp_path / "config.yaml")
    result = runner.invoke(main, [
        "index", img_dir,
        "--db-path", db_path,
        "--config-path", config_path,
    ])
    assert result.exit_code == 0
    assert "New:" in result.output or "new" in result.output.lower()


def test_index_nonexistent_directory(runner, tmp_path):
    result = runner.invoke(main, [
        "index", "/nonexistent/path",
        "--db-path", str(tmp_path / "test.db"),
        "--config-path", str(tmp_path / "config.yaml"),
    ])
    assert result.exit_code != 0


def test_search_command(runner, img_dir, tmp_path):
    db_path = str(tmp_path / "test.db")
    config_path = str(tmp_path / "config.yaml")
    runner.invoke(main, [
        "index", img_dir,
        "--db-path", db_path,
        "--config-path", config_path,
    ])
    result = runner.invoke(main, [
        "search", "red color",
        "--db-path", db_path,
        "--config-path", config_path,
        "--no-sync",
        "-n", "2",
    ])
    assert result.exit_code == 0
    assert ".jpg" in result.output


def test_search_empty_db(runner, tmp_path):
    db_path = str(tmp_path / "empty.db")
    config_path = str(tmp_path / "config.yaml")
    result = runner.invoke(main, [
        "search", "anything",
        "--db-path", db_path,
        "--config-path", config_path,
        "--no-sync",
    ])
    assert result.exit_code == 0
    assert "No images indexed" in result.output
