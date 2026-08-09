# Avatar or talking-head presenter pipeline

An avatar/talking-head provider (for example, HeyGen) is used for one presenter
master, not as the scene compositor. The host workflow supplies the private
profile, asset ID, and credentials from a local secret store.

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
Use the approved engine, profile, and expressiveness setting; do not silently
swap in another avatar or provider. The skill does not require a specific
vendor.

## Acceptance checklist

- mouth movement follows the exact approved audio;
- eyes and head do not freeze for more than two seconds;
- expression changes are small but visible at both full and circle scale;
- shoulders and face remain inside a safe crop;
- the opening can survive a full-screen crop;
- the same master can be reused for every scene without a visible seam.

Record the preview approval as an event with timestamp, audio checksum, and
reviewer note. Then render the full master once and hash the output.

## Local compositor contract

For the default 1920×1080 canvas:

- full-screen: `x=0, y=0, width=1920, height=1080`;
- bottom-left circle: diameter `180`, origin roughly `(42, 834)`;
- bottom-right circle: diameter `180`, origin roughly `(1698, 834)`;
- use a restrained edge/accent ring from the project brand tokens;
- leave the bottom caption band free;
- use a short `0.48s` settle (`0.96 → 1.025 → 1.0`) when entering PIP.

Change the circle size or origin for a different aspect ratio, but keep the
layout values in the manifest and test every corner against the page content.
