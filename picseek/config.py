import os
from pathlib import Path
import yaml

CONFIG_DIR = os.path.expanduser("~/.picseek")
DEFAULT_CONFIG_PATH = os.path.join(CONFIG_DIR, "config.yaml")


def get_default_config() -> dict:
    return {
        "formats": ["jpg", "jpeg", "png", "webp", "bmp", "gif"],
        "default_limit": 10,
        "db_path": "~/.picseek/index.db",
        "index_paths": [],
    }


def save_config(config: dict, path: str | None = None) -> None:
    path = path or DEFAULT_CONFIG_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)


def load_config(path: str | None = None) -> dict:
    path = path or DEFAULT_CONFIG_PATH
    if not os.path.exists(path):
        cfg = get_default_config()
        save_config(cfg, path)
        return cfg
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    # Merge with defaults for any missing keys
    defaults = get_default_config()
    for key, value in defaults.items():
        if key not in cfg:
            cfg[key] = value
    return cfg


def get_db_path(config: dict) -> str:
    return os.path.expanduser(config["db_path"])
