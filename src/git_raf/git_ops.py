"""Thin wrapper around git subprocess calls."""

from __future__ import annotations

import subprocess
from pathlib import Path


class GitError(Exception):
    """Raised when a git command fails."""


def _run(args: list[str], cwd: Path | None = None, check: bool = True) -> str:
    """Run a git command and return stdout."""
    try:
        result = subprocess.run(
            ["git", *args],
            capture_output=True,
            text=True,
            cwd=cwd,
            check=check,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as exc:
        raise GitError(exc.stderr.strip() or str(exc)) from exc


def git_root(cwd: Path | None = None) -> Path:
    """Return the root directory of the current git repository."""
    out = _run(["rev-parse", "--show-toplevel"], cwd=cwd)
    return Path(out)


def is_git_repo(cwd: Path | None = None) -> bool:
    """Check if the current directory is inside a git repository."""
    try:
        _run(["rev-parse", "--is-inside-work-tree"], cwd=cwd)
        return True
    except GitError:
        return False


def current_branch(cwd: Path | None = None) -> str:
    """Return the name of the current branch."""
    return _run(["rev-parse", "--abbrev-ref", "HEAD"], cwd=cwd)


def staged_files(cwd: Path | None = None) -> list[str]:
    """Return list of staged file paths."""
    out = _run(["diff", "--cached", "--name-only"], cwd=cwd)
    if not out:
        return []
    return out.splitlines()


def diff_names(ref1: str, ref2: str = "HEAD", cwd: Path | None = None) -> list[str]:
    """Return files changed between two refs."""
    out = _run(["diff", "--name-only", ref1, ref2], cwd=cwd, check=False)
    if not out:
        return []
    return out.splitlines()


def last_tag(cwd: Path | None = None) -> str | None:
    """Return the most recent tag, or None if no tags exist."""
    try:
        return _run(["describe", "--tags", "--abbrev=0"], cwd=cwd)
    except GitError:
        return None


def head_hash(cwd: Path | None = None, short: bool = False) -> str:
    """Return the commit hash of HEAD."""
    args = ["rev-parse"]
    if short:
        args.append("--short")
    args.append("HEAD")
    return _run(args, cwd=cwd)


def create_tag(name: str, message: str, cwd: Path | None = None) -> None:
    """Create an annotated git tag."""
    _run(["tag", "-a", name, "-m", message], cwd=cwd)


def commit(message: str, cwd: Path | None = None) -> str:
    """Run git commit with the given message. Returns the new commit hash."""
    _run(["commit", "-m", message], cwd=cwd)
    return head_hash(cwd=cwd)


def ls_files(cwd: Path | None = None) -> list[str]:
    """Return all tracked files."""
    out = _run(["ls-files"], cwd=cwd)
    if not out:
        return []
    return out.splitlines()


def install_hook(hook_name: str, content: str, cwd: Path | None = None) -> Path:
    """Write a git hook script. Returns the hook file path."""
    root = git_root(cwd)
    hook_path = root / ".git" / "hooks" / hook_name
    hook_path.write_text(content, encoding="utf-8")
    hook_path.chmod(0o755)
    return hook_path
