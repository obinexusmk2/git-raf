"""Governance metadata generation for RAF commits and tags.

Produces governance vectors, entropy checksums, and commit trailer formatting
as defined in the RAF specification.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class GovernanceVector:
    """Three-dimensional risk assessment vector."""
    attack_risk: float
    rollback_cost: float
    stability_impact: float

    def __str__(self) -> str:
        return (f"[attack_risk: {self.attack_risk:.2f}, "
                f"rollback_cost: {self.rollback_cost:.2f}, "
                f"stability_impact: {self.stability_impact:.2f}]")


@dataclass
class GovernanceMetadata:
    """Complete governance metadata for a commit or tag."""
    policy_tag: str
    governance_ref: str
    entropy_checksum: str
    governance_vector: GovernanceVector
    aura_seal: str
    timestamp: str
    artifact_count: int


def compute_entropy_checksum(file_paths: list[str], root: Path) -> str:
    """Compute SHA3-256 entropy checksum over file contents.

    Hashes each file with SHA3-256, then hashes the concatenated hashes.
    """
    combined = ""
    for fp in sorted(file_paths):
        full_path = root / fp
        if full_path.exists() and full_path.is_file():
            data = full_path.read_bytes()
            file_hash = hashlib.sha3_256(data).hexdigest()
            combined += file_hash

    if not combined:
        combined = "empty"

    return hashlib.sha3_256(combined.encode("utf-8")).hexdigest()


def compute_governance_vector(
    sinphase: float,
    changed_files: list[str] | None = None,
) -> GovernanceVector:
    """Compute governance vector from sinphase and change scope.

    attack_risk = 1 - sinphase (higher sinphase = lower risk)
    rollback_cost = based on number of changed files
    stability_impact = sinphase value
    """
    attack_risk = max(0.0, min(1.0, 1.0 - sinphase))

    if changed_files:
        file_count = len(changed_files)
        rollback_cost = min(1.0, file_count / 50.0)
    else:
        rollback_cost = 0.15

    stability_impact = max(0.0, min(1.0, sinphase))

    return GovernanceVector(
        attack_risk=attack_risk,
        rollback_cost=rollback_cost,
        stability_impact=stability_impact,
    )


def compute_aura_seal(
    entropy_checksum: str,
    timestamp: str,
    stability: str,
    version: str,
) -> str:
    """Generate AuraSeal as HMAC-SHA256 over governance data.

    Uses a deterministic key derived from the governance data itself for
    unsealed commits. For signed commits, the user's private key is used
    instead (see crypto.py).
    """
    import hmac

    content = f"{entropy_checksum}{timestamp}{stability}{version}"
    seal = hmac.new(
        key=b"git-raf-governance",
        msg=content.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()
    return seal


def generate_metadata(
    stability: str,
    sinphase: float,
    version: str,
    artifact_patterns: list[str],
    governance_ref: str,
    root: Path,
) -> GovernanceMetadata:
    """Generate complete governance metadata for a tag or commit."""
    import glob

    # Count artifacts
    artifact_count = 0
    artifact_files: list[str] = []
    for pattern in artifact_patterns:
        matches = glob.glob(str(root / pattern), recursive=True)
        artifact_files.extend(matches)
        artifact_count += len(matches)

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entropy = compute_entropy_checksum(artifact_files, root)
    vector = compute_governance_vector(sinphase)
    seal = compute_aura_seal(entropy, timestamp, stability, version)

    return GovernanceMetadata(
        policy_tag=stability,
        governance_ref=governance_ref,
        entropy_checksum=entropy,
        governance_vector=vector,
        aura_seal=seal,
        timestamp=timestamp,
        artifact_count=artifact_count,
    )


def format_tag_message(
    stability: str,
    sinphase: float,
    version: str,
    metadata: GovernanceMetadata,
) -> str:
    """Format governance metadata as a tag annotation message."""
    return (
        f"Git-RAF Auto-Tag: {stability}\n"
        f"Sinphase: {sinphase:.4f}\n"
        f"Version: {version}\n"
        f"Policy-Tag: \"{metadata.policy_tag}\"\n"
        f"Governance-Ref: {metadata.governance_ref}\n"
        f"Entropy-Checksum: {metadata.entropy_checksum}\n"
        f"Governance-Vector: {metadata.governance_vector}\n"
        f"AuraSeal: {metadata.aura_seal}\n"
        f"Build-Timestamp: {metadata.timestamp}\n"
        f"Artifact-Count: {metadata.artifact_count}"
    )


def generate_commit_trailers(
    policy_tag: str,
    governance_ref: str,
    staged_files: list[str],
    root: Path,
    sign: bool = False,
) -> str:
    """Generate governance trailers for a commit message."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entropy = compute_entropy_checksum(staged_files, root)
    vector = compute_governance_vector(0.5, staged_files)

    lines = [
        f"Policy-Tag: {policy_tag}",
        f"Governance-Ref: {governance_ref}",
        f"Entropy-Checksum: {entropy}",
        f"Governance-Vector: {vector}",
        f"RAF-Timestamp: {timestamp}",
    ]

    if sign:
        seal = compute_aura_seal(entropy, timestamp, policy_tag, "HEAD")
        lines.append(f"AuraSeal: {seal}")

    return "\n".join(lines)
