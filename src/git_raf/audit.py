"""Audit trail management for RAF governance.

Stores audit records as JSON Lines (.jsonl) in .raf/audit.jsonl.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


AUDIT_FILE = "audit.jsonl"


def generate_audit_record(
    event_type: str,
    commit_hash: str | None = None,
    metadata: dict | None = None,
    validation_results: dict | None = None,
) -> dict:
    """Create a structured audit record."""
    return {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "event_type": event_type,
        "commit_hash": commit_hash,
        "metadata": metadata or {},
        "validation_results": validation_results or {},
    }


def append_audit_log(root: Path, record: dict) -> None:
    """Append an audit record to .raf/audit.jsonl."""
    audit_path = root / ".raf" / AUDIT_FILE
    audit_path.parent.mkdir(parents=True, exist_ok=True)

    with open(audit_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, separators=(",", ":")) + "\n")


def read_audit_log(
    root: Path,
    from_date: str | None = None,
    to_date: str | None = None,
) -> list[dict]:
    """Read and optionally filter audit records."""
    audit_path = root / ".raf" / AUDIT_FILE
    if not audit_path.exists():
        return []

    records = []
    with open(audit_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue

            ts = record.get("timestamp", "")
            if from_date and ts < from_date:
                continue
            if to_date and ts > to_date + "T99:99:99Z":
                continue

            records.append(record)

    return records


def format_audit_report(records: list[dict]) -> str:
    """Format audit records as a human-readable report."""
    lines = [f"RAF Audit Trail ({len(records)} records)", "=" * 50]

    for record in records:
        ts = record.get("timestamp", "?")
        event = record.get("event_type", "?")
        commit = record.get("commit_hash", "?")
        if commit and len(commit) > 8:
            commit = commit[:8]

        lines.append(f"\n[{ts}] {event}")
        if commit and commit != "?":
            lines.append(f"  Commit: {commit}")

        meta = record.get("metadata", {})
        for key, value in meta.items():
            lines.append(f"  {key}: {value}")

    return "\n".join(lines)
