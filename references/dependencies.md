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

## Official dependency references

Check these sources at implementation time and pin the versions actually used by
the host project:

- [OpenBMB/VoxCPM](https://github.com/OpenBMB/VoxCPM) — reference local voice
  clone and WAV source;
- [HeyGen Create Video API](https://developers.heygen.com/reference/create-video)
  — current avatar/photo-avatar video request, uploaded-audio, engine, motion,
  and asynchronous job contract;
- [heygen-com/hyperframes](https://github.com/heygen-com/hyperframes) and its
  [GSAP animation guide](https://hyperframes.app/docs/3-guides/3-gsap-animation)
  — HTML composition and paused, seek-controlled motion runtime;
- [Remotion rendering](https://www.remotion.dev/docs/render) and
  [video component guidance](https://www.remotion.dev/docs/offthreadvideo) —
  deterministic React composition and frame-accurate local video sources;
- [FFmpeg](https://ffmpeg.org/documentation.html) — probing, decode validation,
  EBU R128 loudness, black/freeze detection, contact sheets, and encoding;
- [Python](https://docs.python.org/3/) — standard-library project and QC scripts.

Provider schemas, defaults, quotas, pricing, and privacy behavior are temporal.
Do not copy a request body from this skill without checking the current official
contract. Prefer the current Remotion video component for the pinned version;
older projects may still use `OffthreadVideo` intentionally.

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

No provider SDK is required by the public repository. `scripts/record_provider_job.py`
records private state but never calls a provider. `scripts/build_pip_geometry.py`
uses measurement data supplied by the project and does not bundle a face detector.
`scripts/validate_delivery.py` requires local `ffmpeg` and `ffprobe` for the full
gate; the remaining bundled scripts use only the Python standard library.

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

## Method and motion references

The following repositories influenced workflow or motion vocabulary. They are
not runtime dependencies and their assets/code are not vendored here. License
notes were checked on 2026-08-13 and must be rechecked before reuse:

| reference | useful for | reuse boundary |
| --- | --- | --- |
| [video-shotcraft](https://github.com/Vincentwei1021/video-shotcraft) | shot cards, motion grammar, readable holds, Remotion examples | Apache-2.0 at review time; adapt principles and verify asset-level attribution |
| [HyperFrames Motion Director](https://github.com/geekjourneyx/hyperframes-motion-director) | Chinese-first brief/design/storyboard contracts and HyperFrames review gates | AGPL-3.0 at review time; reference concepts unless the chosen project can comply with the license |
| [HyperFrames Motion Library](https://github.com/nutllwhy/hyperframes-motion-library) | parameterized local motion templates and transparent-overlay formats | no repository license was declared at review time; do not copy code or assets without permission or a clear license |
| [Rachel Digital Human Production](https://github.com/Jingyi-Wu-Richael/rachel-digital-human-production) | paid-call preflight, 15-second approval gate, job-state tracking | MIT at review time; its MiniMax path is not a dependency of this skill |

Use these as comparative references. The public Skill's executable contract is
defined only by this repository and the selected host-project adapters.
