import os
import pytest
from PIL import Image
from picseek.searcher import run_search
from picseek.indexer import run_index
from picseek.model import reset_model


@pytest.fixture(autouse=True)
def use_mock_model(monkeypatch):
    monkeypatch.setenv("PICSEEK_MOCK_MODEL", "1")
    reset_model()
    yield
    reset_model()


def _create_colored_images(tmp_path) -> str:
    img_dir = tmp_path / "images"
    img_dir.mkdir()
    Image.new("RGB", (64, 64), color="red").save(str(img_dir / "red.jpg"))
    Image.new("RGB", (64, 64), color="blue").save(str(img_dir / "blue.jpg"))
    Image.new("RGB", (64, 64), color="green").save(str(img_dir / "green.jpg"))
    return str(img_dir)


def test_search_returns_results(tmp_path):
    img_dir = _create_colored_images(tmp_path)
    db_path = str(tmp_path / "test.db")
    run_index(img_dir, db_path, formats=["jpg"], show_progress=False)
    results = run_search("red color", db_path, limit=3, sync=False)
    assert len(results) > 0
    assert "file_path" in results[0]
    assert "score" in results[0]


def test_search_respects_limit(tmp_path):
    img_dir = _create_colored_images(tmp_path)
    db_path = str(tmp_path / "test.db")
    run_index(img_dir, db_path, formats=["jpg"], show_progress=False)
    results = run_search("any image", db_path, limit=2, sync=False)
    assert len(results) <= 2


def test_search_score_between_0_and_1(tmp_path):
    img_dir = _create_colored_images(tmp_path)
    db_path = str(tmp_path / "test.db")
    run_index(img_dir, db_path, formats=["jpg"], show_progress=False)
    results = run_search("a picture", db_path, limit=3, sync=False)
    for r in results:
        assert 0.0 <= r["score"] <= 1.0


def test_search_empty_db(tmp_path):
    db_path = str(tmp_path / "empty.db")
    results = run_search("anything", db_path, limit=5, sync=False)
    assert results == []
