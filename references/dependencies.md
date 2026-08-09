# Dependencies and provider boundaries

Keep the skill portable by separating required interfaces from optional tools.
Pin versions in each project and record them in the QC report.

## Required interfaces

| interface | responsibility | replaceable by |
| --- | --- | --- |
| voice generator/clone | produces the approved WAV and timing manifest | any local or hosted TTS/voice-clone engine |
| presenter renderer | produces a lip-synced avatar/talking-head master | avatar API, local talking-head model, or filmed presenter |
| capture/source layer | supplies real product pages, diagrams, or approved assets | browser capture, design export, screen recording, asset library |
| motion layer | creates scene packets, transitions, and information hierarchy | HyperFrames-like system, custom React/HTML, motion-graphics tool |
| compositor | aligns audio, base visuals, presenter, captions, and output | Remotion, FFmpeg graph, NLE, or equivalent deterministic renderer |
| QC layer | checks metadata, loudness, black frames, freezes, provenance, and review frames | local scripts plus human review |

## Local baseline

The reference implementation is intentionally small:

- Python 3 standard library for the bundled scripts;
- `ffprobe` and `ffmpeg` for media metadata and optional audio/black-frame checks;
- Node.js plus the selected compositor's package manager when using a React-based
  renderer such as Remotion;
- the selected motion engine's CLI/checker, if one exists;
- an authenticated provider adapter only during the private generation step.

The public skill does not require a provider SDK, does not contain credentials,
and does not upload media by itself. Provider commands belong in the host
project's private runbook. If a hosted API is used, verify current official
documentation, retention behavior, consent requirements, and data residency
before sending voice, face, or customer material.

## Version and environment capture

Record at least:

```text
python --version
ffprobe -version
ffmpeg -version
node --version
renderer package/version
motion checker/version
provider engine/model/version (redacted IDs)
```

A reproducible delivery includes these versions, the manifest schema version,
the three principal media checksums, and the exact command or job reference
needed to recreate it without exposing secrets.
