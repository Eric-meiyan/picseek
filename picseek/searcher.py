import sys
from picseek.db import Database
from picseek.model import get_model
from picseek.scanner import scan_images
from picseek.sync import compute_diff


def run_search(
    query: str,
    db_path: str,
    limit: int = 10,
    sync: bool = True,
    index_paths: list[str] | None = None,
    formats: list[str] | None = None,
) -> list[dict]:
    db = Database(db_path)
    model = get_model()

    if sync and index_paths and formats:
        _sync_before_search(db, model, index_paths, formats)

    records = db.get_all_records()
    if not records:
        db.close()
        return []

    query_vec = model.encode_text(query)
    raw_results = db.search(query_vec, limit=limit)
    db.close()

    results = []
    for r in raw_results:
        distance = r["distance"]
        score = max(0.0, 1.0 - distance * distance / 2.0)
        results.append({
            "file_path": r["file_path"],
            "score": round(score, 4),
        })

    return results


def _sync_before_search(db, model, index_paths, formats):
    all_fs_files = []
    for path in index_paths:
        try:
            all_fs_files.extend(scan_images(path, formats))
        except FileNotFoundError:
            print(f"Warning: index path not found: {path}", file=sys.stderr)

    db_records = db.get_all_records()
    diff = compute_diff(db_records, all_fs_files)

    for record in diff["deleted"]:
        db.delete_image(record["file_path"])

    for file_info in diff["added"]:
        try:
            vec = model.encode_image(file_info["file_path"])
            db.insert_image(file_info["file_path"], file_info["file_size"], file_info["modified_at"], vec)
        except Exception:
            pass

    for file_info in diff["modified"]:
        try:
            vec = model.encode_image(file_info["file_path"])
            db.update_image(file_info["file_path"], file_info["file_size"], file_info["modified_at"], vec)
        except Exception:
            pass
