# picseek/sync.py


def compute_diff(
    db_records: list[dict], fs_files: list[dict]
) -> dict[str, list[dict]]:
    db_map = {r["file_path"]: r for r in db_records}
    fs_map = {f["file_path"]: f for f in fs_files}

    added = []
    modified = []
    deleted = []

    for path, fs_info in fs_map.items():
        if path not in db_map:
            added.append(fs_info)
        elif fs_info["modified_at"] != db_map[path]["modified_at"]:
            modified.append(fs_info)

    for path, db_info in db_map.items():
        if path not in fs_map:
            deleted.append(db_info)

    return {"added": added, "deleted": deleted, "modified": modified}
