# VoxCPM voice pipeline

The voice master is the timing authority. Do not build a visual timeline first
and stretch it to a later voice edit.

## Candidate recipe

1. Start from the approved clone/reference voice profile in the host project.
2. Split the script into semantic scenes, normally 8–12 sections for a short
   explainer.
3. Generate one full candidate and scene-level files with deterministic names.
4. Check transcript alignment and listen to the first 15 seconds, the densest
   comparison scene, and the closing.
5. Preserve a candidate manifest; never overwrite a previously approved master.

## Humanized cadence

Use phrase-aware `atempo` or an equivalent time-compression operation:

| phrase type | target | treatment |
| --- | ---: | --- |
| ordinary explanation | 1.15x | compress only spoken samples |
| dense list / platform names | 1.20x | keep each name intelligible |
| emphasis | 1.10–1.15x | leave a little more room |
| closing / CTA | 1.08–1.10x | let the final breath land |

Copy all audio outside phrase regions at `1.0x`. This retains breath gaps and
avoids the metronomic, robotic quality caused by global speed-up. Keep scene
boundary pauses intentional and non-uniform (for example, 0.12–0.30 seconds),
then record the chosen values in the generation manifest.

## Mastering and timing

- Mix to a practical web target near `-16 LUFS`; leave true-peak headroom.
- Keep the original sample rate until the final delivery encode; 48kHz stereo
  AAC is a sensible video target.
- Derive scene start/end, caption chunks, HyperFrames durations, and Remotion
  frames from the final generation manifest.
- Hash the locked WAV and place the hash in the QC report.
- Generate a short presenter preview from the exact locked audio, not a proxy
  recording.

## Human listening checklist

- Does the first 40 seconds sound like the later version?
- Do breaths occur at phrase boundaries rather than on a fixed metronome?
- Are 1.20x dense passages still intelligible?
- Does the voice settle slightly before a key product claim or URL?
- Does the audio end naturally instead of truncating the final consonant?

If the front and back timbre differ, stop the pipeline, identify which source
segments were used, and regenerate a single consistent candidate before making
any presenter call.
