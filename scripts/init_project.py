#!/usr/bin/env python3
"""Create a clean, media-free project skeleton for the production skill."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


DEFAULT_MANIFEST = {
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
    "presenter_layout": {
        "opening_fullscreen_seconds": 3.0,
        "circle_diameter_px": 180,
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
    }.items():
        path = root / name
        if not path.exists():
            path.write_text(content, encoding="utf-8")

    print(root)
    print(manifest_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
