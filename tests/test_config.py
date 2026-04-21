"""Tests for config management."""
import tempfile
from pathlib import Path

from agent_proxy.core.config import AppConfig


def test_default_config():
    config = AppConfig()
    assert config.proxy.listen_port == 8080
    assert config.capture.max_flows == 10000


def test_config_round_trip():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "config.yaml"
        config = AppConfig()
        config.proxy.listen_port = 9090
        config.save(path)

        loaded = AppConfig.from_yaml(path)
        assert loaded.proxy.listen_port == 9090


def test_config_from_yaml():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "config.yaml"
        path.write_text("proxy:\n  listen_port: 3000\n")
        config = AppConfig.from_yaml(path)
        assert config.proxy.listen_port == 3000
