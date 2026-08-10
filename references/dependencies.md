# Dependencies and provider boundaries

Keep the skill portable by separating required interfaces from optional tools.
Pin versions in each project and record them in the QC report.

## Reference implementation stack

The following stack is the concrete, documented path for this skill. It makes
the technology choices discoverable without putting any project topic, product
brand, page copy, or customer material into the public repository.

| layer | reference technology | input | output | private boundary |
| --- | --- | --- | --- | --- |
| voice | VoxCPM / VoxCPM2 | approved script, local clone/reference profile | locked PCM WAV + generation manifest | model weights, reference audio, prompts, and local paths |
| presenter | HeyGen Photo Avatar / HeyGen Avatar API | locked WAV + approved avatar profile | 12–15s preview, then one full presenter master | account, avatar/profile ID, job ID, source image, API key |
| motion | HyperFrames + GSAP (default runtime) | scene manifest, capture assets, brand tokens from the project | seek-safe scene packets, base visuals, motion-check evidence | project assets and any private renderer configuration |
| compositor | Remotion | locked voice clock, presenter master, base visuals, captions | deterministic PIP/caption composition and final render | project source, fonts, environment variables |
| media/QC | FFmpeg + ffprobe + Python | rendered media and QC thresholds | encoded delivery, metadata/QC JSON, checksums | none; keep raw logs in the project when they contain paths |

The reference handoff is:

```text
VoxCPM locked WAV
  → HeyGen preview approval
  → HeyGen full presenter master
  → HyperFrames + GSAP scene packets/base motion
  → Remotion local PIP + captions + composition
  → FFmpeg/ffprobe encode + QC
```

This is a reference stack, not a hard-coded vendor requirement. A replacement
must satisfy the same artifact contract: one timing authority, an approved
audio checksum, a short presenter preview before the full master, deterministic
scene timing, local layout control, and machine-readable QC evidence.

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
- Node.js/npm plus Remotion's package manager and render commands for the default
  deterministic compositor;
- HyperFrames CLI/checker plus the selected runtime package (GSAP by default);
- VoxCPM/VoxCPM2 local runtime for the default voice path;
- an authenticated HeyGen adapter only during the private preview/full-master
  generation step;
- browser capture or design-export tooling for real product surfaces.

Whisper/ASR is optional: use it when word-level captions or transcript
consistency checks are required. Git LFS, a release asset, or object storage is
optional for large demo media and must not become a dependency of the reusable
skill itself.

The public skill does not require a provider SDK, does not contain credentials,
and does not upload media by itself. Provider commands belong in the host
project's private runbook. If a hosted API is used, verify the provider's
current official documentation, retention behavior, consent requirements, and
data residency before sending voice, face, or customer material.

## What is deliberately not included

- product names, product claims, brand tokens, page copy, customer screenshots,
  or a fixed audience;
- HeyGen account setup, avatar/profile IDs, upload code, billing, or API keys;
- VoxCPM weights, reference recordings, private prompts, or a hosted model
  endpoint;
- HyperFrames/Remotion project source, fonts, licensed assets, or a specific
  motion template;
- a claim that any provider feature, retention policy, model version, or API
  field is stable without checking the provider documentation at run time.

## Version and environment capture

Record at least:

```text
python --version
ffprobe -version
ffmpeg -version
node --version
renderer package/version
animation runtime/version
motion checker/version
provider engine/model/version (redacted IDs)
```

A reproducible delivery includes these versions, the manifest schema version,
the three principal media checksums, and the exact command or job reference
needed to recreate it without exposing secrets. For the reference stack, also
record the VoxCPM generation settings, HeyGen preview approval event, HyperFrames
scene-manifest version, Remotion render command, and FFmpeg encode parameters.
