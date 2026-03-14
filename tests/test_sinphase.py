"""Tests for sinphase stability metric calculation."""

from pathlib import Path

import pytest

from git_raf.sinphase import (
    SinphaseResult,
    calculate_sinphase,
    classify_stability,
    count_artifacts,
    parse_junit_xml,
)


class TestClassifyStability:
    def test_alpha(self):
        assert classify_stability(0.0) == "alpha"
        assert classify_stability(0.1) == "alpha"
        assert classify_stability(0.19) == "alpha"

    def test_beta(self):
        assert classify_stability(0.2) == "beta"
        assert classify_stability(0.3) == "beta"
        assert classify_stability(0.39) == "beta"

    def test_rc(self):
        assert classify_stability(0.4) == "rc"
        assert classify_stability(0.5) == "rc"
        assert classify_stability(0.59) == "rc"

    def test_stable(self):
        assert classify_stability(0.6) == "stable"
        assert classify_stability(0.7) == "stable"
        assert classify_stability(0.79) == "stable"

    def test_release(self):
        assert classify_stability(0.8) == "release"
        assert classify_stability(0.9) == "release"
        assert classify_stability(1.0) == "release"


class TestCountArtifacts:
    def test_no_patterns(self, tmp_path: Path):
        assert count_artifacts([], tmp_path) == 0

    def test_matching_patterns(self, tmp_path: Path):
        (tmp_path / "build").mkdir()
        (tmp_path / "build" / "app.bin").write_text("binary")
        (tmp_path / "build" / "app.so").write_text("shared")

        assert count_artifacts(["build/*.bin"], tmp_path) == 1
        assert count_artifacts(["build/*"], tmp_path) == 2

    def test_no_matches(self, tmp_path: Path):
        assert count_artifacts(["build/*.bin"], tmp_path) == 0


class TestParseJunitXml:
    def test_valid_testsuite(self, tmp_path: Path):
        xml_path = tmp_path / "results.xml"
        xml_path.write_text(
            '<?xml version="1.0"?>'
            '<testsuite tests="10" failures="2" errors="1">'
            "</testsuite>"
        )
        result = parse_junit_xml(xml_path)
        assert result == (7, 10)

    def test_valid_testsuites(self, tmp_path: Path):
        xml_path = tmp_path / "results.xml"
        xml_path.write_text(
            '<?xml version="1.0"?>'
            '<testsuites tests="20" failures="3" errors="0">'
            "</testsuites>"
        )
        result = parse_junit_xml(xml_path)
        assert result == (17, 20)

    def test_missing_file(self, tmp_path: Path):
        assert parse_junit_xml(tmp_path / "nope.xml") is None

    def test_invalid_xml(self, tmp_path: Path):
        xml_path = tmp_path / "bad.xml"
        xml_path.write_text("not xml at all")
        assert parse_junit_xml(xml_path) is None


class TestCalculateSinphase:
    def test_with_override(self, tmp_path: Path):
        result = calculate_sinphase([], tmp_path, test_results=(8, 10))
        assert result is not None
        # No artifacts, so value = (0 * 8) / (10 * 10) = 0
        assert result.value == 0.0
        assert result.stability == "alpha"

    def test_with_artifacts_and_tests(self, tmp_path: Path):
        (tmp_path / "build").mkdir()
        (tmp_path / "build" / "app.bin").write_text("b")
        (tmp_path / "build" / "lib.so").write_text("l")

        result = calculate_sinphase(
            ["build/*"], tmp_path, test_results=(8, 10)
        )
        assert result is not None
        # value = (2 * 8) / (10 * 10) = 0.16
        assert result.value == pytest.approx(0.16)
        assert result.stability == "alpha"

    def test_no_test_results(self, tmp_path: Path):
        result = calculate_sinphase([], tmp_path)
        assert result is None

    def test_zero_tests(self, tmp_path: Path):
        result = calculate_sinphase([], tmp_path, test_results=(0, 0))
        assert result is None
