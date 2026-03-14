"""Tests for RAF configuration management."""

from pathlib import Path

from git_raf.config import RAFConfig


class TestRAFConfig:
    def test_defaults(self):
        config = RAFConfig()
        assert config.sinphase_threshold == 0.5
        assert config.tag_prefix == "raf"
        assert config.governance_ref == "default_policy.rift.gov"

    def test_init_creates_files(self, tmp_path: Path):
        config_path = RAFConfig.init(tmp_path)
        assert config_path.exists()
        assert (tmp_path / ".raf" / "config.toml").exists()

    def test_is_initialized(self, tmp_path: Path):
        assert not RAFConfig.is_initialized(tmp_path)
        RAFConfig.init(tmp_path)
        assert RAFConfig.is_initialized(tmp_path)

    def test_load_defaults(self, tmp_path: Path):
        RAFConfig.init(tmp_path)
        config = RAFConfig.load(tmp_path)
        assert config.sinphase_threshold == 0.5
        assert config.tag_prefix == "raf"

    def test_load_missing(self, tmp_path: Path):
        config = RAFConfig.load(tmp_path)
        assert config.sinphase_threshold == 0.5  # Returns defaults
