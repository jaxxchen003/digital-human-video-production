# Production contract

This is the small, reviewable contract that keeps a presenter-led product video
reproducible. It defines the shape of a project without prescribing a client's
topic, copy, visual identity, or provider.

## Required project manifest

```json
{
  "title": "Product explainer",
  "language": "zh-CN",
  "audience": "",
  "promise": "",
  "aspect_ratio": "16:9",
  "width": 1920,
  "height": 1080,
  "fps": 30,
  "duration_ceiling_seconds": 180,
  "voice": {"provider": "local-clone", "model": ""},
  "presenter": {"provider": "avatar-or-talking-head", "profile": ""},
  "renderers": ["motion-engine", "compositor"],
  "reference_stack": {
    "voice": "VoxCPM/VoxCPM2",
    "presenter": "HeyGen Photo Avatar/Avatar API",
    "motion": "HyperFrames + GSAP",
    "compositor": "Remotion",
    "media_qc": "FFmpeg + ffprobe + Python"
  },
  "approved_audio": "audio/narration-master.wav",
  "presenter_layout": {
    "opening_mode": "prominent",
    "compact_mode": "circle-or-rectangle-pip",
    "allowed_positions": ["bottom-left", "bottom-right"],
    "later_fullscreen": false,
    "caption_keepout_ratio": 0.17
  },
  "brand_tokens": {
    "background": "<project token>",
    "surface": "<project token>",
    "ink": "<project token>",
    "accent": "<project token>",
    "code_surface": "<project token>"
  },
  "approvals": {
    "brief": false,
    "voice": false,
    "presenter_preview": false,
    "timeline": false,
    "delivery": false
  }
}
```

## Suggested project tree

```text
project/
├── brief.md
├── script.md
├── config/
│   ├── production.json
│   ├── narration-segments.json
│   ├── avatar-schedule.json
│   └── shot-manifest.json
├── audio/
│   ├── narration-master.wav
│   └── narration-master.generation.json
├── presenter/
│   ├── preview.mp4
│   ├── master.mp4
│   └── provider-job.redacted.json
├── compositions/frames/
├── remotion-compositor/  # or the selected local renderer
├── sources/
├── deliverables/
│   ├── final.mp4
│   ├── qc.json
│   └── contact-sheet.png
└── logs/
```

Raw audio, provider outputs, captured customer pages, fonts with unclear
redistribution rights, `.env` files, and unredacted job logs stay local. Commit
schemas, templates, redacted manifests, and QC evidence—not private media.

## Approval gates

1. **Brief gate** — audience, promise, claims, source links, brand tokens,
   delivery target, and risk constraints are identified.
2. **Voice gate** — one narration candidate is approved by listening; the chosen
   WAV, generation settings, and checksum are recorded.
3. **Presenter gate** — a short preview is approved for cadence, expression,
   eye contact, lip sync, crop, and freeze behavior.
4. **Timeline gate** — scene boundaries, captions, page captures, and presenter
   schedule all use the locked voice clock.
5. **Delivery gate** — technical, visual, audio, provenance, and checksum checks
   pass; known limitations are explicitly recorded.

The workflow may continue after a failed gate only with a `preview` or
`candidate` label. A later voice or claim change reopens downstream gates.

## Claim and asset discipline

Use a source table for every load-bearing claim: source URL/path, retrieval date,
claim owner, and the exact on-screen wording. Mark illustrative UI as such and
never present a fabricated provider screen as a verified product fact. Track
font, logo, screenshot, music, SFX, and model rights separately; the public skill
does not grant rights to a project's assets.

## Variation points

Projects may replace the voice engine, avatar provider, motion renderer,
compositor, language, aspect ratio, caption style, or PIP geometry. Preserve the
invariants: one timing authority, explicit approvals, local composition, source
provenance, and a machine-readable final QC report.

`reference_stack` is an implementation note, not a content field. Keep it
explicit when using the documented VoxCPM → HeyGen → HyperFrames + GSAP →
Remotion path; update it when a project selects an alternative. Never place a product
brand, customer page, provider credential, or private asset ID in the public
skill manifest.
