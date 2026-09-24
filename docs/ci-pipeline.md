# Running the pipeline in CI

The gate is deterministic: identical inputs always produce the same
`enforcement/v1` decision, so `validate → enforce` can run on every pull
request without a human in the loop. This page is the recipe, with the
evidence archived alongside the build.

`docs/first-run.md` covers the same steps interactively.

---

## What runs where

| Step | Command | Fails the build when |
|---|---|---|
| Installation health | `archharness doctor` | a governance input will not load |
| Requirements | `archharness req-validate req.yaml` | a `req/v2` rule is violated |
| Model | `archharness arch-check -i blueprint.yaml` | a model rule (`A-01`…) is an error |
| Traceability | `archharness trace-check -r req.yaml -b blueprint.yaml` | a node is not in the inventory or has no deployment |
| Compatibility | `archharness schema-check --baseline <base>` | a schema change is breaking under the same id |
| Gate | `archharness enforce --validation validate_result.json` | the decision is `BLOCK` |
| Evidence | `archharness validate-check`, `archharness backlog` | `validate-check` finds an unverifiable finding |

The diagram itself is produced by the deterministic generator
(`archharness diagram`), so the same YAML always draws the same XML. Validation
is the one step that needs judgement; supply the `validation/v1` result from
the `arch-validate` skill, or archive it as an input to the build.

## The workflow

```yaml
name: Architecture gate

on:
  pull_request:
  workflow_dispatch:

jobs:
  gate:
    runs-on: ubuntu-latest
    env:
      PROJECT: projects/orders            # or examples/<id>
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0                  # schema-check needs a baseline

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - run: pip install --quiet pyyaml

      - name: Installation health
        run: python -m archharness doctor

      - name: Requirements and model
        run: |
          python -m archharness req-validate "$PROJECT/output/requirements/req.yaml"
          python -m archharness arch-check -i "$PROJECT/output/designs/blueprint.yaml"
          python -m archharness trace-check \
            -r "$PROJECT/output/requirements/req.yaml" \
            -b "$PROJECT/output/designs/blueprint.yaml"

      - name: Schema compatibility
        run: |
          baseline="${{ github.event.pull_request.base.sha }}"
          if [ -z "$baseline" ]; then baseline="HEAD^"; fi
          if git rev-parse --verify --quiet "${baseline}^{commit}" >/dev/null; then
            python -m archharness schema-check --baseline "$baseline"
          else
            echo "baseline ${baseline} unavailable; skipping"
          fi

      - name: Redraw the diagram from the committed model
        run: |
          python -m archharness diagram -i "$PROJECT/output/designs/blueprint.yaml" \
            -o "$PROJECT/output/diagrams/diagram-ci.drawio" \
            --d2 "$PROJECT/output/diagrams/diagram-ci.d2" \
            --png "$PROJECT/output/diagrams/diagram-ci.png" \
            --routing-diagnostics "$PROJECT/output/diagrams/routes.json"

      # The gate. exit 1 = BLOCK, which fails this step and the build.
      - name: Enforce the gate policy
        run: |
          python -m archharness enforce \
            --validation "$PROJECT/output/validation/validate_result.json" \
            --profile "${{ vars.ARCH_GATE_PROFILE || 'baseline' }}" \
            --output "$PROJECT/output/validation/enforce_result.json"

      - name: Check the findings are joinable to the model
        run: |
          python -m archharness validate-check \
            -v "$PROJECT/output/validation/validate_result.json" \
            -r "$PROJECT/output/requirements/req.yaml" \
            -b "$PROJECT/output/designs/blueprint.yaml"
          python -m archharness backlog \
            -v "$PROJECT/output/validation/validate_result.json" \
            -r "$PROJECT/output/requirements/req.yaml" \
            -b "$PROJECT/output/designs/blueprint.yaml" \
            -o "$PROJECT/output/validation/backlog.md"

      - name: Archive the evidence
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: architecture-gate
          path: |
            $PROJECT/output/validation/*.json
            $PROJECT/output/validation/*.md
            $PROJECT/output/diagrams/diagram-ci.*
            $PROJECT/output/diagrams/routes.json
          retention-days: 30
```

## Notes

- **`if: always()` on the archive step** keeps the evidence even when the gate
  blocks, which is when it matters most.
- **`--profile`** selects a policy profile (`baseline`, `poc`, `production`);
  a profile may tighten the baseline freely, and a looser one has to declare
  `allow_looser: true` with a rationale, so the gate cannot be relaxed in a
  pipeline edit without the policy file saying so.
- **`--output`** writes the `enforcement/v1` decision. Commit it if the
  decision should be auditable later, or archive it as a build artifact.
- **Determinism** means a re-run reproduces the decision exactly. This
  repository enforces that on its own records:
  `tests/test_example_artifacts.py` replays every recorded decision and fails
  when the current policy and validation result no longer produce it.
- `archharness enforce` exits `0` for PASS or WARN and `1` for BLOCK; a
  malformed input exits `2`, so a broken pipeline never looks like a pass.

## Keeping the records honest

```bash
python -m archharness workflow verify     # do recorded artifacts match disk?
python -m archharness workflow can draw   # may this stage start?
```

Artifacts are hash-verified, not just named: a diagram edited underneath a
recorded decision fails the gate closed rather than silently certifying the
wrong picture.
