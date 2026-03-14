"""Cryptographic operations for RAF: Ed25519 signing, SHA3-256, AuraSeal.

Implements the cryptographic framework from the RAF specification:
- Ed25519 keypair generation and signing
- SHA3-256 entropy checksums
- AuraSeal generation and verification
"""

from __future__ import annotations

import hashlib
import hmac
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)


DEFAULT_KEY_DIR = Path.home() / ".raf" / "keys"


def generate_keypair(output_dir: str | None = None) -> dict[str, Path]:
    """Generate Ed25519 keypair and save to disk.

    Returns dict with 'private' and 'public' key file paths.
    """
    key_dir = Path(output_dir) if output_dir else DEFAULT_KEY_DIR
    key_dir.mkdir(parents=True, exist_ok=True)

    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    private_path = key_dir / "raf_ed25519"
    public_path = key_dir / "raf_ed25519.pub"

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    private_path.write_bytes(private_pem)

    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    public_path.write_bytes(public_pem)

    return {"private": private_path, "public": public_path}


def load_private_key(path: Path | None = None) -> Ed25519PrivateKey:
    """Load Ed25519 private key from PEM file."""
    if path is None:
        path = DEFAULT_KEY_DIR / "raf_ed25519"

    if not path.exists():
        raise FileNotFoundError(
            f"Private key not found at {path}. Run 'git raf keygen' first."
        )

    pem_data = path.read_bytes()
    key = serialization.load_pem_private_key(pem_data, password=None)
    if not isinstance(key, Ed25519PrivateKey):
        raise ValueError("Key is not Ed25519")
    return key


def load_public_key(path: Path | None = None) -> Ed25519PublicKey:
    """Load Ed25519 public key from PEM file."""
    if path is None:
        path = DEFAULT_KEY_DIR / "raf_ed25519.pub"

    if not path.exists():
        raise FileNotFoundError(f"Public key not found at {path}.")

    pem_data = path.read_bytes()
    key = serialization.load_pem_public_key(pem_data)
    if not isinstance(key, Ed25519PublicKey):
        raise ValueError("Key is not Ed25519")
    return key


def sign_message(message: bytes, private_key_path: Path | None = None) -> bytes:
    """Sign a message with Ed25519. Returns raw signature bytes."""
    key = load_private_key(private_key_path)
    return key.sign(message)


def verify_signature(
    message: bytes,
    signature: bytes,
    public_key_path: Path | None = None,
) -> bool:
    """Verify an Ed25519 signature. Returns True if valid."""
    key = load_public_key(public_key_path)
    try:
        key.verify(signature, message)
        return True
    except Exception:
        return False


def entropy_checksum(file_paths: list[str | Path]) -> str:
    """Compute SHA3-256 entropy checksum over a set of files.

    Hashes each file individually, then hashes the concatenated hashes.
    """
    combined = ""
    for fp in sorted(str(p) for p in file_paths):
        path = Path(fp)
        if path.exists() and path.is_file():
            data = path.read_bytes()
            combined += hashlib.sha3_256(data).hexdigest()

    if not combined:
        combined = "empty"

    return hashlib.sha3_256(combined.encode("utf-8")).hexdigest()


def generate_aura_seal(
    entropy_checksum_val: str,
    timestamp: str,
    stability: str,
    version: str,
    key_material: bytes | None = None,
) -> str:
    """Generate AuraSeal as HMAC-SHA256 over governance data.

    If key_material is provided (from a private key), it's used as the
    HMAC key. Otherwise uses a default key for unsigned seals.
    """
    if key_material is None:
        key_material = b"git-raf-governance"

    content = f"{entropy_checksum_val}{timestamp}{stability}{version}"
    seal = hmac.new(
        key=key_material,
        msg=content.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()
    return seal


def verify_aura_seal(
    seal: str,
    entropy_checksum_val: str,
    timestamp: str,
    stability: str,
    version: str,
    key_material: bytes | None = None,
) -> bool:
    """Verify an AuraSeal by recomputing and comparing."""
    expected = generate_aura_seal(
        entropy_checksum_val, timestamp, stability, version, key_material
    )
    return hmac.compare_digest(seal, expected)


def generate_aura_seal_for_commit(
    commit_ref: str,
    config: object,
    root: Path,
) -> str:
    """Generate AuraSeal for an existing commit."""
    from datetime import datetime, timezone
    from git_raf.git_ops import head_hash

    commit_hash = head_hash() if commit_ref == "HEAD" else commit_ref
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Compute entropy over tracked files
    from git_raf.git_ops import ls_files
    files = ls_files()
    file_paths = [root / f for f in files]
    ec = entropy_checksum(file_paths)

    seal = generate_aura_seal(ec, timestamp, "stable", commit_hash[:16])
    return seal


def verify_aura_seal_for_commit(
    commit_ref: str,
    config: object,
    root: Path,
) -> dict:
    """Verify AuraSeal on a commit by checking trailers."""
    from git_raf.git_ops import _run

    try:
        message = _run(["log", "-1", "--format=%B", commit_ref])
    except Exception as e:
        return {"valid": False, "reason": str(e)}

    # Parse trailers from commit message
    trailers: dict[str, str] = {}
    for line in message.splitlines():
        if ": " in line:
            key, _, value = line.partition(": ")
            key = key.strip()
            if key in ("AuraSeal", "Entropy-Checksum", "RAF-Timestamp",
                        "Policy-Tag", "Governance-Ref"):
                trailers[key] = value.strip()

    if "AuraSeal" not in trailers:
        return {"valid": False, "reason": "No AuraSeal found in commit message"}

    seal = trailers["AuraSeal"]
    ec = trailers.get("Entropy-Checksum", "")
    timestamp = trailers.get("RAF-Timestamp", "")
    policy = trailers.get("Policy-Tag", "stable")

    from git_raf.git_ops import head_hash
    commit_hash = head_hash() if commit_ref == "HEAD" else commit_ref

    valid = verify_aura_seal(seal, ec, timestamp, policy, commit_hash[:16])

    return {
        "valid": valid,
        "entropy_checksum": ec,
        "timestamp": timestamp,
        "reason": "" if valid else "Seal mismatch",
    }
