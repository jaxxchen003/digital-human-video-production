# Avatar or talking-head presenter pipeline

An avatar/talking-head provider (for example, HeyGen) is used for one presenter
master, not as the scene compositor. The host workflow supplies the private
profile, asset ID, and credentials from a local secret store.

## Reference provider contract

The documented reference path uses **HeyGen Photo Avatar / HeyGen Avatar API**:

- input: the exact locked WAV plus a project-approved avatar/profile;
- first output: a 12–15 second preview for human review;
- second output: one full presenter master after the preview gate passes;
- local handoff: the full master is cropped, masked, resized, hidden, or moved
  into PIP by the local compositor.

HeyGen is a technology dependency, not a content dependency. A project may
substitute a local talking-head renderer or filmed presenter, but it must keep
the same preview → approval → one full master boundary. Check the current
HeyGen feature, consent, retention, and export behavior in the private runbook
before uploading face or customer material.

## Boundary

```text
approved VoxCPM WAV
        │
        ├─ 12–15s HeyGen preview ──> human approval
        │                              │
        └────────────── approved ──────┴─> one full 16:9 master
                                               │
                                               └─> local Remotion PIP/crop/mask
```

Never put the avatar group/look ID in this repository. A local job manifest may
contain it only if that file is ignored and redacted before export.

## Preview prompt shape

Use the selected provider's current CLI or authenticated app workflow. The
prompt should describe behavior, not a synthetic script:

```text
Speak directly to the viewer in a calm, helpful product-explainer style.
Keep natural eye contact, small head and hand movement, and varied expression.
Honor the supplied pauses and breaths. Avoid a fixed smile, looped breathing,
large gestures, sudden camera pushes, or a frozen pose.
```

Keep the source orientation and aspect ratio consistent with the final master.
Use the approved engine, profile, expressiveness setting, and motion prompt; do
not silently swap in another avatar or provider. When a provider supports either
script-driven speech or uploaded audio, select the locked audio input instead of
regenerating speech inside the provider. Record the current API/model behavior in
the private runbook because provider defaults change. The skill does not require
a specific vendor.

## Acceptance checklist

- mouth movement follows the exact approved audio;
- eyes and head do not freeze for more than two seconds;
- expression changes are small but visible at both full and circle scale;
- shoulders and face remain inside a safe crop;
- the opening can survive a full-screen crop;
- the same master can be reused for every scene without a visible seam.

Record the preview approval as an event with timestamp, audio checksum, engine,
motion-prompt revision, and reviewer note. Then render the full master once and
hash the output. Use `references/provider-job-ledger.md` to prevent accidental
duplicate full-master generation.

## Local compositor contract

Read `references/presenter-compositing.md` and measure the face before choosing a
crop. For the default 1920×1080 scaffold:

- full-screen: `x=0, y=0, width=1920, height=1080`;
- circular PIP: start around `200–240px`; the scaffold uses `220px`;
- keep horizontal and caption-band margins in the project manifest;
- use a restrained edge/accent ring from the project brand tokens;
- leave the bottom caption band free;
- use a short, non-overshooting settle when entering PIP.

Change the circle size or origin for a different aspect ratio, but keep the
layout and measured crop values in the manifest. Mute the provider video, use the
locked WAV as the only audio source, and test every corner against the page
content. If a single-layer full-to-crop interpolation exposes black borders or
causes a face jump, crossfade synchronized full-frame and measured-crop views.
