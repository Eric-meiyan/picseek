import os


def scan_images(directory: str, formats: list[str]) -> list[dict]:
    if not os.path.isdir(directory):
        raise FileNotFoundError(f"Directory not found: {directory}")

    formats_lower = {f.lower().lstrip(".") for f in formats}
    results = []

    for entry in _walk_entries(directory):
        ext = entry.name.rsplit(".", 1)[-1].lower() if "." in entry.name else ""
        if ext in formats_lower:
            stat = entry.stat()
            results.append({
                "file_path": entry.path,
                "file_size": stat.st_size,
                "modified_at": stat.st_mtime,
            })

    return results


def _walk_entries(directory: str):
    try:
        with os.scandir(directory) as it:
            for entry in it:
                if entry.is_file(follow_symlinks=False):
                    yield entry
                elif entry.is_dir(follow_symlinks=False):
                    yield from _walk_entries(entry.path)
    except PermissionError:
        pass
