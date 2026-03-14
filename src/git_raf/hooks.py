"""Git hook installation for RAF governance enforcement."""

from __future__ import annotations

from pathlib import Path

from git_raf.git_ops import install_hook


PRECOMMIT_HOOK = """\
#!/bin/sh
# Git-RAF Pre-Commit Hook
# Validates staged changes against governance policies

if command -v git-raf >/dev/null 2>&1; then
    echo "Git-RAF: Validating staged changes..."
    git-raf validate
    exit $?
else
    echo "Git-RAF: git-raf not found on PATH, skipping validation."
fi
"""

POSTCOMMIT_HOOK = """\
#!/bin/sh
# Git-RAF Post-Commit Hook
# Logs governance audit record after commit

if command -v git-raf >/dev/null 2>&1; then
    echo "Git-RAF: Recording audit entry..."
    # Future: git-raf audit --record
fi
"""


def install_all_hooks(root: Path) -> list[str]:
    """Install all RAF git hooks. Returns list of installed hook names."""
    installed = []

    install_hook("pre-commit", PRECOMMIT_HOOK, cwd=root)
    installed.append("pre-commit")

    install_hook("post-commit", POSTCOMMIT_HOOK, cwd=root)
    installed.append("post-commit")

    return installed


def uninstall_hooks(root: Path) -> list[str]:
    """Remove RAF git hooks. Only removes hooks with RAF header comment."""
    removed = []
    hooks_dir = root / ".git" / "hooks"

    for hook_name in ["pre-commit", "post-commit"]:
        hook_path = hooks_dir / hook_name
        if hook_path.exists():
            content = hook_path.read_text(encoding="utf-8")
            if "Git-RAF" in content:
                hook_path.unlink()
                removed.append(hook_name)

    return removed
