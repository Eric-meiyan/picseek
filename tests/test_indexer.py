import os
import pytest
from PIL import Image
from picseek.indexer import run_index
from picseek.db import Database
from picseek.model import reset_model


@pytest.fixture(autouse=True)
def use_mock_model(monkeypatch):
    monkeypatch.setenv("PICSEEK_MOCK_MODEL", "1")
    reset_model()
    yield
    reset_model()


def _create_test_images(tmp_path, count: int = 3) -> str:
    img_dir = tmp_path / "images"
    img_dir.mkdir()
    for i in range(count):
        img = Image.new("RGB", (64, 64), color=(i * 50, i * 50, i * 50))
        img.save(str(img_dir / f"img_{i}.jpg"))
    return str(img_dir)


def test_run_index_indexes_all_images(tmp_path):
    img_dir = _create_test_images(tmp_path, count=3)
    db_path = str(tmp_path / "test.db")
    stats = run_index(img_dir, db_path, formats=["jpg"])
    assert stats["new"] == 3
    assert stats["deleted"] == 0
    assert stats["updated"] == 0
    assert stats["errors"] == 0


def test_run_index_skips_already_indexed(tmp_path):
    img_dir = _create_test_images(tmp_path, count=2)
    db_path = str(tmp_path / "test.db")
    run_index(img_dir, db_path, formats=["jpg"])
    stats = run_index(img_dir, db_path, formats=["jpg"])
    assert stats["new"] == 0
    assert stats["skipped"] == 2


def test_run_index_detects_deleted(tmp_path):
    img_dir = _create_test_images(tmp_path, count=2)
    db_path = str(tmp_path / "test.db")
    run_index(img_dir, db_path, formats=["jpg"])
    os.remove(os.path.join(img_dir, "img_0.jpg"))
    stats = run_index(img_dir, db_path, formats=["jpg"])
    assert stats["deleted"] == 1


def test_run_index_handles_corrupt_image(tmp_path):
    img_dir = tmp_path / "images"
    img_dir.mkdir()
    img = Image.new("RGB", (64, 64), color="red")
    img.save(str(img_dir / "good.jpg"))
    (img_dir / "bad.jpg").write_bytes(b"not an image")
    db_path = str(tmp_path / "test.db")
    stats = run_index(str(img_dir), db_path, formats=["jpg"])
    assert stats["new"] == 1
    assert stats["errors"] == 1
