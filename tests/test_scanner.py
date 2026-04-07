import os
import pytest
from picseek.scanner import scan_images


def _create_files(tmp_path, filenames: list[str]) -> None:
    for name in filenames:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"\x00")


def test_scan_finds_supported_formats(tmp_path):
    _create_files(tmp_path, ["a.jpg", "b.png", "c.webp", "d.txt", "e.py"])
    results = scan_images(str(tmp_path), formats=["jpg", "png", "webp"])
    paths = {r["file_path"] for r in results}
    assert str(tmp_path / "a.jpg") in paths
    assert str(tmp_path / "b.png") in paths
    assert str(tmp_path / "c.webp") in paths
    assert str(tmp_path / "d.txt") not in paths


def test_scan_is_case_insensitive(tmp_path):
    _create_files(tmp_path, ["photo.JPG", "image.Png"])
    results = scan_images(str(tmp_path), formats=["jpg", "png"])
    assert len(results) == 2


def test_scan_recurses_subdirectories(tmp_path):
    _create_files(tmp_path, ["a.jpg", "sub/b.jpg", "sub/deep/c.jpg"])
    results = scan_images(str(tmp_path), formats=["jpg"])
    assert len(results) == 3


def test_scan_returns_file_metadata(tmp_path):
    (tmp_path / "a.jpg").write_bytes(b"\x00\x01\x02")
    results = scan_images(str(tmp_path), formats=["jpg"])
    assert len(results) == 1
    r = results[0]
    assert "file_path" in r
    assert "file_size" in r
    assert "modified_at" in r
    assert r["file_size"] == 3


def test_scan_empty_directory(tmp_path):
    results = scan_images(str(tmp_path), formats=["jpg"])
    assert results == []


def test_scan_nonexistent_directory():
    with pytest.raises(FileNotFoundError):
        scan_images("/nonexistent/path", formats=["jpg"])
