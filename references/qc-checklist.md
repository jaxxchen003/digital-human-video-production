# Delivery QC checklist

Use the smallest check that proves the claim, then save its result in a QC JSON.
Commands below assume `ffprobe`, `ffmpeg`, and `shasum` are available.

## Metadata and checksum

```bash
ffprobe -v error -show_format -show_streams -of json deliverables/final.mp4
shasum -a 256 deliverables/final.mp4 audio/narration-master.wav presenter/heygen-master.mp4
```

Expected default video: H.264, 1920×1080, 30fps, no unexpected rotation. Expected
audio: AAC, 48kHz, stereo. If a target differs, record the exception rather than
silently accepting it.

## Audio

```bash
ffmpeg -i deliverables/final.mp4 -af loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json -f null -
```

Check integrated loudness near `-16 LUFS`, true peak below the delivery ceiling,
and no audible clipping. Listen at 0–15s, the densest comparison, the MCP step,
and the last 10s.

## Picture and presenter

```bash
ffmpeg -i deliverables/final.mp4 -vf "blackdetect=d=0.5:pix_th=0.10" -an -f null -
```

Create a contact sheet with the host's preferred frame extractor. Inspect at
least: frame 0, the full-to-circle handoff, both circle corners, every major
product surface, the MCP/URL response, and the closing. Check that:

- the avatar never covers the URL, button, dense table, or caption line;
- the circle has a clean edge and no aliasing halo;
- text is readable at 100% and the page remains the focal point;
- there is no black gap, presenter freeze over 2s, or late hero re-entry;
- transitions settle and hold instead of continuously drifting.

## Code and timeline

```bash
python3 -m py_compile scripts/*.py
npm run lint --prefix remotion-compositor
npx hyperframes check .
```

Run the actual Remotion still/render command used by the host project. Record
warnings, skipped optional checks, tool versions, and the final file checksum.

## QC JSON minimum

```json
{
  "status": "PASS",
  "deliverable": "deliverables/final.mp4",
  "sha256": "<sha256>",
  "video": {"width": 1920, "height": 1080, "fps": 30},
  "audio": {"sample_rate_hz": 48000, "integrated_lufs": -16.0},
  "avatar_layout": {
    "opening_fullscreen_seconds": 3.6,
    "compact_diameter_px": 180,
    "allowed_positions": ["bottom-left", "bottom-right"],
    "later_fullscreen_or_hero_shots": 0
  },
  "checks": {
    "black_events_over_0_5_seconds": 0,
    "presenter_freeze_events_over_2_seconds": 0,
    "remotion_lint_and_typecheck": "PASS"
  }
}
```
