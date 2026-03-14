"""Semantic versioning for RAF tags.

Ported from scripts/git-raf.sh: version parsing, bumping, and tag formatting.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from git_raf.git_ops import GitError, diff_names, last_tag


@dataclass
class SemVer:
    """Semantic version with major.minor.patch components."""
    major: int = 0
    minor: int = 0
    patch: int = 0

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"


def parse_version(tag_str: str) -> SemVer:
    """Extract SemVer from a tag string like 'raf-v1.2.3-stable' or 'v1.2.3'."""
    match = re.search(r"(\d+)\.(\d+)\.(\d+)", tag_str)
    if not match:
        return SemVer()
    return SemVer(
        major=int(match.group(1)),
        minor=int(match.group(2)),
        patch=int(match.group(3)),
    )


def bump(version: SemVer, level: str) -> SemVer:
    """Increment version by the given level (major, minor, or patch)."""
    if level == "major":
        return SemVer(major=version.major + 1, minor=0, patch=0)
    elif level == "minor":
        return SemVer(major=version.major, minor=version.minor + 1, patch=0)
    else:
        return SemVer(major=version.major, minor=version.minor, patch=version.patch + 1)


def determine_bump(
    root: Path,
    rules: dict[str, list[str]] | None = None,
) -> str:
    """Determine version bump level based on changed files.

    Rules map bump levels to path prefix lists. Files matching a 'major'
    prefix trigger a major bump, 'minor' prefixes trigger minor, else patch.
    """
    if rules is None:
        rules = {"major": ["include/"], "minor": ["src/core/"]}

    tag = last_tag()
    if tag is None:
        # No previous tags -- check all files
        from git_raf.git_ops import ls_files
        changed = ls_files()
    else:
        changed = diff_names(tag, "HEAD")

    if not changed:
        return "patch"

    for filepath in changed:
        for prefix in rules.get("major", []):
            if filepath.startswith(prefix):
                return "major"

    for filepath in changed:
        for prefix in rules.get("minor", []):
            if filepath.startswith(prefix):
                return "minor"

    return "patch"


def get_current_version() -> SemVer:
    """Get the current version from the latest tag."""
    tag = last_tag()
    if tag is None:
        return SemVer()
    return parse_version(tag)


def format_tag(prefix: str, version: str, stability: str, fmt: str) -> str:
    """Format a tag name using the configured format string."""
    return fmt.format(prefix=prefix, version=version, stability=stability)
