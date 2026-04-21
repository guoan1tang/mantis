"""Configuration management."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class CaptureConfig:
    max_flows: int = 10000
    max_body_size: int = 1048576
    default_domains: list[str] = field(default_factory=list)


@dataclass
class ProxyConfig:
    listen_host: str = "0.0.0.0"
    listen_port: int = 8080
    auto_system_proxy: bool = True


@dataclass
class LLMConfig:
    api_key: str = ""
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-4o"


@dataclass
class MemoryConfig:
    working_window_size: int = 20
    consolidation_interval: int = 15
    semantic_confidence_threshold: float = 0.7
    stale_memory_days: int = 7
    memory_dir: str = str(Path.home() / ".agent-proxy" / "memory")


@dataclass
class AppConfig:
    proxy: ProxyConfig = field(default_factory=ProxyConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    capture: CaptureConfig = field(default_factory=CaptureConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)

    @classmethod
    def from_yaml(cls, path: str | Path | None = None) -> AppConfig:
        """Load config from YAML file."""
        import yaml

        config_path = Path(path) if path else _default_config_path()
        if config_path.exists():
            with open(config_path) as f:
                data = yaml.safe_load(f)
            return _dict_to_config(data)
        return cls()

    def save(self, path: str | Path | None = None) -> None:
        """Save config to YAML."""
        import yaml

        config_path = Path(path) if path else _default_config_path()
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w") as f:
            yaml.dump(_config_to_dict(self), f, default_flow_style=False)


def _default_config_path() -> Path:
    return Path.home() / ".agent-proxy" / "config.yaml"


def _dict_to_config(data: dict) -> AppConfig:
    config = AppConfig()
    if "proxy" in data:
        config.proxy = ProxyConfig(**{k: v for k, v in data["proxy"].items() if hasattr(config.proxy, k)})
    if "llm" in data:
        config.llm = LLMConfig(**{k: v for k, v in data["llm"].items() if hasattr(config.llm, k)})
    if "capture" in data:
        config.capture = CaptureConfig(**{k: v for k, v in data["capture"].items() if hasattr(config.capture, k)})
    if "memory" in data:
        config.memory = MemoryConfig(**{k: v for k, v in data["memory"].items() if hasattr(config.memory, k)})
    return config


def _config_to_dict(config: AppConfig) -> dict:
    return {
        "proxy": {
            "listen_host": config.proxy.listen_host,
            "listen_port": config.proxy.listen_port,
            "auto_system_proxy": config.proxy.auto_system_proxy,
        },
        "llm": {
            "api_key": config.llm.api_key,
            "base_url": config.llm.base_url,
            "model": config.llm.model,
        },
        "capture": {
            "max_flows": config.capture.max_flows,
            "max_body_size": config.capture.max_body_size,
            "default_domains": config.capture.default_domains,
        },
        "memory": {
            "working_window_size": config.memory.working_window_size,
            "consolidation_interval": config.memory.consolidation_interval,
            "semantic_confidence_threshold": config.memory.semantic_confidence_threshold,
            "stale_memory_days": config.memory.stale_memory_days,
            "memory_dir": config.memory.memory_dir,
        },
    }
