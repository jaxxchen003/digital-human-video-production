#!/usr/bin/env python3
"""Build measured presenter crop and PIP geometry from face-center samples."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from statistics import fmean
from typing import Any


def load_samples(path: Path) -> list[dict[str, float]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    raw_samples = payload.get("samples", []) if isinstance(payload, dict) else payload
    if not isinstance(raw_samples, list) or not raw_samples:
        raise ValueError("measurements must contain a non-empty samples list")
    samples: list[dict[str, float]] = []
    for index, sample in enumerate(raw_samples):
        if not isinstance(sample, dict) or "x" not in sample or "y" not in sample:
            raise ValueError(f"sample {index} must contain numeric x and y values")
        try:
            x = float(sample["x"])
            y = float(sample["y"])
        except (TypeError, ValueError) as exc:
            raise ValueError(f"sample {index} has invalid x or y") from exc
        if not math.isfinite(x) or not math.isfinite(y):
            raise ValueError(f"sample {index} must be finite")
        samples.append({"x": x, "y": y})
    return samples


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(value, maximum))


def build_geometry(
    samples: list[dict[str, float]],
    *,
    source_width: int,
    source_height: int,
    crop_size: int,
    pip_diameter: int,
    target_face_x_ratio: float,
    target_face_y_ratio: float,
    canvas_width: int,
    canvas_height: int,
    margin_x: int,
    bottom_margin: int,
    tolerance_px: float,
) -> dict[str, Any]:
    if source_width <= 0 or source_height <= 0 or crop_size <= 0 or pip_diameter <= 0:
        raise ValueError("source, crop, and PIP dimensions must be positive")
    if crop_size > source_width or crop_size > source_height:
        raise ValueError("crop_size must fit inside the source frame")
    if pip_diameter > canvas_width or pip_diameter > canvas_height:
        raise ValueError("pip_diameter must fit inside the output canvas")
    if not 0 <= target_face_x_ratio <= 1 or not 0 <= target_face_y_ratio <= 1:
        raise ValueError("target face ratios must be between 0 and 1")

    mean_x = fmean(sample["x"] for sample in samples)
    mean_y = fmean(sample["y"] for sample in samples)
    raw_crop_x = mean_x - target_face_x_ratio * crop_size
    raw_crop_y = mean_y - target_face_y_ratio * crop_size
    crop_x = clamp(raw_crop_x, 0, source_width - crop_size)
    crop_y = clamp(raw_crop_y, 0, source_height - crop_size)

    scale = pip_diameter / crop_size
    target_x = target_face_x_ratio * pip_diameter
    target_y = target_face_y_ratio * pip_diameter
    average_output_x = (mean_x - crop_x) * scale
    average_output_y = (mean_y - crop_y) * scale
    offset_x = average_output_x - target_x
    offset_y = average_output_y - target_y
    average_offset = math.hypot(offset_x, offset_y)

    sample_offsets = []
    for sample in samples:
        output_x = (sample["x"] - crop_x) * scale
        output_y = (sample["y"] - crop_y) * scale
        sample_offsets.append(math.hypot(output_x - target_x, output_y - target_y))

    pip_y = canvas_height - pip_diameter - bottom_margin
    right_x = canvas_width - pip_diameter - margin_x
    if min(margin_x, bottom_margin, pip_y, right_x) < 0:
        raise ValueError("PIP margins place the overlay outside the output canvas")

    return {
        "schema_version": "1.0",
        "status": "PASS" if average_offset <= tolerance_px else "FAIL",
        "source": {"width": source_width, "height": source_height},
        "measurements": {
            "sample_count": len(samples),
            "average_face_center": {"x": round(mean_x, 3), "y": round(mean_y, 3)},
        },
        "crop": {
            "x": round(crop_x, 3),
            "y": round(crop_y, 3),
            "width": crop_size,
            "height": crop_size,
            "was_clamped": abs(crop_x - raw_crop_x) > 1e-6 or abs(crop_y - raw_crop_y) > 1e-6,
        },
        "pip": {
            "diameter": pip_diameter,
            "target_face_center": {"x": round(target_x, 3), "y": round(target_y, 3)},
            "average_face_center": {"x": round(average_output_x, 3), "y": round(average_output_y, 3)},
            "average_offset": {
                "x": round(offset_x, 3),
                "y": round(offset_y, 3),
                "distance": round(average_offset, 3),
            },
            "max_sample_offset_distance": round(max(sample_offsets), 3),
            "tolerance_px": tolerance_px,
        },
        "canvas_positions": {
            "bottom_left": {"x": margin_x, "y": pip_y},
            "bottom_right": {"x": right_x, "y": pip_y},
            "bottom_margin": bottom_margin,
        },
        "css_percentages": {
            "video_width": round(source_width / crop_size * 100, 6),
            "video_height": round(source_height / crop_size * 100, 6),
            "video_left": round(-crop_x / crop_size * 100, 6),
            "video_top": round(-crop_y / crop_size * 100, 6),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--measurements", required=True, type=Path)
    parser.add_argument("--source-width", default=1920, type=int)
    parser.add_argument("--source-height", default=1080, type=int)
    parser.add_argument("--crop-size", default=600, type=int)
    parser.add_argument("--pip-diameter", default=220, type=int)
    parser.add_argument("--target-face-x-ratio", default=0.5, type=float)
    parser.add_argument("--target-face-y-ratio", default=0.59, type=float)
    parser.add_argument("--canvas-width", default=1920, type=int)
    parser.add_argument("--canvas-height", default=1080, type=int)
    parser.add_argument("--margin-x", default=42, type=int)
    parser.add_argument("--bottom-margin", default=66, type=int)
    parser.add_argument("--tolerance", default=2.0, type=float)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    try:
        report = build_geometry(
            load_samples(args.measurements.expanduser().resolve()),
            source_width=args.source_width,
            source_height=args.source_height,
            crop_size=args.crop_size,
            pip_diameter=args.pip_diameter,
            target_face_x_ratio=args.target_face_x_ratio,
            target_face_y_ratio=args.target_face_y_ratio,
            canvas_width=args.canvas_width,
            canvas_height=args.canvas_height,
            margin_x=args.margin_x,
            bottom_margin=args.bottom_margin,
            tolerance_px=args.tolerance,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise SystemExit(str(exc)) from exc

    output = args.output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output)
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
