#!/usr/bin/env python3
"""Build a deterministic full-screen-to-circular-presenter schedule."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_times(value: str | None) -> list[float]:
    if not value:
        return []
    return [float(item.strip()) for item in value.split(",") if item.strip()]


def rounded(value: float) -> float:
    return round(value, 3)


def build_schedule(
    duration: float,
    intro_seconds: float,
    scene_ends: list[float],
    left_scenes: set[int],
) -> list[dict[str, object]]:
    if duration <= 0:
        raise ValueError("duration must be positive")
    if intro_seconds < 0 or intro_seconds > duration:
        raise ValueError("intro_seconds must be within the video duration")

    clean_ends = sorted({round(end, 6) for end in scene_ends if 0 < end < duration})
    boundaries = [0.0, *clean_ends, duration]
    schedule: list[dict[str, object]] = []
    for index, (start, end) in enumerate(zip(boundaries, boundaries[1:]), start=1):
        if end <= start:
            continue
        if index == 1 and intro_seconds > start:
            full_end = min(end, intro_seconds)
            schedule.append({"from": rounded(start), "to": rounded(full_end), "layout": "full"})
            start = full_end
        if end <= start:
            continue
        layout = "pip-left" if index in left_scenes else "pip-right"
        schedule.append({"from": rounded(start), "to": rounded(end), "layout": layout})
    return schedule


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--duration", required=True, type=float)
    parser.add_argument("--intro-seconds", default=3.0, type=float)
    parser.add_argument("--circle-size", default=220, type=int)
    parser.add_argument("--margin-x", default=42, type=int)
    parser.add_argument("--bottom-margin", default=66, type=int)
    parser.add_argument("--scene-ends", help="comma-separated scene end times in seconds")
    parser.add_argument("--left-scenes", default="", help="1-based scene indexes, e.g. 4,9,10")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    left_scenes = {int(item.strip()) for item in args.left_scenes.split(",") if item.strip()}
    if any(scene < 1 for scene in left_scenes):
        raise SystemExit("left scene indexes must be 1-based")
    schedule = build_schedule(args.duration, args.intro_seconds, parse_times(args.scene_ends), left_scenes)
    payload = {
        "schema_version": "1.0",
        "duration_seconds": round(args.duration, 3),
        "opening_fullscreen_seconds": round(args.intro_seconds, 3),
        "circle_diameter_px": args.circle_size,
        "horizontal_margin_px": args.margin_x,
        "bottom_margin_px": args.bottom_margin,
        "allowed_positions": ["bottom-left", "bottom-right"],
        "later_fullscreen_or_hero_shots": 0,
        "schedule": schedule,
    }
    output = args.output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
