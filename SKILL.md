---
name: digital-human-video-production
description: Produce a verified presenter-led product video from a brief, an approved voice master, an avatar or talking-head render, real product captures, and deterministic motion/compositing. Use when asked to plan, generate, revise, render, or QC a digital-human explainer, demo, tutorial, or launch video, including preview-gated provider generation, measured presenter PIP framing, generation-ledger controls, and delivery QC; keep product claims, brand tokens, media, provider IDs, and credentials in the project, never in this reusable skill.
---

# Digital human video production

This skill is a provider-neutral production contract for presenter-led product
videos. It turns a project brief into an approval-gated package: voice and
presenter previews, shot/timeline artifacts, local motion and compositing, and a
verifiable final delivery. Product copy, visual identity, and audience examples
are deliberately variables supplied by each project.

## Reference technology stack

The documented reference path is explicit about tools while remaining portable:

```text
VoxCPM / VoxCPM2 (voice clone)
  → HeyGen Photo Avatar / Avatar API (presenter preview + one full master)
  → HyperFrames + GSAP (scene packets and seek-safe motion)
  → Remotion (deterministic local composition)
  → FFmpeg + ffprobe + Python (encode and QC)
```

These names describe implementation dependencies, not the product or brand that
the video explains. Each layer has a replaceable adapter; see
`references/dependencies.md` for input/output contracts, required setup, and
private credential boundaries. The public skill never stores a HeyGen profile
ID, VoxCPM model weights, customer media, API key, or project brand token.

## Workflow

### 1. Establish the project contract

Read `references/production-contract.md` and create a local manifest. Confirm:

- audience, language, promise, duration ceiling, aspect ratio, and delivery
  destinations;
- a source-of-truth location for product facts and a claim-review owner;
- brand tokens, fonts, logo/asset rights, safe areas, caption language, and
  accessibility requirements;
- the selected voice, presenter, renderer, capture, and review tools;
- the presenter layout contract: opening treatment, compact/PIP treatment,
  hiding rules, caption keep-out, and whether later hero shots are allowed.

The reusable skill must not contain a client's product name, script, page copy,
brand hex values, customer data, absolute paths, provider IDs, access tokens, or
generated media. Keep those values in ignored project manifests and redacted
handoff artifacts.

### 2. Lock claims, script, and voice

Write numbered scenes. Each scene gets one claim, one focal visual, one primary
motion action, and one readable hold. Separate verified facts from illustrative
examples, and state format, access, ownership, or deployment boundaries instead
of implying capabilities that were not checked.

Use `references/voice-pipeline.md` with the project's approved local voice clone
(the reference implementation uses VoxCPM/VoxCPM2; another supported engine may
be substituted):

1. generate a full candidate and deterministic scene-level artifacts;
2. review the opening, densest explanation, and closing for timbre consistency;
3. apply phrase-aware cadence changes only to spoken regions;
4. copy breaths and non-uniform pauses at `1.0x`;
5. approve one WAV master and record its checksum and generation manifest.

Typical starting rates are `1.10x`–`1.20x`, selected by phrase density rather
than globally. The locked voice master is the timing authority for scene
boundaries, captions, motion packets, and the final composition. A later audio
change reopens the timeline gate.

### 3. Approve and render one presenter master

Use `references/avatar-pipeline.md` with the chosen avatar/talking-head provider
(the reference implementation uses HeyGen Photo Avatar/Avatar API; a local
renderer or filmed presenter may be substituted):

1. render a short preview from the exact approved WAV;
2. inspect lip sync, eye contact, expression, breath-like pauses, crop, and
   freeze events;
3. record a human approval event;
4. render one full-length presenter master;
5. do all scene-level crop, size, corner, mask, and visibility changes locally.

Do not generate one provider clip per scene unless the brief explicitly requires
it. Avoid fixed smiles, looped breathing, sudden camera pushes, frozen poses,
and motion that competes with the product surface. Use
`references/provider-job-ledger.md` to enforce one completed full master per
locked audio checksum. Keep provider job records private and redact IDs before
archiving a QC report.

### 4. Build the information-first visual timeline

Capture real product surfaces when possible. Create a shot manifest and motion
packets before styling every detail. Use the selected renderer's primitives and
the principles in `references/motion-pipeline.md`:

- one focal action per shot (seat, reveal, draw, resolve, morph, or handoff);
- a short settle followed by a deliberate readable hold;
- visual hierarchy that keeps the page, data, code, or URL ahead of the avatar;
- no decorative continuous drift, glow, heavy shadow, or template cascade;
- captions, URLs, commands, and labels remain inside safe areas at delivery size.

The referenced Shotcraft repository is a grammar reference only. Do not copy its
assets, fixed frame tables, or a branded look into a new project.

### 5. Composite presenter and product locally

Read `references/presenter-compositing.md`. Use a deterministic timeline keyed to
the locked voice. A robust default pattern
is: presenter is prominent only for the opening/context beat, then becomes a
small circular or rectangular PIP; it moves to an unoccupied corner, or hides,
when the product surface needs the space. Make all values configurable by
aspect-ratio and scene density rather than hard-coding a client's composition.

Measure face centers from several frames before selecting the PIP crop. Keep the
provider master muted and use the locked WAV as the only soundtrack. If one
interpolated full-to-PIP layer reveals black source edges or jumps framing,
crossfade synchronized full-frame and measured-crop views of the same master.

Keep captions in a reserved band, animate PIP entry with a short settle, and test
the overlay against every focal element. The presenter is the narrator, not the
content being explained. Never let a late accidental full-screen re-entry obscure
the payoff or URL.

### 6. Integrate connector/MCP handoffs when needed

For a tool-call or MCP scene, read `references/mcp-connector-handoff.md`. Verify
the current endpoint, auth boundary, operation name, and returned URL/identifier
from the product source. Show a generic natural-language request and a sanitized
result; never show tokens, cookies, private slugs, raw headers, or claims based
only on a browser return.

### 7. Run delivery gates

Use `scripts/validate_delivery.py` and `references/qc-checklist.md`. A final
delivery requires:

- a contact sheet covering the opening, presenter transition, each major surface,
  densest information, connector/result handoff, and close;
- video/audio metadata matching the project manifest and duration ceiling;
- loudness and true-peak checks with no clipping;
- no black event beyond the configured threshold and no presenter-master freeze
  beyond the configured threshold;
- final-render freezes classified against declared readable-hold intervals;
- a full decode pass and duration sync within the configured tolerance;
- renderer lint/typecheck/build and motion validation passing, with warnings
  reviewed;
- SHA-256 checksums for the final video, voice master, and presenter master;
- a QC JSON containing the manifest version, tool versions, approvals, source
  provenance, test results, and accepted limitations.

If a gate is missing, label the output preview/candidate rather than final.

## Reusable scripts

Run from the skill root:

```bash
python3 scripts/init_project.py --path ./my-video --title "Product explainer"
python3 scripts/build_avatar_schedule.py --duration 120 --output ./my-video/config/avatar-schedule.json
python3 scripts/build_pip_geometry.py \
  --measurements ./my-video/config/pip-face-centers.json \
  --output ./my-video/config/pip-geometry.json
python3 scripts/record_provider_job.py \
  --log ./my-video/logs/provider-generation.jsonl \
  --provider avatar-provider --stage preview --status completed \
  --audio ./my-video/audio/narration-master.wav \
  --output ./my-video/presenter/preview.mp4
python3 scripts/validate_delivery.py \
  --video ./my-video/deliverables/final.mp4 \
  --voice-master ./my-video/audio/narration-master.wav \
  --presenter-master ./my-video/presenter/master.mp4 \
  --approved-holds ./my-video/config/approved-holds.json \
  --contact-sheet ./my-video/deliverables/contact-sheet.jpg \
  --output ./my-video/deliverables/qc.json
```

The scripts are standard-library Python. Delivery validation requires local
`ffprobe` and `ffmpeg`; no bundled script calls a provider, uploads media, or
opens an MCP connection. The host project supplies provider adapters and renderer
commands.

## Reference routing

- contract, artifacts, approvals, and claim discipline: `references/production-contract.md`
- runtime/tool dependencies and provider boundaries: `references/dependencies.md`
- voice cadence, breaths, mastering, and preview gate: `references/voice-pipeline.md`
- avatar preview/full-master boundary and motion prompt: `references/avatar-pipeline.md`
- private provider events and the one-full-master budget: `references/provider-job-ledger.md`
- measured crop, synchronized layers, muted presenter, and PIP geometry: `references/presenter-compositing.md`
- motion grammar, timeline schema, and renderer handoff: `references/motion-pipeline.md`
- technical, audio, visual, and provenance QC: `references/qc-checklist.md`
- generic connector/MCP result handoff: `references/mcp-connector-handoff.md`
