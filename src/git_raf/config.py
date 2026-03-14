"""RAF configuration management via .raf/config.toml."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ImportError:
        tomllib = None  # type: ignore[assignment]


CONFIG_DIR = ".raf"
CONFIG_FILE = "config.toml"

DEFAULT_CONFIG_TOML = """\
# Git-RAF Configuration
# Regulation As Firmware - governance-integrated version control

[raf]
sinphase_threshold = 0.5
tag_prefix = "raf"
tag_format = "{prefix}-v{version}-{stability}"
governance_ref = "default_policy.rift.gov"
entropy_threshold = 0.05

[raf.artifacts]
# Glob patterns for build artifacts to verify
patterns = []

[raf.branch_policies]
main = "maximum"
release = "high"
develop = "standard"
feature = "moderate"
experimental = "minimal"

[raf.version_bump_rules]
# Path prefixes that trigger major/minor bumps (everything else is patch)
major = ["include/"]
minor = ["src/core/"]
"""


@dataclass
class RAFConfig:
    """Holds RAF configuration values."""

    sinphase_threshold: float = 0.5
    tag_prefix: str = "raf"
    tag_format: str = "{prefix}-v{version}-{stability}"
    governance_ref: str = "default_policy.rift.gov"
    entropy_threshold: float = 0.05
    artifact_patterns: list[str] = field(default_factory=list)
    branch_policies: dict[str, str] = field(default_factory=lambda: {
        "main": "maximum",
        "release": "high",
        "develop": "standard",
        "feature": "moderate",
        "experimental": "minimal",
    })
    version_bump_rules: dict[str, list[str]] = field(default_factory=lambda: {
        "major": ["include/"],
        "minor": ["src/core/"],
    })

    @classmethod
    def load(cls, repo_root: Path) -> RAFConfig:
        """Load configuration from .raf/config.toml."""
        config_path = repo_root / CONFIG_DIR / CONFIG_FILE
        if not config_path.exists():
            return cls()

        if tomllib is None:
            # Fallback: return defaults if no TOML parser available
            return cls()

        with open(config_path, "rb") as f:
            data = tomllib.load(f)

        raf = data.get("raf", {})
        artifacts = raf.get("artifacts", {})
        branch_policies = raf.get("branch_policies", {})
        bump_rules = raf.get("version_bump_rules", {})

        return cls(
            sinphase_threshold=raf.get("sinphase_threshold", 0.5),
            tag_prefix=raf.get("tag_prefix", "raf"),
            tag_format=raf.get("tag_format", "{prefix}-v{version}-{stability}"),
            governance_ref=raf.get("governance_ref", "default_policy.rift.gov"),
            entropy_threshold=raf.get("entropy_threshold", 0.05),
            artifact_patterns=artifacts.get("patterns", []),
            branch_policies=branch_policies if branch_policies else cls().branch_policies,
            version_bump_rules=bump_rules if bump_rules else cls().version_bump_rules,
        )

    @staticmethod
    def init(repo_root: Path) -> Path:
        """Create .raf/config.toml with defaults. Returns the config file path."""
        raf_dir = repo_root / CONFIG_DIR
        raf_dir.mkdir(exist_ok=True)
        config_path = raf_dir / CONFIG_FILE
        config_path.write_text(DEFAULT_CONFIG_TOML, encoding="utf-8")
        return config_path

    @staticmethod
    def is_initialized(repo_root: Path) -> bool:
        """Check if RAF has been initialized in the repo."""
        return (repo_root / CONFIG_DIR / CONFIG_FILE).exists()
