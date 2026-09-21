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
`req/v2` schema (`schemas/req-v2.schema.json`), always with a gap report:

```bash
archharness req --diagram arch.drawio --doc brief.md --csv cmdb.csv \
    -o req.yaml --report gap-report.md --manifest req.manifest.json

# Cross-field validation (rules V1-V7) of the merged req/v2 document:
archharness req-validate req.yaml            # add --json for machine output
```

`--manifest` writes an `artifact/v1` provenance record (hash-bound to the
output) for the workflow gate. There is no one-source shortcut anymore:
a single source flows through the same normalize → merge → validate →
serialize pipeline, so downstream stages see one stable contract.

## What the merger does

1. **Per-entity merge** — matches each entity kind across sources:
   - named entities (`infra`, `systems`, `components`) by normalized name
   - `deployments` by (component, environment)
   - `flows` by (source, target)
   - `network_links` by (undirected endpoint pair, method)
   - `auth` by (entry point, subject)
2. **Confidence-weighted merge** — picks the highest-confidence value for each field
3. **Conflict detection** — if two MEDIUM+ confidence sources give different values, flags `CONFLICT`
4. **Reference resolution** — partials reference other entities by **name**; the
   merger resolves names to **typed IDs** (`INF-nn`, `APP-nn`, `CMP-nn`, `DEP-nn`,
   `FLOW-nn`, `LNK-nn`, `AUTH-nn`, `STK-nn`) and drops any row whose required
   reference cannot be resolved, recording a critical gap.
5. **Gap analysis + contract validation** — checks every CRITICAL field, then
   validates the output against `req/v2`
6. **Output** — `req.yaml` + `gap-report.md`

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
| Infra | `name`, `node_kind` |
| System | `name`, `type` (owner recommended) |
| Component | `name`, owning system resolved, `kind` |
| Deployment | `component` + `environment` resolved; `infra_id` required for `prod` |
| Flow | both endpoints resolved to components, `protocol`, inline `auth_method` |
| Network link | both `infra` endpoints resolved, `method` |
| Auth | entry point resolved, `protocol` |
| Project | `project_name` |

All other fields are non-critical (can be TBD). Some strong recommendations are
reported as non-critical gaps: component `component_role`, `sensitivity`,
flow `port`, infra `country`.

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
because only the CLI validates the output against `req/v2` and resolves
name references into typed IDs.

## After merge: what to tell the user

Always conclude with:
- Count of critical gaps remaining
- Whether arch-design can proceed (`0 critical gaps`) or interview is needed
- Which specific gaps need filling (quote the exact field names from gap-report.md)
