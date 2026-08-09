#!/usr/bin/env python3
"""Run lightweight, provider-neutral delivery checks and write a QC JSON."""

from __future__ import annotations

import argparse
import json
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
        raise RuntimeError(result.stderr.strip() or "ffprobe failed")
    return json.loads(result.stdout)


def number(value: Any, default: float | None = None) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


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

    duration = number(metadata.get("format", {}).get("duration"), 0.0) or 0.0
    if duration > duration_ceiling + 0.05:
        failures.append(f"duration {duration:.3f}s exceeds {duration_ceiling:.3f}s")

    video_report: dict[str, Any] = {}
    audio_report: dict[str, Any] = {}
    if video:
        actual_fps = number(Fraction(video.get("r_frame_rate", "0/1")))
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
        "duration_seconds": round(duration, 3),
        "video": video_report,
        "audio": audio_report,
    }, failures


def run_blackdetect(path: Path) -> tuple[int | None, str | None]:
    if not shutil.which("ffmpeg"):
        return None, "ffmpeg not available"
    result = run([
        "ffmpeg",
        "-hide_banner",
        "-i",
        str(path),
        "-vf",
        "blackdetect=d=0.5:pix_th=0.10",
        "-an",
        "-f",
        "null",
        "-",
    ])
    durations = [float(value) for value in re.findall(r"black_duration:([0-9.]+)", result.stderr)]
    return len([value for value in durations if value >= 0.5]), None


def run_loudnorm(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    if not shutil.which("ffmpeg"):
        return None, "ffmpeg not available"
    result = run([
        "ffmpeg",
        "-hide_banner",
        "-i",
        str(path),
        "-af",
        "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json",
        "-f",
        "null",
        "-",
    ])
    blocks = re.findall(r"\{\s*\"input_i\".*?\n\}", result.stderr, re.S)
    if not blocks:
        return None, "loudnorm JSON not found"
    try:
        report = json.loads(blocks[-1])
    except json.JSONDecodeError:
        return None, "loudnorm JSON could not be parsed"
    return report, None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--width", default=1920, type=int)
    parser.add_argument("--height", default=1080, type=int)
    parser.add_argument("--fps", default=30.0, type=float)
    parser.add_argument("--duration-ceiling", default=180.0, type=float)
    parser.add_argument("--sample-rate", default=48000, type=int)
    args = parser.parse_args()

    video = args.video.expanduser().resolve()
    if not video.exists():
        raise SystemExit(f"video not found: {video}")
    if not shutil.which("ffprobe"):
        raise SystemExit("ffprobe is required for delivery validation")

    metadata, metadata_failures = check_metadata(
        ffprobe(video),
        width=args.width,
        height=args.height,
        fps=args.fps,
        duration_ceiling=args.duration_ceiling,
        expected_sample_rate=args.sample_rate,
    )
    black_events, black_warning = run_blackdetect(video)
    loudnorm, loudnorm_warning = run_loudnorm(video)
    failures = list(metadata_failures)
    if black_events:
        failures.append(f"{black_events} black event(s) at or above 0.5s")
    checks = {
        "black_events_over_0_5_seconds": black_events,
        "loudnorm": loudnorm,
        "warnings": [warning for warning in (black_warning, loudnorm_warning) if warning],
    }
    report = {
        "status": "FAIL" if failures else "PASS",
        "deliverable": str(video),
        "checks": checks,
        "metadata": metadata,
        "failures": failures,
    }
    output = args.output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
