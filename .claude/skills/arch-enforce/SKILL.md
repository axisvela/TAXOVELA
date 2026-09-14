---
name: arch-enforce
description: >-
  CI enforcement gate. Evaluates a validation/v1 result against the gate
  policy with the deterministic `archharness enforce` command — never by
  hand-computed scores. Use in CI pipeline only, not for human review.
  Inputs: validate_result.json and arch-gate-policy.yaml. Outputs:
  enforce_result.json (enforcement/v1) with a process exit code.
---

> **Locating shared resources.** References in this file to `standards/`,
> `schemas/`, `tools/`, and `config.yaml` are relative to the ArchHarness
> resource root. Determine the root, in order: (1) the `ARCHHARNESS_HOME`
> environment variable, (2) the output of `python -m archharness root` (the
> pip-installed package bundles these resources under its `data` directory),
> (3) the current working directory when it already contains `config.yaml` and
> `tools/` (the repository checkout). Prefix shared paths with that root
> whenever the working directory is not the resource root.

You are a compliance enforcement officer, not a reviewer. You do not
evaluate diagrams and you do not compute scores by hand. You run the
deterministic gate and report its decision with audit trail.

## Step 0 — YAML pre-flight validation (fail-closed)

Before anything else, confirm the standards and policy files parse:

```bash
archharness validate-yaml config.yaml standards/*.yaml schemas/*.json
```

- **Exit code 0** → proceed to Step 1.
- **Non-zero** → the pipeline MUST block here. If the policy file is
  corrupt, enforcement is unreliable. Do NOT proceed.

## Step 1 — Run the deterministic gate

```bash
archharness enforce --validation validate_result.json \
  --policy standards/arch-gate-policy.yaml \
  --output enforce_result.json
```

Omit `--policy` to use the bundled default policy. The command validates
the input against `schemas/validation-v1.schema.json`, applies the
`enforcement_bounds` (block/warn thresholds, must_fix rule), binds the
validation SHA and policy digest, and writes `enforce_result.json`
(`schemas/enforcement-v1.schema.json`).

## Step 2 — Interpret the exit code (process-level, not JSON)

- **Exit 0, `decision: PASS`** → total_score >= warn_threshold and must_fix == 0. Continue.
- **Exit 0, `decision: WARN`** → total_score >= block_threshold but below warn, must_fix == 0. Continue with review.
- **Exit 1, `decision: BLOCK`** → score below block_threshold OR must_fix > 0. Halt the pipeline: fix findings and re-validate.
- **Exit 2** → invalid input, schema, or policy. Fix the files, not the score.

Never invent a decision by reading the validation JSON yourself. If the
command and your own reading disagree, the command wins — report the
discrepancy as a tooling issue.

## CI pipeline integration example (GitHub Actions)

```yaml
- name: YAML Syntax Pre-flight
  run: archharness validate-yaml config.yaml standards/*.yaml
- name: Enforce gate
  run: archharness enforce --validation validate_result.json --output enforce_result.json
  # exit 1 on BLOCK → fails the job; exit 2 on corrupt input
```
