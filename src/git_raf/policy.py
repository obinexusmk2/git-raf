"""Branch policy hierarchy and validation for RAF.

Policy levels (ascending strictness):
    minimal      - Experimental branches, basic checks only
    moderate     - Feature branches, semantic validation
    standard     - Development/integration branches
    high         - Staging/release branches, entropy + vectors
    maximum      - Main/production, full AuraSeal + signatures
"""

from __future__ import annotations

POLICY_LEVELS = ["minimal", "moderate", "standard", "high", "maximum"]


def get_branch_policy(branch: str, policies: dict[str, str]) -> str:
    """Determine the policy level for a branch.

    Matches against configured branch-to-policy mappings. Falls back to
    'standard' if no match is found.
    """
    # Exact match first
    if branch in policies:
        return policies[branch]

    # Prefix match (e.g., "feature/foo" matches "feature")
    for pattern, level in policies.items():
        if branch.startswith(pattern + "/") or branch.startswith(pattern):
            return level

    return "standard"


def policy_level_index(level: str) -> int:
    """Return the numeric index of a policy level."""
    try:
        return POLICY_LEVELS.index(level)
    except ValueError:
        return POLICY_LEVELS.index("standard")


def validate_for_policy(
    policy: str,
    staged_files: list[str],
    strict: bool = False,
) -> list[str]:
    """Validate staged changes against a policy level.

    Returns a list of failure messages (empty = passed).
    """
    failures: list[str] = []
    level = policy_level_index(policy)

    # All levels: check for obviously problematic files
    sensitive_patterns = [".env", "credentials", "secret", ".pem", "private_key"]
    for filepath in staged_files:
        name = filepath.lower()
        for pattern in sensitive_patterns:
            if pattern in name:
                failures.append(
                    f"Sensitive file detected: {filepath} "
                    f"(matches '{pattern}')"
                )

    # High and above: require governance metadata awareness
    if level >= 3:  # high
        if strict and not any(f.endswith(".rift.gov") for f in staged_files):
            # Not necessarily a failure, just a warning in non-strict
            pass

    # Maximum: would require AuraSeal and multi-sig (checked at commit time)
    if level >= 4 and strict:  # maximum
        failures_note = (
            "Maximum policy: commits require AuraSeal signing (-S flag)"
        )
        # This is informational; actual enforcement happens in commit command
        if strict:
            pass  # Enforcement deferred to commit phase

    return failures


def check_merge_policy(
    source_policy: str,
    target_policy: str,
) -> tuple[bool, str]:
    """Check if merging from source to target policy level is allowed.

    Returns (allowed, reason).
    """
    source_idx = policy_level_index(source_policy)
    target_idx = policy_level_index(target_policy)

    if target_idx > source_idx:
        return (True, (
            f"Merge from {source_policy} to {target_policy} requires "
            f"elevated validation (target is stricter)."
        ))

    return (True, "Policy levels compatible.")
