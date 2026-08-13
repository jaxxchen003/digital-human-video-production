#!/usr/bin/env python3
"""Append an auditable preview or full-master event to a private JSONL ledger."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TERMINAL_STATUSES = {"completed", "failed", "cancelled"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def duration_seconds(path: Path) -> float | None:
    if not shutil.which("ffprobe"):
        return None
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        return None
    try:
        return round(float(result.stdout.strip()), 6)
    except ValueError:
        return None


def read_events(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    events = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSONL at line {line_number}") from exc
        if not isinstance(event, dict):
            raise ValueError(f"event at line {line_number} must be an object")
        events.append(event)
    return events


def assert_full_master_budget(
    events: list[dict[str, Any]],
    *,
    audio_sha256: str,
    status: str = "completed",
    provider_job_id: str | None = None,
    allow_regeneration_reason: str | None,
) -> None:
    existing = [
        event
        for event in events
        if event.get("stage") == "full-master"
        and event.get("status") in {"submitted", "completed"}
        and event.get("audio_sha256") == audio_sha256
    ]
    conflicts = []
    for event in existing:
        same_job = provider_job_id and event.get("provider_job_id") == provider_job_id
        if status == "completed" and event.get("status") == "submitted" and same_job:
            continue
        if status == "completed" and event.get("status") == "submitted" and not provider_job_id:
            continue
        conflicts.append(event)
    if conflicts and not allow_regeneration_reason:
        raise ValueError(
            "a submitted or completed full master already exists for this audio checksum; "
            "reuse it locally or provide --allow-regeneration-reason"
        )


def build_event(
    *,
    provider: str,
    stage: str,
    status: str,
    audio: Path,
    output: Path | None,
    approval_reference: str | None,
    provider_job_id: str | None,
    engine: str | None,
    allow_regeneration_reason: str | None,
) -> dict[str, Any]:
    if not audio.exists():
        raise ValueError(f"audio not found: {audio}")
    if status == "completed" and (output is None or not output.exists()):
        raise ValueError("completed events require an existing --output file")
    if stage == "full-master" and status in {"submitted", "completed"} and not approval_reference:
        raise ValueError("full-master events require --approval-reference")

    event: dict[str, Any] = {
        "schema_version": "1.0",
        "event_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "provider": provider,
        "stage": stage,
        "status": status,
        "audio_sha256": sha256(audio),
        "audio_duration_seconds": duration_seconds(audio),
        "approval_reference": approval_reference,
        "provider_job_id": provider_job_id,
        "engine": engine,
        "output": str(output) if output else None,
        "output_sha256": sha256(output) if output and output.exists() else None,
        "output_duration_seconds": duration_seconds(output) if output and output.exists() else None,
        "regeneration_exception_reason": allow_regeneration_reason,
    }
    return event


def append_event(path: Path, event: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", required=True, type=Path)
    parser.add_argument("--provider", required=True)
    parser.add_argument("--stage", required=True, choices=("preview", "full-master"))
    parser.add_argument("--status", required=True, choices=("submitted", *sorted(TERMINAL_STATUSES)))
    parser.add_argument("--audio", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--approval-reference")
    parser.add_argument("--provider-job-id")
    parser.add_argument("--engine")
    parser.add_argument("--allow-regeneration-reason")
    args = parser.parse_args()

    log = args.log.expanduser().resolve()
    audio = args.audio.expanduser().resolve()
    output = args.output.expanduser().resolve() if args.output else None
    try:
        events = read_events(log)
        audio_hash = sha256(audio)
        if args.stage == "full-master" and args.status in {"submitted", "completed"}:
            assert_full_master_budget(
                events,
                audio_sha256=audio_hash,
                status=args.status,
                provider_job_id=args.provider_job_id,
                allow_regeneration_reason=args.allow_regeneration_reason,
            )
        event = build_event(
            provider=args.provider,
            stage=args.stage,
            status=args.status,
            audio=audio,
            output=output,
            approval_reference=args.approval_reference,
            provider_job_id=args.provider_job_id,
            engine=args.engine,
            allow_regeneration_reason=args.allow_regeneration_reason,
        )
        append_event(log, event)
    except (OSError, ValueError) as exc:
        raise SystemExit(str(exc)) from exc

    print(json.dumps(event, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
