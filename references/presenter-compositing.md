# Measured presenter compositing

Use this reference after one presenter master has passed the preview gate. The
goal is to reuse that master across the entire timeline without paying for
scene-by-scene provider renders or allowing the presenter to cover the content.

## Audio ownership

The locked narration WAV owns the final soundtrack and clock. Mute every copy of
the provider presenter video in the local compositor. Do not mix the provider's
embedded audio with the locked WAV: even a small offset can create comb filtering,
echo, or apparent lip-sync drift.

## Measure before cropping

Do not assume that `object-fit: cover` centers the face. Sample the presenter
master at the opening, early/middle/late speech, and several expression peaks.
Record the face center in source pixels:

```json
{
  "samples": [
    {"frame": 0, "x": 960, "y": 360},
    {"frame": 900, "x": 958, "y": 363}
  ]
}
```

Use a face detector, a vision tool, or careful manual measurement. Keep this
project artifact private when it contains a recognizable face or absolute media
paths. Then derive a deterministic crop and output geometry:

```bash
python3 scripts/build_pip_geometry.py \
  --measurements config/pip-face-centers.json \
  --source-width 1920 \
  --source-height 1080 \
  --crop-size 600 \
  --pip-diameter 220 \
  --output config/pip-geometry.json
```

The report contains the source crop, left/right canvas positions, CSS percentages,
and average face-center error. Treat the default `2px` tolerance as a starting
point, not a universal visual truth. Inspect the result at final delivery size.

## Full-to-PIP transition

A single video layer that changes from full-frame `cover` to a measured square
crop can expose letterboxing or jump the face during interpolation. Use two
synchronized, muted views of the same source when that happens:

1. full-frame view: normal full-screen crop, opacity `1 - progress`;
2. measured PIP view: geometry from `pip-geometry.json`, opacity `progress`;
3. both views use the same source, trim, frame clock, and playback rate;
4. animate only the shared outer mask/position/size and the two opacities;
5. remove the full-frame view after the transition settles.

For Remotion, use the current recommended video component for the pinned project
version. Keep both source views muted and drive every animation from
`useCurrentFrame()` or equivalent deterministic time—not CSS transitions or wall
clock timers.

## Layout contract

At 1920×1080, a circular PIP around `200–240px` is a useful starting range. Keep
diameter, margins, caption keep-out, crop, face target, and allowed corners in the
project manifest. The default scaffold uses `220px`, but scene density decides the
final value.

- open prominent only when the presenter helps establish trust or context;
- move to the corner with the largest verified empty region;
- hide during dense code, tables, forms, URLs, or full-width diagrams;
- never re-enter full-screen late unless the storyboard explicitly calls for it;
- sample both corners and every hidden interval in a contact sheet.

The provider master is a reusable performance asset. Scene layout remains a
local, reversible composition decision.
