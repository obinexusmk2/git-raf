"""Tests for semantic versioning."""

from git_raf.versioning import SemVer, bump, format_tag, parse_version


class TestSemVer:
    def test_str(self):
        assert str(SemVer(1, 2, 3)) == "1.2.3"

    def test_default(self):
        assert str(SemVer()) == "0.0.0"


class TestParseVersion:
    def test_simple(self):
        v = parse_version("v1.2.3")
        assert v == SemVer(1, 2, 3)

    def test_with_prefix(self):
        v = parse_version("raf-v2.0.1-stable")
        assert v == SemVer(2, 0, 1)

    def test_no_version(self):
        v = parse_version("no-version-here")
        assert v == SemVer()


class TestBump:
    def test_major(self):
        v = bump(SemVer(1, 2, 3), "major")
        assert v == SemVer(2, 0, 0)

    def test_minor(self):
        v = bump(SemVer(1, 2, 3), "minor")
        assert v == SemVer(1, 3, 0)

    def test_patch(self):
        v = bump(SemVer(1, 2, 3), "patch")
        assert v == SemVer(1, 2, 4)


class TestFormatTag:
    def test_default_format(self):
        result = format_tag("raf", "1.0.0", "stable", "{prefix}-v{version}-{stability}")
        assert result == "raf-v1.0.0-stable"

    def test_custom_format(self):
        result = format_tag("app", "2.1.0", "rc", "v{version}-{stability}")
        assert result == "v2.1.0-rc"
