"""Sinphase stability metric calculation.

Ported from scripts/git-raf.sh. The sinphase metric sigma measures build
stability as a function of artifact availability and test pass rate.

Formula: sigma = (artifact_count * tests_passed) / (tests_total * NORM_FACTOR)

Stability classification thresholds:
    alpha   < 0.2
    beta    < 0.4
    rc      < 0.6
    stable  < 0.8
    release >= 0.8
"""

from __future__ import annotations

import glob
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path


NORM_FACTOR = 10

STABILITY_THRESHOLDS = [
    (0.2, "alpha"),
    (0.4, "beta"),
    (0.6, "rc"),
    (0.8, "stable"),
]


@dataclass
class SinphaseResult:
    """Result of a sinphase calculation."""
    value: float
    stability: str
    artifact_count: int
    tests_passed: int
    tests_total: int


def classify_stability(sinphase: float) -> str:
    """Classify stability level from a sinphase value."""
    for threshold, label in STABILITY_THRESHOLDS:
        if sinphase < threshold:
            return label
    return "release"


def count_artifacts(patterns: list[str], root: Path) -> int:
    """Count files matching artifact glob patterns."""
    count = 0
    for pattern in patterns:
        full_pattern = str(root / pattern)
        count += len(glob.glob(full_pattern, recursive=True))
    return count


def parse_junit_xml(path: Path) -> tuple[int, int] | None:
    """Parse JUnit XML for (passed, total) test counts.

    Returns None if file doesn't exist or can't be parsed.
    """
    if not path.exists():
        return None

    try:
        tree = ET.parse(path)
        root_elem = tree.getroot()

        # Handle both <testsuites> and <testsuite> root elements
        if root_elem.tag == "testsuites":
            total = int(root_elem.get("tests", "0"))
            failures = int(root_elem.get("failures", "0"))
            errors = int(root_elem.get("errors", "0"))
        elif root_elem.tag == "testsuite":
            total = int(root_elem.get("tests", "0"))
            failures = int(root_elem.get("failures", "0"))
            errors = int(root_elem.get("errors", "0"))
        else:
            return None

        passed = total - failures - errors
        return (max(passed, 0), total)
    except (ET.ParseError, ValueError):
        return None


def find_test_results(root: Path) -> tuple[int, int] | None:
    """Search for test results in common locations.

    Looks for JUnit XML in standard paths. Returns (passed, total) or None.
    """
    candidates = [
        root / "test" / "results.xml",
        root / "tests" / "results.xml",
        root / "build" / "test-results.xml",
        root / "report.xml",
        root / "junit.xml",
        root / ".raf" / "test-results.xml",
    ]

    for path in candidates:
        result = parse_junit_xml(path)
        if result is not None:
            return result

    return None


def calculate_sinphase(
    artifact_patterns: list[str],
    root: Path,
    test_results: tuple[int, int] | None = None,
) -> SinphaseResult | None:
    """Calculate the sinphase stability metric.

    Args:
        artifact_patterns: Glob patterns for build artifacts.
        root: Repository root path.
        test_results: Optional (passed, total) tuple. If not provided,
            searches for JUnit XML in standard locations.

    Returns:
        SinphaseResult or None if calculation cannot be performed.
    """
    artifact_count = count_artifacts(artifact_patterns, root)

    if test_results is None:
        test_results = find_test_results(root)

    if test_results is None:
        return None

    tests_passed, tests_total = test_results

    if tests_total == 0:
        return None

    value = (artifact_count * tests_passed) / (tests_total * NORM_FACTOR)
    stability = classify_stability(value)

    return SinphaseResult(
        value=value,
        stability=stability,
        artifact_count=artifact_count,
        tests_passed=tests_passed,
        tests_total=tests_total,
    )
