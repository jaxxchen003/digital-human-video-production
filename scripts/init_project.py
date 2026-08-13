#!/usr/bin/env python3
"""Create a clean, media-free project skeleton for the production skill."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


DEFAULT_MANIFEST = {
    "schema_version": "2.0",
    "title": "Product explainer",
    "language": "zh-CN",
    "audience": "AI beginners",
    "aspect_ratio": "16:9",
    "width": 1920,
    "height": 1080,
    "fps": 30,
    "duration_ceiling_seconds": 180,
    "voice_provider": "local-clone",
    "presenter_provider": "avatar-or-talking-head",
    "renderer": ["motion-engine", "compositor"],
    "approved_audio": "audio/narration-master.wav",
    "audio_timing_authority": True,
    "provider_generation_policy": {
        "preview_required": True,
        "human_preview_approval_required": True,
        "full_master_budget": 1,
        "scene_layout_changes_must_be_local": True,
    },
    "presenter_layout": {
        "opening_fullscreen_seconds": 3.0,
        "circle_diameter_px": 220,
        "horizontal_margin_px": 42,
        "bottom_margin_px": 66,
        "target_face_center_ratio": {"x": 0.5, "y": 0.59},
        "allowed_positions": ["bottom-left", "bottom-right"],
        "later_fullscreen": False,
    },
    "brand_tokens": {
        "background": "<project token>",
        "surface": "<project token>",
        "ink": "<project token>",
        "accent": "<project token>",
        "code_surface": "<project token>",
    },
}


DIRECTORIES = (
    "audio",
    "config",
    "presenter",
    "compositions/frames",
    "sources",
    "deliverables",
    "logs",
    "snapshots",
    "remotion-compositor/public/audio",
    "remotion-compositor/public/avatar",
    "remotion-compositor/public/base",
    "remotion-compositor/public/captions",
    "remotion-compositor/public/timeline",
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", required=True, type=Path)
    parser.add_argument("--title", default=DEFAULT_MANIFEST["title"])
    parser.add_argument("--force", action="store_true", help="replace production.json only")
    args = parser.parse_args()

    root = args.path.expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    for directory in DIRECTORIES:
        (root / directory).mkdir(parents=True, exist_ok=True)

    manifest = json.loads(json.dumps(DEFAULT_MANIFEST))
    manifest["title"] = args.title
    manifest_path = root / "config" / "production.json"
    if manifest_path.exists() and not args.force:
        raise SystemExit(f"Refusing to overwrite {manifest_path}; use --force")
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    for name, content in {
        "brief.md": "# Brief\n\nWrite the audience, promise, product facts, and source links here.\n",
        "script.md": "# Script\n\nUse numbered scenes with one claim and one focal action per scene.\n",
        "config/narration-segments.json": '{"segments": []}\n',
        "config/avatar-schedule.json": "[]\n",
        "config/approvals.json": '{"voice": null, "presenter_preview": null, "timeline": null, "delivery": null}\n',
        "config/approved-holds.json": '{"holds": []}\n',
        "config/pip-face-centers.example.json": '{"samples": [{"frame": 0, "x": 960, "y": 360}]}\n',
        "logs/provider-generation.jsonl": "",
    }.items():
        path = root / name
        if not path.exists():
            path.write_text(content, encoding="utf-8")

    print(root)
    print(manifest_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
