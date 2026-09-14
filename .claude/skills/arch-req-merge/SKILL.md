---
name: arch-req-merge
description: >
  Merge multiple partial requirements YAML files from different readers into
  one consolidated req.yaml. Detects field conflicts between sources, identifies
  critical gaps, and produces a gap report. Run after all readers, before
  the gap-filling interview in arch-requirements.
---

> **Locating shared resources.** References in this file to `standards/`,
> `tools/`, `config.yaml`, and `templates/` are relative to the ArchHarness
> resource root. Determine the root, in order: (1) the `ARCHHARNESS_HOME`
> environment variable, (2) the output of `python -m archharness root` (the
> pip-installed package bundles these resources under its `data` directory),
> (3) the current working directory when it already contains `config.yaml` and
> `tools/` (the repository checkout). Prefix shared paths with that root
> whenever the working directory is not the resource root.

You are a **requirements consolidation specialist**.
Your job is to merge partial requirements from multiple sources, detect conflicts,
and produce a clear list of what still needs to be filled in.

## How to invoke (single pipeline for any number of sources)

One command handles one source or many — the output is always the same
`req/v1` schema (`schemas/req-v1.schema.json`), always with a gap report:

```bash
archharness req --diagram arch.drawio --doc brief.md --csv cmdb.csv \
    -o req.yaml --report gap-report.md --manifest req.manifest.json
```

`--manifest` writes an `artifact/v1` provenance record (hash-bound to the
output) for the workflow gate. There is no one-source shortcut anymore:
a single source flows through the same normalize → merge → validate →
serialize pipeline, so downstream stages see one stable contract.

## What the merger does

1. **Name matching** — identifies the same application/component across sources using fuzzy name matching
2. **Confidence-weighted merge** — picks the highest-confidence value for each field
3. **Conflict detection** — if two HIGH+ confidence sources give different values, flags `⚠CONFLICT`
4. **Gap analysis** — checks every CRITICAL field and reports what's missing
5. **Output** — `merged-req.yaml` + `gap-report.md`

## Confidence priority (high to low)

1. `manual` — user explicitly confirmed in interview
2. `high` — CMDB API, structured arch YAML file
3. `medium` — draw.io/D2 diagram, document extraction
4. `low` — vision OCR, inferred values
5. `unknown` — no source

When two sources conflict at the same confidence level, both values are preserved
and flagged as `⚠CONFLICT`. The user must resolve conflicts manually.

## Critical fields that block arch-design

| Category | Critical fields |
|----------|----------------|
| Application | `dc_or_region`, `country`, `platform` |
| Component | `comp_type` |
| Interaction | `from_component`, `to_component`, `protocol`, `auth_method` |
| User auth | `auth_server`, `auth_protocol` |
| Project | `project_name` |

All other fields are non-critical (can be TBD).

## When to run arch-req-merge via CLI vs in chat

**CLI** (authoritative — automated pipeline, any number of files):
```bash
archharness req --diagram a.drawio --doc b.md -o req.yaml --report gap-report.md
```

**In chat** (user provides partial YAML blocks):
If the user provides partial req.yaml blocks in the conversation, you may
perform the merge logic manually:
1. For each field, identify which source has it with the highest confidence
2. Flag any conflicts
3. List all critical gaps
4. Output the merged YAML and gap list inline

Chat merges are drafts: a CLI run is still required before arch-design,
because only the CLI validates the output against `req/v1`.

## After merge: what to tell the user

Always conclude with:
- Count of critical gaps remaining
- Whether arch-design can proceed (`0 critical gaps`) or interview is needed
- Which specific gaps need filling (quote the exact field names from gap-report.md)
