"""Shared test fixtures for git-raf tests."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def tmp_git_repo(tmp_path: Path) -> Path:
    """Create a temporary git repository with an initial commit."""
    subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=tmp_path, check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=tmp_path, check=True, capture_output=True,
    )

    # Create initial commit
    readme = tmp_path / "README.md"
    readme.write_text("# Test Repo\n")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "initial commit"],
        cwd=tmp_path, check=True, capture_output=True,
    )

    return tmp_path


@pytest.fixture
def raf_initialized_repo(tmp_git_repo: Path) -> Path:
    """A git repo with RAF initialized (.raf/config.toml exists)."""
    from git_raf.config import RAFConfig
    RAFConfig.init(tmp_git_repo)
    return tmp_git_repo
