"""Tests for git hook installation."""

from pathlib import Path

from git_raf.hooks import POSTCOMMIT_HOOK, PRECOMMIT_HOOK, install_all_hooks, uninstall_hooks


class TestInstallHooks:
    def test_install(self, tmp_git_repo: Path):
        installed = install_all_hooks(tmp_git_repo)
        assert "pre-commit" in installed
        assert "post-commit" in installed

        hooks_dir = tmp_git_repo / ".git" / "hooks"
        assert (hooks_dir / "pre-commit").exists()
        assert (hooks_dir / "post-commit").exists()

    def test_hook_content(self, tmp_git_repo: Path):
        install_all_hooks(tmp_git_repo)
        hooks_dir = tmp_git_repo / ".git" / "hooks"

        pre = (hooks_dir / "pre-commit").read_text()
        assert "Git-RAF" in pre
        assert "git-raf validate" in pre

    def test_uninstall(self, tmp_git_repo: Path):
        install_all_hooks(tmp_git_repo)
        removed = uninstall_hooks(tmp_git_repo)
        assert "pre-commit" in removed
        assert "post-commit" in removed

        hooks_dir = tmp_git_repo / ".git" / "hooks"
        assert not (hooks_dir / "pre-commit").exists()
        assert not (hooks_dir / "post-commit").exists()
