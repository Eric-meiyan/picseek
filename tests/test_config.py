import os
import pytest
import yaml
from picseek.config import load_config, save_config, get_default_config, CONFIG_DIR


def test_get_default_config_has_required_keys():
    cfg = get_default_config()
    assert "formats" in cfg
    assert "default_limit" in cfg
    assert "db_path" in cfg
    assert "index_paths" in cfg


def test_default_formats_include_common_types():
    cfg = get_default_config()
    assert "jpg" in cfg["formats"]
    assert "png" in cfg["formats"]
    assert "webp" in cfg["formats"]


def test_save_and_load_config(tmp_path):
    config_path = tmp_path / "config.yaml"
    cfg = get_default_config()
    cfg["default_limit"] = 20
    save_config(cfg, str(config_path))
    loaded = load_config(str(config_path))
    assert loaded["default_limit"] == 20


def test_load_config_creates_default_if_missing(tmp_path):
    config_path = tmp_path / "nonexistent" / "config.yaml"
    cfg = load_config(str(config_path))
    assert cfg == get_default_config()
    assert config_path.exists()


def test_db_path_expands_tilde():
    cfg = get_default_config()
    assert "~" in cfg["db_path"]
