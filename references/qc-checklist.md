# Delivery QC checklist

Use the smallest check that proves the claim, then save its result in a QC JSON.
Commands below assume `ffprobe`, `ffmpeg`, and `shasum` are available. The
bundled validator performs these checks and writes one machine-readable report.

## Metadata and checksum

```bash
ffprobe -v error -show_format -show_streams -of json deliverables/final.mp4
shasum -a 256 deliverables/final.mp4 audio/narration-master.wav presenter/master.mp4
ffmpeg -v error -i deliverables/final.mp4 -f null -
```

Expected default video: H.264, 1920×1080, 30fps, no unexpected rotation. Expected
audio: AAC, 48kHz, stereo. If a target differs, record the exception rather than
silently accepting it.

## Audio

```bash
ffmpeg -i deliverables/final.mp4 -af ebur128=peak=true -f null -
```

Check integrated loudness near `-16 LUFS`, true peak below the delivery ceiling,
and no audible clipping. Listen at 0–15s, the densest comparison, the MCP step,
and the last 10s.

## Picture and presenter

```bash
ffmpeg -i deliverables/final.mp4 -vf "blackdetect=d=0.2:pix_th=0.02" -an -f null -
ffmpeg -i deliverables/final.mp4 -vf "freezedetect=n=-50dB:d=2" -an -f null -
ffmpeg -i presenter/master.mp4 -vf "freezedetect=n=-50dB:d=2" -an -f null -
```

A presenter-master freeze over the threshold is a failure. A final-render freeze
may be an intentional reading hold only when it overlaps a declared interval in
`config/approved-holds.json`; review those frames manually. Do not dismiss every
freeze detector event as an animation hold.

Create a contact sheet with the host's preferred frame extractor. Inspect at
least: frame 0, the full-to-circle handoff, both circle corners, every major
product surface, the MCP/URL response, and the closing. Check that:

- the avatar never covers the URL, button, dense table, or caption line;
- the circle has a clean edge and no aliasing halo;
- text is readable at 100% and the page remains the focal point;
- there is no black gap, presenter freeze over 2s, or late hero re-entry;
- transitions settle and hold instead of continuously drifting.
- the measured face center remains stable in both PIP corners;
- no black source edge appears during the full-frame-to-measured-crop handoff.

## Code and timeline

```bash
python3 -m py_compile scripts/*.py
python3 -m unittest discover -s tests -v
npm run lint --prefix remotion-compositor
npx hyperframes check .
```

Run the actual Remotion still/render command used by the host project. Record
warnings, skipped optional checks, tool versions, and the final file checksum.

## QC JSON minimum

Run the bundled end-to-end gate:

```bash
python3 scripts/validate_delivery.py \
  --video deliverables/final.mp4 \
  --voice-master audio/narration-master.wav \
  --presenter-master presenter/master.mp4 \
  --approved-holds config/approved-holds.json \
  --contact-sheet deliverables/contact-sheet.jpg \
  --output deliverables/qc.json
```

The resulting schema includes full decode, media hashes and durations, black
events, presenter freezes, approved readability holds, unexpected freezes,
EBU R128 loudness, and the generated contact-sheet path. A minimal excerpt is:

```json
{
  "schema_version": "2.0",
  "status": "PASS",
  "deliverable": "deliverables/final.mp4",
  "checks": {
    "full_decode": "PASS",
    "black_events": [],
    "approved_readability_freezes": [],
    "unexpected_freezes": [],
    "loudness": {"integrated_loudness_lufs": -16.0}
  }
}
```

For an early technical smoke test, `--allow-partial` permits omitted masters or
contact-sheet output and returns `CANDIDATE`; it never upgrades a partial run to
`PASS`.
