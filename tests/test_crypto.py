"""Tests for cryptographic operations."""

from pathlib import Path

import pytest

from git_raf.crypto import (
    entropy_checksum,
    generate_aura_seal,
    generate_keypair,
    load_private_key,
    load_public_key,
    sign_message,
    verify_aura_seal,
    verify_signature,
)


class TestKeypairGeneration:
    def test_generate(self, tmp_path: Path):
        result = generate_keypair(str(tmp_path))
        assert result["private"].exists()
        assert result["public"].exists()

    def test_load_keys(self, tmp_path: Path):
        generate_keypair(str(tmp_path))
        priv = load_private_key(tmp_path / "raf_ed25519")
        pub = load_public_key(tmp_path / "raf_ed25519.pub")
        assert priv is not None
        assert pub is not None


class TestSignVerify:
    def test_roundtrip(self, tmp_path: Path):
        generate_keypair(str(tmp_path))

        message = b"test governance data"
        sig = sign_message(message, tmp_path / "raf_ed25519")
        assert verify_signature(message, sig, tmp_path / "raf_ed25519.pub")

    def test_bad_signature(self, tmp_path: Path):
        generate_keypair(str(tmp_path))

        message = b"test governance data"
        sig = sign_message(message, tmp_path / "raf_ed25519")
        assert not verify_signature(b"wrong data", sig, tmp_path / "raf_ed25519.pub")

    def test_missing_key(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError):
            sign_message(b"test", tmp_path / "nonexistent")


class TestEntropyChecksum:
    def test_basic(self, tmp_path: Path):
        f = tmp_path / "test.bin"
        f.write_bytes(b"\x00\x01\x02")

        result = entropy_checksum([f])
        assert len(result) == 64

    def test_deterministic(self, tmp_path: Path):
        f = tmp_path / "test.txt"
        f.write_text("hello")

        r1 = entropy_checksum([f])
        r2 = entropy_checksum([f])
        assert r1 == r2

    def test_empty(self):
        result = entropy_checksum([])
        assert len(result) == 64


class TestAuraSeal:
    def test_generate_and_verify(self):
        seal = generate_aura_seal("ec123", "2025-01-01T00:00:00Z", "stable", "1.0.0")
        assert verify_aura_seal(seal, "ec123", "2025-01-01T00:00:00Z", "stable", "1.0.0")

    def test_tampered_seal(self):
        seal = generate_aura_seal("ec123", "2025-01-01T00:00:00Z", "stable", "1.0.0")
        assert not verify_aura_seal(
            "tampered" + seal[8:], "ec123", "2025-01-01T00:00:00Z", "stable", "1.0.0"
        )

    def test_with_key_material(self):
        key = b"custom-key-material"
        seal = generate_aura_seal("ec", "ts", "stable", "1.0.0", key_material=key)
        assert verify_aura_seal(seal, "ec", "ts", "stable", "1.0.0", key_material=key)
        assert not verify_aura_seal(seal, "ec", "ts", "stable", "1.0.0")
