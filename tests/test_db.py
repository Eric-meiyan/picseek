import os
import struct
import pytest
from picseek.db import Database, serialize_f32


def make_vector(value: float, dim: int = 512) -> list[float]:
    """Create a dummy vector filled with a single value."""
    return [value] * dim


def test_serialize_f32_produces_correct_bytes():
    vec = [1.0, 2.0, 3.0]
    result = serialize_f32(vec)
    assert isinstance(result, bytes)
    assert len(result) == 3 * 4  # 3 floats * 4 bytes each
    unpacked = struct.unpack("3f", result)
    assert unpacked == (1.0, 2.0, 3.0)


def test_database_creates_tables(tmp_path):
    db_path = str(tmp_path / "test.db")
    db = Database(db_path)
    db.close()
    assert os.path.exists(db_path)


def test_insert_and_get_image(tmp_path):
    db = Database(str(tmp_path / "test.db"))
    vec = make_vector(0.1)
    row_id = db.insert_image("/path/to/img.jpg", 1024, 1700000000.0, vec)
    assert row_id > 0
    record = db.get_image("/path/to/img.jpg")
    assert record is not None
    assert record["file_path"] == "/path/to/img.jpg"
    assert record["file_size"] == 1024
    db.close()


def test_delete_image(tmp_path):
    db = Database(str(tmp_path / "test.db"))
    vec = make_vector(0.1)
    db.insert_image("/path/to/img.jpg", 1024, 1700000000.0, vec)
    db.delete_image("/path/to/img.jpg")
    assert db.get_image("/path/to/img.jpg") is None
    db.close()


def test_get_all_records(tmp_path):
    db = Database(str(tmp_path / "test.db"))
    db.insert_image("/a.jpg", 100, 1.0, make_vector(0.1))
    db.insert_image("/b.jpg", 200, 2.0, make_vector(0.2))
    records = db.get_all_records()
    assert len(records) == 2
    paths = {r["file_path"] for r in records}
    assert paths == {"/a.jpg", "/b.jpg"}
    db.close()


def test_search_similar(tmp_path):
    db = Database(str(tmp_path / "test.db"))
    db.insert_image("/a.jpg", 100, 1.0, make_vector(0.1))
    db.insert_image("/b.jpg", 200, 2.0, make_vector(0.9))
    # Search with a vector close to b.jpg
    results = db.search(make_vector(0.85), limit=2)
    assert len(results) == 2
    # b.jpg should be more similar (closer distance)
    assert results[0]["file_path"] == "/b.jpg"
    db.close()


def test_update_image(tmp_path):
    db = Database(str(tmp_path / "test.db"))
    vec1 = make_vector(0.1)
    vec2 = make_vector(0.9)
    db.insert_image("/a.jpg", 100, 1.0, vec1)
    db.update_image("/a.jpg", 200, 2.0, vec2)
    record = db.get_image("/a.jpg")
    assert record["file_size"] == 200
    assert record["modified_at"] == 2.0
    db.close()
