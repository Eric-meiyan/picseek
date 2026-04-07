import sys
from tqdm import tqdm
from picseek.scanner import scan_images
from picseek.sync import compute_diff
from picseek.db import Database
from picseek.model import get_model


def run_index(
    directory: str,
    db_path: str,
    formats: list[str],
    show_progress: bool = True,
) -> dict:
    db = Database(db_path)
    model = get_model()

    fs_files = scan_images(directory, formats)
    db_records = db.get_all_records()
    diff = compute_diff(db_records, fs_files)

    stats = {
        "new": 0,
        "updated": 0,
        "deleted": 0,
        "skipped": len(fs_files) - len(diff["added"]) - len(diff["modified"]),
        "errors": 0,
    }

    for record in diff["deleted"]:
        db.delete_image(record["file_path"])
        stats["deleted"] += 1

    to_process = diff["added"] + diff["modified"]
    iterator = tqdm(to_process, desc="Indexing", disable=not show_progress)

    for file_info in iterator:
        try:
            from PIL import Image as _Image
            _Image.open(file_info["file_path"]).verify()
            vec = model.encode_image(file_info["file_path"])
            if file_info in diff["added"]:
                db.insert_image(
                    file_info["file_path"],
                    file_info["file_size"],
                    file_info["modified_at"],
                    vec,
                )
                stats["new"] += 1
            else:
                db.update_image(
                    file_info["file_path"],
                    file_info["file_size"],
                    file_info["modified_at"],
                    vec,
                )
                stats["updated"] += 1
        except Exception as e:
            print(f"Warning: skipping {file_info['file_path']}: {e}", file=sys.stderr)
            stats["errors"] += 1

    db.close()
    return stats
