import pytest
from picseek.sync import compute_diff


def test_all_new_when_db_empty():
    db_records = []
    fs_files = [
        {"file_path": "/a.jpg", "file_size": 100, "modified_at": 1.0},
        {"file_path": "/b.jpg", "file_size": 200, "modified_at": 2.0},
    ]
    diff = compute_diff(db_records, fs_files)
    assert len(diff["added"]) == 2
    assert len(diff["deleted"]) == 0
    assert len(diff["modified"]) == 0


def test_no_changes_when_in_sync():
    records = [
        {"file_path": "/a.jpg", "file_size": 100, "modified_at": 1.0},
    ]
    diff = compute_diff(records, records)
    assert len(diff["added"]) == 0
    assert len(diff["deleted"]) == 0
    assert len(diff["modified"]) == 0


def test_detect_deleted_file():
    db_records = [
        {"file_path": "/a.jpg", "file_size": 100, "modified_at": 1.0},
        {"file_path": "/b.jpg", "file_size": 200, "modified_at": 2.0},
    ]
    fs_files = [
        {"file_path": "/a.jpg", "file_size": 100, "modified_at": 1.0},
    ]
    diff = compute_diff(db_records, fs_files)
    assert len(diff["deleted"]) == 1
    assert diff["deleted"][0]["file_path"] == "/b.jpg"


def test_detect_modified_file():
    db_records = [
        {"file_path": "/a.jpg", "file_size": 100, "modified_at": 1.0},
    ]
    fs_files = [
        {"file_path": "/a.jpg", "file_size": 150, "modified_at": 2.0},
    ]
    diff = compute_diff(db_records, fs_files)
    assert len(diff["modified"]) == 1
    assert diff["modified"][0]["modified_at"] == 2.0


def test_mixed_changes():
    db_records = [
        {"file_path": "/keep.jpg", "file_size": 100, "modified_at": 1.0},
        {"file_path": "/delete.jpg", "file_size": 200, "modified_at": 2.0},
        {"file_path": "/update.jpg", "file_size": 300, "modified_at": 3.0},
    ]
    fs_files = [
        {"file_path": "/keep.jpg", "file_size": 100, "modified_at": 1.0},
        {"file_path": "/update.jpg", "file_size": 350, "modified_at": 4.0},
        {"file_path": "/new.jpg", "file_size": 400, "modified_at": 5.0},
    ]
    diff = compute_diff(db_records, fs_files)
    assert len(diff["added"]) == 1
    assert len(diff["deleted"]) == 1
    assert len(diff["modified"]) == 1
