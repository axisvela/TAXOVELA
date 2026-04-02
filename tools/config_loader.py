"""
config_loader.py — ArchHarness 共用配置加载器

所有 Python 工具通过此模块读取 config.yaml，避免硬编码公司专属信息。

使用方式:
    from config_loader import load_config, find_config

    cfg = load_config()                   # 自动向上查找 config.yaml
    cfg = load_config("/path/to/config.yaml")  # 指定路径

    # 读取配置项
    dc_list   = cfg.datacenters           # list[dict]
    api_gw    = cfg.platforms.api_gateway # str
    input_dir = cfg.paths.input_dir       # Path
    output_dir= cfg.paths.output_dir      # Path
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as e:
    raise ImportError("pyyaml is required: pip install pyyaml") from e


# ──────────────────────────────────────────────────────────────────
# Data classes（只暴露常用字段，raw dict 始终可通过 .raw 访问）
# ──────────────────────────────────────────────────────────────────

@dataclass
class CompanyConfig:
    name: str = "Acme Corp"
    classification_prefix: str = "Acme"


@dataclass
class DatacenterConfig:
    id: str = ""
    aliases: list[str] = field(default_factory=list)
    location: dict[str, str] = field(default_factory=dict)
    model: str = "two-tier"
    zones: list[str] = field(default_factory=list)
    region: str = ""
    notes: str = ""

    @property
    def display_name(self) -> str:
        """Return the first alias, falling back to id."""
        return self.aliases[0] if self.aliases else self.id

    @property
    def city(self) -> str:
        return self.location.get("city", "")

    @property
    def country(self) -> str:
        return self.location.get("country", "")


@dataclass
class PlatformConfig:
    api_gateway: str = "API Gateway"
    message_bus: str = "Message Bus"
    k8s_platform: str = "K8s Platform"
    integration_platforms: list[str] = field(default_factory=list)
    auth_internal: str = "ADFS"
    auth_external: str = "Enterprise ID"
    authz_platform: str = "AuthZ Platform"


@dataclass
class PathsConfig:
    _root: Path = field(default_factory=Path.cwd, repr=False)
    input_dir: str = "./input"
    output_dir: str = "./output"
    standards_dir: str = "./standards"

    def _resolve(self, rel: str) -> Path:
        p = Path(rel)
        return p if p.is_absolute() else (self._root / p).resolve()

    @property
    def input_path(self) -> Path:
        return self._resolve(self.input_dir)

    @property
    def output_path(self) -> Path:
        return self._resolve(self.output_dir)

    @property
    def standards_path(self) -> Path:
        return self._resolve(self.standards_dir)

    def ensure_dirs(self) -> None:
        """Create input and output directories if they don't exist."""
        self.input_path.mkdir(parents=True, exist_ok=True)
        self.output_path.mkdir(parents=True, exist_ok=True)


@dataclass
class ArchConfig:
    """Top-level configuration object."""
    company: CompanyConfig = field(default_factory=CompanyConfig)
    datacenters: list[DatacenterConfig] = field(default_factory=list)
    platforms: PlatformConfig = field(default_factory=PlatformConfig)
    paths: PathsConfig = field(default_factory=PathsConfig)
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    # ── Convenience helpers ───────────────────────────────
    def dc_by_id(self, dc_id: str) -> DatacenterConfig | None:
        return next((d for d in self.datacenters if d.id == dc_id), None)

    def dc_by_alias(self, alias: str) -> DatacenterConfig | None:
        """Case-insensitive alias lookup."""
        alias_lower = alias.lower()
        for dc in self.datacenters:
            if any(a.lower() == alias_lower for a in dc.aliases):
                return dc
        return None

    def integration_platform_names(self) -> list[str]:
        """Flat list of all integration platform names for rules checking."""
        return list(self.platforms.integration_platforms)

    def classification(self, level: str = "Internal") -> str:
        """e.g. classification('Confidential') → 'Acme Confidential'"""
        return f"{self.company.classification_prefix} {level}"


# ──────────────────────────────────────────────────────────────────
# Loader
# ──────────────────────────────────────────────────────────────────

def find_config(start: Path | str | None = None) -> Path | None:
    """
    Walk up from `start` (default: cwd) looking for config.yaml.
    Returns the first match or None.
    """
    current = Path(start).resolve() if start else Path.cwd().resolve()
    for directory in [current, *current.parents]:
        candidate = directory / "config.yaml"
        if candidate.exists():
            return candidate
    return None


def load_config(config_path: Path | str | None = None) -> ArchConfig:
    """
    Load ArchHarness configuration.

    Resolution order:
      1. Explicit `config_path` argument
      2. ARCH_CONFIG env var
      3. Auto-discover by walking up from cwd (find_config)
      4. Return default config with a warning
    """
    # 1. Explicit path
    if config_path:
        path = Path(config_path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"config.yaml not found at: {path}")
        return _parse(path)

    # 2. Environment variable
    env_path = os.environ.get("ARCH_CONFIG")
    if env_path:
        path = Path(env_path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"ARCH_CONFIG points to missing file: {path}")
        return _parse(path)

    # 3. Auto-discover
    discovered = find_config()
    if discovered:
        return _parse(discovered)

    # 4. Defaults (warn but don't crash)
    import warnings
    warnings.warn(
        "config.yaml not found — using built-in defaults. "
        "Company-specific values (DC names, platform names) will be generic. "
        "Create config.yaml at the project root to customise.",
        UserWarning,
        stacklevel=2,
    )
    return ArchConfig()


def _parse(path: Path) -> ArchConfig:
    root = path.parent
    with open(path, encoding="utf-8") as f:
        raw: dict[str, Any] = yaml.safe_load(f) or {}

    # company
    c = raw.get("company", {})
    company = CompanyConfig(
        name=c.get("name", "Acme Corp"),
        classification_prefix=c.get("classification_prefix", c.get("name", "Acme")),
    )

    # datacenters
    dcs: list[DatacenterConfig] = []
    for d in raw.get("datacenters", []):
        dcs.append(DatacenterConfig(
            id=d.get("id", ""),
            aliases=d.get("aliases", []),
            location=d.get("location", {}),
            model=d.get("model", "two-tier"),
            zones=d.get("zones", []),
            region=d.get("region", ""),
            notes=d.get("notes", ""),
        ))

    # platforms
    p = raw.get("platforms", {})
    platforms = PlatformConfig(
        api_gateway=p.get("api_gateway", "API Gateway"),
        message_bus=p.get("message_bus", "Message Bus"),
        k8s_platform=p.get("k8s_platform", "K8s Platform"),
        integration_platforms=p.get("integration_platforms", [
            p.get("api_gateway", "API Gateway"),
            p.get("message_bus", "Message Bus"),
        ]),
        auth_internal=p.get("auth_internal", "ADFS"),
        auth_external=p.get("auth_external", "Enterprise ID"),
        authz_platform=p.get("authz_platform", "AuthZ Platform"),
    )

    # paths
    pa = raw.get("paths", {})
    paths = PathsConfig(
        _root=root,
        input_dir=pa.get("input_dir", "./input"),
        output_dir=pa.get("output_dir", "./output"),
        standards_dir=pa.get("standards_dir", "./standards"),
    )

    return ArchConfig(
        company=company,
        datacenters=dcs,
        platforms=platforms,
        paths=paths,
        raw=raw,
    )
