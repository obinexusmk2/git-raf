"""Tests for branch policy hierarchy."""

from git_raf.policy import (
    check_merge_policy,
    get_branch_policy,
    policy_level_index,
    validate_for_policy,
)


DEFAULT_POLICIES = {
    "main": "maximum",
    "release": "high",
    "develop": "standard",
    "feature": "moderate",
    "experimental": "minimal",
}


class TestGetBranchPolicy:
    def test_exact_match(self):
        assert get_branch_policy("main", DEFAULT_POLICIES) == "maximum"
        assert get_branch_policy("develop", DEFAULT_POLICIES) == "standard"

    def test_prefix_match(self):
        assert get_branch_policy("feature/auth", DEFAULT_POLICIES) == "moderate"
        assert get_branch_policy("release/1.0", DEFAULT_POLICIES) == "high"

    def test_no_match(self):
        assert get_branch_policy("hotfix/urgent", DEFAULT_POLICIES) == "standard"


class TestPolicyLevelIndex:
    def test_known_levels(self):
        assert policy_level_index("minimal") == 0
        assert policy_level_index("moderate") == 1
        assert policy_level_index("standard") == 2
        assert policy_level_index("high") == 3
        assert policy_level_index("maximum") == 4

    def test_unknown_level(self):
        assert policy_level_index("nonexistent") == 2  # defaults to standard


class TestValidateForPolicy:
    def test_no_issues(self):
        failures = validate_for_policy("minimal", ["src/app.py", "tests/test.py"])
        assert failures == []

    def test_sensitive_file(self):
        failures = validate_for_policy("minimal", [".env", "src/app.py"])
        assert len(failures) == 1
        assert ".env" in failures[0]

    def test_credentials_file(self):
        failures = validate_for_policy("standard", ["config/credentials.json"])
        assert len(failures) == 1


class TestCheckMergePolicy:
    def test_compatible(self):
        allowed, reason = check_merge_policy("moderate", "standard")
        assert allowed is True

    def test_stricter_target(self):
        allowed, reason = check_merge_policy("minimal", "maximum")
        assert allowed is True
        assert "elevated" in reason
