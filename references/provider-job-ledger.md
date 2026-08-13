# Provider generation ledger

Hosted avatar generation consumes credits and may handle sensitive face or voice
data. Keep a private, append-only JSONL ledger so previews, approvals, retries,
and one full master can be audited without embedding credentials in the skill.

## Invariant

For one locked audio checksum:

```text
preview submitted → preview completed → human approval
  → full master submitted → full master completed exactly once
```

Reuse the completed full master for all local crop, PIP, mask, corner, and hide
changes. A second full generation for the same audio requires an explicit reason,
such as a provider output that failed technical QC. Cosmetic layout changes are
not a valid reason.

## Record events

Store the ledger under an ignored project path such as
`logs/provider-generation.jsonl`:

```bash
python3 scripts/record_provider_job.py \
  --log logs/provider-generation.jsonl \
  --provider avatar-provider \
  --stage preview \
  --status completed \
  --audio audio/narration-master.wav \
  --output presenter/preview.mp4

python3 scripts/record_provider_job.py \
  --log logs/provider-generation.jsonl \
  --provider avatar-provider \
  --stage full-master \
  --status completed \
  --approval-reference approvals/presenter-preview.json \
  --audio audio/narration-master.wav \
  --output presenter/master.mp4
```

The script records media hashes and durations when `ffprobe` is available. It
refuses a duplicate submitted or completed full master for the same audio
checksum unless `--allow-regeneration-reason` is supplied. Record the submitted
event before any retry so the guard runs before another paid call.

## Private and public records

The private ledger may contain provider job IDs, engine settings, timestamps,
and local paths. Before publishing a QC report:

- remove account, avatar/profile, job, asset, callback, and signed URL values;
- retain provider class, engine family when useful, timing, approval state,
  duration, checksum, and retry reason;
- never publish API keys, headers, cookies, source portraits, or voice samples;
- state the number of full-master generations and any accepted exception.

The ledger proves workflow state and cost discipline. It does not prove visual
quality; human preview approval and final contact-sheet review remain required.
