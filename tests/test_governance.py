"""Tests for governance metadata generation."""

from pathlib import Path

import pytest

from git_raf.governance import (
    GovernanceVector,
    compute_aura_seal,
    compute_entropy_checksum,
    compute_governance_vector,
    generate_commit_trailers,
)


class TestGovernanceVector:
    def test_str(self):
        v = GovernanceVector(0.1, 0.2, 0.3)
        assert "attack_risk: 0.10" in str(v)
        assert "rollback_cost: 0.20" in str(v)
        assert "stability_impact: 0.30" in str(v)


class TestComputeGovernanceVector:
    def test_high_sinphase(self):
        v = compute_governance_vector(0.9)
        assert v.attack_risk == pytest.approx(0.1)
        assert v.stability_impact == pytest.approx(0.9)

    def test_low_sinphase(self):
        v = compute_governance_vector(0.1)
        assert v.attack_risk == pytest.approx(0.9)
        assert v.stability_impact == pytest.approx(0.1)

    def test_with_files(self):
        v = compute_governance_vector(0.5, ["a.py", "b.py", "c.py"])
        assert v.rollback_cost == pytest.approx(3 / 50.0)


class TestEntropyChecksum:
    def test_basic(self, tmp_path: Path):
        f1 = tmp_path / "a.txt"
        f1.write_text("hello")
        f2 = tmp_path / "b.txt"
        f2.write_text("world")

        checksum = compute_entropy_checksum(["a.txt", "b.txt"], tmp_path)
        assert len(checksum) == 64  # SHA3-256 hex digest

    def test_empty(self, tmp_path: Path):
        checksum = compute_entropy_checksum([], tmp_path)
        assert len(checksum) == 64

    def test_deterministic(self, tmp_path: Path):
        f1 = tmp_path / "test.txt"
        f1.write_text("deterministic")

        c1 = compute_entropy_checksum(["test.txt"], tmp_path)
        c2 = compute_entropy_checksum(["test.txt"], tmp_path)
        assert c1 == c2


class TestAuraSeal:
    def test_seal_and_verify(self):
        seal = compute_aura_seal("abc123", "2025-01-01T00:00:00Z", "stable", "1.0.0")
        assert len(seal) == 64  # SHA-256 hex

    def test_different_inputs_different_seals(self):
        s1 = compute_aura_seal("abc", "t1", "stable", "1.0.0")
        s2 = compute_aura_seal("def", "t1", "stable", "1.0.0")
        assert s1 != s2


class TestCommitTrailers:
    def test_basic_trailers(self, tmp_path: Path):
        (tmp_path / "file.py").write_text("code")

        trailers = generate_commit_trailers(
            policy_tag="stable",
            governance_ref="test_policy.rift.gov",
            staged_files=["file.py"],
            root=tmp_path,
        )
        assert "Policy-Tag: stable" in trailers
        assert "Governance-Ref: test_policy.rift.gov" in trailers
        assert "Entropy-Checksum:" in trailers
        assert "Governance-Vector:" in trailers

    def test_signed_trailers(self, tmp_path: Path):
        (tmp_path / "file.py").write_text("code")

        trailers = generate_commit_trailers(
            policy_tag="stable",
            governance_ref="test.rift.gov",
            staged_files=["file.py"],
            root=tmp_path,
            sign=True,
        )
        assert "AuraSeal:" in trailers
