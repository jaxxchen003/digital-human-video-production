#!/usr/bin/env python3
"""Run provider-neutral media, sync, freeze, loudness, and checksum delivery QC."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import shutil
import subprocess
from fractions import Fraction
from pathlib import Path
from typing import Any


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, capture_output=True, check=False)


def ffprobe(path: Path) -> dict[str, Any]:
    result = run([
        "ffprobe",
        "-v",
        "error",
        "-show_format",
        "-show_streams",
        "-of",
        "json",
        str(path),
    ])
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or f"ffprobe failed for {path}")
    return json.loads(result.stdout)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def number(value: Any, default: float | None = None) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def frame_rate(value: Any) -> float | None:
    try:
        return float(Fraction(str(value)))
    except (ValueError, ZeroDivisionError):
        return None


def duration_from_metadata(metadata: dict[str, Any]) -> float:
    return number(metadata.get("format", {}).get("duration"), 0.0) or 0.0


def check_metadata(
    metadata: dict[str, Any],
    *,
    width: int,
    height: int,
    fps: float,
    duration_ceiling: float,
    expected_sample_rate: int,
) -> tuple[dict[str, Any], list[str]]:
    streams = metadata.get("streams", [])
    video = next((item for item in streams if item.get("codec_type") == "video"), None)
    audio = next((item for item in streams if item.get("codec_type") == "audio"), None)
    failures: list[str] = []
    if not video:
        failures.append("missing video stream")
    if not audio:
        failures.append("missing audio stream")

    duration = duration_from_metadata(metadata)
    if duration > duration_ceiling + 0.05:
        failures.append(f"duration {duration:.3f}s exceeds {duration_ceiling:.3f}s")

    video_report: dict[str, Any] = {}
    audio_report: dict[str, Any] = {}
    if video:
        actual_fps = frame_rate(video.get("r_frame_rate", "0/1"))
        video_report = {
            "codec": video.get("codec_name"),
            "width": video.get("width"),
            "height": video.get("height"),
            "fps": round(actual_fps or 0, 3),
            "pixel_format": video.get("pix_fmt"),
        }
        if video.get("width") != width or video.get("height") != height:
            failures.append("video dimensions do not match the production contract")
        if actual_fps is None or abs(actual_fps - fps) > 0.05:
            failures.append("video frame rate does not match the production contract")
    if audio:
        actual_rate = int(audio.get("sample_rate", 0) or 0)
        audio_report = {
            "codec": audio.get("codec_name"),
            "sample_rate_hz": actual_rate,
            "channels": audio.get("channels"),
        }
        if actual_rate != expected_sample_rate:
            failures.append("audio sample rate does not match the production contract")
    return {
        "duration_seconds": round(duration, 6),
        "size_bytes": int(metadata.get("format", {}).get("size", 0) or 0),
        "video": video_report,
        "audio": audio_report,
    }, failures


def decode_media(path: Path) -> tuple[bool, str | None]:
    result = run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "null", "-"])
    return result.returncode == 0, result.stderr.strip() or None


def run_blackdetect(path: Path, *, minimum_duration: float, pixel_threshold: float) -> list[dict[str, float]]:
    result = run([
        "ffmpeg",
        "-hide_banner",
        "-i",
        str(path),
        "-vf",
        f"blackdetect=d={minimum_duration}:pix_th={pixel_threshold}",
        "-an",
        "-f",
        "null",
        "-",
    ])
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "blackdetect failed")
    events = []
    pattern = r"black_start:([0-9.]+)\s+black_end:([0-9.]+)\s+black_duration:([0-9.]+)"
    for start, end, duration in re.findall(pattern, result.stderr):
        events.append({"start": float(start), "end": float(end), "duration": float(duration)})
    return events


def run_freezedetect(path: Path, *, minimum_duration: float, noise_db: float) -> list[dict[str, float]]:
    result = run([
        "ffmpeg",
        "-hide_banner",
        "-i",
        str(path),
        "-vf",
        f"freezedetect=n={noise_db}dB:d={minimum_duration}",
        "-an",
        "-f",
        "null",
        "-",
    ])
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "freezedetect failed")
    starts = [float(value) for value in re.findall(r"freeze_start:\s*([0-9.]+)", result.stderr)]
    durations = [float(value) for value in re.findall(r"freeze_duration:\s*([0-9.]+)", result.stderr)]
    ends = [float(value) for value in re.findall(r"freeze_end:\s*([0-9.]+)", result.stderr)]
    return [
        {"start": start, "end": end, "duration": duration}
        for start, end, duration in zip(starts, ends, durations)
    ]


def run_ebur128(path: Path) -> dict[str, float]:
    result = run([
        "ffmpeg",
        "-hide_banner",
        "-i",
        str(path),
        "-af",
        "ebur128=peak=true",
        "-f",
        "null",
        "-",
    ])
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "ebur128 failed")
    summary = result.stderr[result.stderr.rfind("Summary:") :]
    integrated = re.search(r"Integrated loudness:\s+I:\s+(-?[0-9.]+) LUFS", summary)
    loudness_range = re.search(r"Loudness range:\s+LRA:\s+(-?[0-9.]+) LU", summary)
    peak = re.search(r"True peak:\s+Peak:\s+(-?[0-9.]+) dBFS", summary)
    if not integrated or not loudness_range or not peak:
        raise RuntimeError("ebur128 summary could not be parsed")
    return {
        "integrated_loudness_lufs": float(integrated.group(1)),
        "loudness_range_lu": float(loudness_range.group(1)),
        "true_peak_dbfs": float(peak.group(1)),
    }


def load_holds(path: Path | None) -> list[dict[str, float]]:
    if path is None:
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    raw_holds = payload.get("holds", []) if isinstance(payload, dict) else payload
    if not isinstance(raw_holds, list):
        raise ValueError("approved holds must be a list or an object with a holds list")
    holds = []
    for index, hold in enumerate(raw_holds):
        if not isinstance(hold, dict) or "from" not in hold or "to" not in hold:
            raise ValueError(f"hold {index} must contain from and to")
        start = float(hold["from"])
        end = float(hold["to"])
        if start < 0 or end <= start:
            raise ValueError(f"hold {index} has invalid bounds")
        holds.append({"from": start, "to": end})
    return holds


def classify_freezes(
    events: list[dict[str, float]],
    holds: list[dict[str, float]],
    *,
    minimum_overlap_ratio: float = 0.8,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    approved = []
    unexpected = []
    for event in events:
        matched_hold = None
        for hold in holds:
            overlap = max(0.0, min(event["end"], hold["to"]) - max(event["start"], hold["from"]))
            if event["duration"] > 0 and overlap / event["duration"] >= minimum_overlap_ratio:
                matched_hold = hold
                break
        enriched = dict(event)
        if matched_hold:
            enriched["approved_hold"] = matched_hold
            approved.append(enriched)
        else:
            unexpected.append(enriched)
    return approved, unexpected


def generate_contact_sheet(path: Path, output: Path, *, duration: float, interval: float) -> None:
    frame_count = max(1, math.ceil(duration / interval))
    columns = min(4, frame_count)
    rows = math.ceil(frame_count / columns)
    output.parent.mkdir(parents=True, exist_ok=True)
    result = run([
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(path),
        "-vf",
        (
            f"select='isnan(prev_selected_t)+gte(t-prev_selected_t\\,{interval})',"
            f"scale=480:-1,tile={columns}x{rows}:padding=8:margin=8:color=white,format=yuvj420p"
        ),
        "-frames:v",
        "1",
        str(output),
    ])
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "contact sheet generation failed")


def resolve_optional_media(path: Path | None, label: str) -> tuple[Path | None, str | None]:
    if path is None:
        return None, None
    resolved = path.expanduser().resolve()
    if not resolved.exists():
        return None, f"{label} not found: {resolved}"
    return resolved, None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--voice-master", type=Path)
    parser.add_argument("--presenter-master", type=Path)
    parser.add_argument("--approved-holds", type=Path)
    parser.add_argument("--contact-sheet", type=Path)
    parser.add_argument(
        "--allow-partial",
        action="store_true",
        help="allow missing masters/contact sheet and mark the report CANDIDATE",
    )
    parser.add_argument("--contact-interval", default=10.0, type=float)
    parser.add_argument("--width", default=1920, type=int)
    parser.add_argument("--height", default=1080, type=int)
    parser.add_argument("--fps", default=30.0, type=float)
    parser.add_argument("--duration-ceiling", default=180.0, type=float)
    parser.add_argument("--sample-rate", default=48000, type=int)
    parser.add_argument("--sync-tolerance", default=0.25, type=float)
    parser.add_argument("--black-duration", default=0.2, type=float)
    parser.add_argument("--black-pixel-threshold", default=0.02, type=float)
    parser.add_argument("--final-freeze-duration", default=2.0, type=float)
    parser.add_argument("--presenter-freeze-duration", default=2.0, type=float)
    parser.add_argument("--freeze-noise-db", default=-50.0, type=float)
    parser.add_argument("--target-lufs", default=-16.0, type=float)
    parser.add_argument("--lufs-tolerance", default=2.0, type=float)
    parser.add_argument("--true-peak-ceiling", default=-1.0, type=float)
    args = parser.parse_args()

    if not shutil.which("ffprobe") or not shutil.which("ffmpeg"):
        raise SystemExit("ffprobe and ffmpeg are required for delivery validation")
    video = args.video.expanduser().resolve()
    if not video.exists():
        raise SystemExit(f"video not found: {video}")

    failures: list[str] = []
    warnings: list[str] = []
    missing_required = []
    if args.voice_master is None:
        missing_required.append("voice master")
    if args.presenter_master is None:
        missing_required.append("presenter master")
    if args.contact_sheet is None:
        missing_required.append("contact sheet output")
    if missing_required:
        message = "missing final-delivery inputs: " + ", ".join(missing_required)
        (warnings if args.allow_partial else failures).append(message)
    voice, voice_error = resolve_optional_media(args.voice_master, "voice master")
    presenter, presenter_error = resolve_optional_media(args.presenter_master, "presenter master")
    failures.extend(error for error in (voice_error, presenter_error) if error)

    try:
        video_metadata = ffprobe(video)
        metadata, metadata_failures = check_metadata(
            video_metadata,
            width=args.width,
            height=args.height,
            fps=args.fps,
            duration_ceiling=args.duration_ceiling,
            expected_sample_rate=args.sample_rate,
        )
        failures.extend(metadata_failures)
        decoded, decode_error = decode_media(video)
        if not decoded:
            failures.append(f"full decode failed: {decode_error or 'unknown error'}")

        black_events = run_blackdetect(
            video,
            minimum_duration=args.black_duration,
            pixel_threshold=args.black_pixel_threshold,
        )
        if black_events:
            failures.append(f"{len(black_events)} black event(s) at or above {args.black_duration}s")

        holds = load_holds(args.approved_holds.expanduser().resolve() if args.approved_holds else None)
        final_freezes = run_freezedetect(
            video,
            minimum_duration=args.final_freeze_duration,
            noise_db=args.freeze_noise_db,
        )
        approved_freezes, unexpected_freezes = classify_freezes(final_freezes, holds)
        if unexpected_freezes:
            failures.append(f"{len(unexpected_freezes)} unapproved freeze event(s) in final render")

        loudness = run_ebur128(video)
        if abs(loudness["integrated_loudness_lufs"] - args.target_lufs) > args.lufs_tolerance:
            failures.append("integrated loudness is outside the configured tolerance")
        if loudness["true_peak_dbfs"] > args.true_peak_ceiling:
            failures.append("true peak exceeds the configured ceiling")

        media_artifacts: dict[str, Any] = {
            "final": {
                "path": str(video),
                "sha256": sha256(video),
                "duration_seconds": metadata["duration_seconds"],
            }
        }
        final_duration = metadata["duration_seconds"]
        if voice:
            voice_duration = duration_from_metadata(ffprobe(voice))
            media_artifacts["voice_master"] = {
                "path": str(voice),
                "sha256": sha256(voice),
                "duration_seconds": round(voice_duration, 6),
            }
            if abs(final_duration - voice_duration) > args.sync_tolerance:
                failures.append("final render and voice master durations exceed sync tolerance")
        if presenter:
            presenter_duration = duration_from_metadata(ffprobe(presenter))
            presenter_freezes = run_freezedetect(
                presenter,
                minimum_duration=args.presenter_freeze_duration,
                noise_db=args.freeze_noise_db,
            )
            media_artifacts["presenter_master"] = {
                "path": str(presenter),
                "sha256": sha256(presenter),
                "duration_seconds": round(presenter_duration, 6),
                "freeze_events": presenter_freezes,
            }
            if abs(final_duration - presenter_duration) > args.sync_tolerance:
                failures.append("final render and presenter master durations exceed sync tolerance")
            if presenter_freezes:
                failures.append(f"{len(presenter_freezes)} freeze event(s) in presenter master")

        contact_sheet = None
        if args.contact_sheet:
            contact_sheet_path = args.contact_sheet.expanduser().resolve()
            generate_contact_sheet(
                video,
                contact_sheet_path,
                duration=final_duration,
                interval=args.contact_interval,
            )
            contact_sheet = str(contact_sheet_path)
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        failures.append(str(exc))
        metadata = {}
        decoded = False
        black_events = []
        approved_freezes = []
        unexpected_freezes = []
        loudness = {}
        media_artifacts = {}
        contact_sheet = None

    status = "FAIL" if failures else "CANDIDATE" if warnings else "PASS"
    report = {
        "schema_version": "2.0",
        "status": status,
        "deliverable": str(video),
        "metadata": metadata,
        "media_artifacts": media_artifacts,
        "checks": {
            "full_decode": "PASS" if decoded else "FAIL",
            "black_events": black_events,
            "approved_readability_freezes": approved_freezes,
            "unexpected_freezes": unexpected_freezes,
            "loudness": loudness,
            "contact_sheet": contact_sheet,
        },
        "warnings": warnings,
        "failures": failures,
    }
    output = args.output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
