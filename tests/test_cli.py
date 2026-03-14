"""Integration tests for the CLI entry point."""

import os
import subprocess
from pathlib import Path

from click.testing import CliRunner

from git_raf.cli import main


class TestCLIHelp:
    def test_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Regulation As Firmware" in result.output

    def test_version(self):
        runner = CliRunner()
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output


class TestInitCommand:
    def test_init(self, tmp_git_repo: Path):
        runner = CliRunner()
        os.chdir(tmp_git_repo)
        result = runner.invoke(main, ["init"])
        assert result.exit_code == 0
        assert "RAF initialized" in result.output
        assert (tmp_git_repo / ".raf" / "config.toml").exists()

    def test_init_already_initialized(self, raf_initialized_repo: Path):
        runner = CliRunner()
        os.chdir(raf_initialized_repo)
        result = runner.invoke(main, ["init"])
        assert result.exit_code == 0
        assert "already initialized" in result.output


class TestStatusCommand:
    def test_status_no_raf(self, tmp_git_repo: Path):
        runner = CliRunner()
        os.chdir(tmp_git_repo)
        result = runner.invoke(main, ["status"])
        assert result.exit_code == 0
        assert "not initialized" in result.output

    def test_status_with_raf(self, raf_initialized_repo: Path):
        runner = CliRunner()
        os.chdir(raf_initialized_repo)
        result = runner.invoke(main, ["status"])
        assert result.exit_code == 0
        assert "Sinphase threshold" in result.output
        assert "Tag prefix" in result.output
