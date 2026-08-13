# Motion engine, compositor, and shot grammar

The motion layer owns information-first frames and scene packets. The compositor
owns deterministic timing, captions, presenter overlay, and the final render.
The locked voice manifest is the clock shared by both.

In the reference implementation, **HyperFrames** owns the HTML/timeline layer
and **GSAP** is its default seek-safe animation runtime. **Remotion** performs
the local React/TypeScript composition when the project uses a Remotion output
path. They are deliberately separate: HyperFrames/GSAP decides what the shot
communicates and how it animates; Remotion decides when and where each layer
appears in the final composition. Either layer can be replaced when the project
preserves the same scene-packet, timecode, and QC contracts.

## Shot grammar

The [video-shotcraft repository](https://github.com/Vincentwei1021/video-shotcraft)
is a reference for shot cards and motion grammar, not a dependency or a source
of copied assets. Adapt its principles to the project's visual system and
evidence:

| purpose | useful grammar | generic adaptation |
| --- | --- | --- |
| reveal an artifact | deal/fly-in card | introduce a small set of related artifacts, then hold the problem |
| explain a path | spatial pan / path draw | move through stages one at a time, ending on the user-visible result |
| compare options | paired/split surface | keep criteria stable while options arrive and resolve |
| demonstrate an action | type/seat/resolve | use a real input surface, one action, one confirmed result |
| close a loop | group lockup / launch | keep the outcome as the anchor while surrounding chrome clears |

Use one main action per shot, a short settle, and a readable hold. Avoid a
template-like cascade where every element moves independently. Real product
captures or faithful, clearly labeled mock surfaces beat generic fake dashboards.

## Scene packet contract

Each scene packet should state:

```text
scene id · voice start/end · one-sentence purpose · focal surface
entry/exit transition · one motion action · hold duration
presenter layout · caption keep-out · source/provenance · known risks
```

Use the project's brand tokens and typography, but keep their values out of this
public skill. Reserve the accent color for a deliberate emphasis beat, prefer
hairline elevation to heavy shadows, and keep code/URL surfaces structurally
distinct from reading surfaces. Adapt the density and type scale to the aspect
ratio; never shrink load-bearing copy below the legibility floor.

## Compositor overlay shape

Keep the overlay driven by a simple schedule rather than scene-specific JSX:

```json
[
  {"from": 0, "to": 3.0, "layout": "prominent"},
  {"from": 3.0, "to": 32.0, "layout": "pip-right"},
  {"from": 32.0, "to": 45.0, "layout": "pip-left"},
  {"from": 45.0, "to": 58.0, "layout": "hidden"}
]
```

The times and geometry are examples, not a fixed template. Switch corners at
scene boundaries, hide the presenter when a dense page needs the canvas, and
test every overlay against the focal card, URL, cursor, code, and captions. Do
not allow a late accidental full-screen presenter shot.

Generate the geometry from measured face centers rather than trusting automatic
`cover` cropping. During the opening-to-PIP handoff, use the two-view pattern in
`references/presenter-compositing.md` when a single interpolated crop produces a
black edge or framing jump. Both presenter views remain muted and synchronized
to the locked WAV.

## Render handoff

1. Copy only the locked audio, presenter master, base visuals, and captions into
   the compositor's local input area.
2. Build the timeline from the generation manifest.
3. Run lint/typecheck and a handful of still frames before a full render.
4. Render the final media and a contact sheet.
5. Run a full decode, black/freeze detection, loudness, duration-sync, and
   checksum pass. Classify only timeline-declared readable holds as intentional.
6. Archive the QC JSON, contact sheet, PIP geometry report, and redacted provider
   ledger beside the deliverable.
