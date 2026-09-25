# Re-validating an example against its current image

A `validation/v1` result is bound to exact bytes: `source.path` names the image
and `source.sha256` is its hash, alongside a `source.ruleset_digest`. Images are
now produced by **D2** (draw.io is the editable source), so whenever an image is
re-rendered the binding has to be redone.

Validation is produced by the **`arch-validate` skill** (LLM vision) or an
equivalent reviewer. It is not a deterministically generated document, so the
CLI cannot recreate it — this guide covers everything around that one human
step.

## Current status (measured)

| Example | Recorded validation binds | Binding | Pending work |
|---|---|---|---|
| `01-ecommerce-azure` | `output/diagrams/diagram.png` (frozen v1, draw.io) | intact — hash matches | validate the current `diagram-v2.png` (D2) so the gate judges the new chart |
| `02-ai-agent-hybrid` | `output/diagrams/diagram.png` | intact | as above (`diagram-v2.png`) |
| `03-order-query-aws-hybrid` | `output/diagrams/diagram.png` | intact | as above (`diagram-v2.png`) |
| `04-service-delivery-private-cloud` | `output/diagrams/diagram.png` | intact | as above (`diagram-v2.png`) |
| `05-supply-chain-order-private-cloud` | `output/diagrams/diagram.png` | intact | as above (`diagram-v2.png`) |
| `06-factory-mes-industrial` | `output/diagrams/diagram.png` | **broken** — the file no longer exists, and the recorded hash matches neither `diagram-v11.png` nor `diagram-v12.png` | re-validate the current image |
| `09-analytics-gcp-shared-vpc` | — | no validation recorded | initial validation |
| `10-power-platform-governed` | — | no validation recorded | initial validation |
| `11-aliyun-landing-zone` | — | no validation recorded | initial validation |

`tests/test_validation_bindings.py` guards this table: a newly dangling or
mismatched binding fails CI, and `06` is acknowledged as the known-broken case.

## Hard rules

- **Never hand-edit** scores or findings in `validate_result.json`, and never
  invent a `source.sha256`. The skill's output is predecessor evidence.
- `tests/test_example_artifacts.py::test_recorded_enforcement_decisions_replay`
  re-runs `enforce` over the recorded validation and requires the recorded
  decision **and reasons** to match — a fabricated validation fails CI.
- A re-render can legitimately change the decision (`BLOCK` → `WARN`, or the
  reverse). Record whatever the gate actually produces.
- Record artifacts under the **workflow artifact name** from
  `standards/workflow.yaml` (`diagram.png`, `validate_result.json`,
  `enforce_result.json`) even when the file is versioned. Example 06 already
  records the name `diagram.png` against the path
  `output/diagrams/diagram-v11.png`.

## Procedure (per example)

Let `EX=examples/<id>`, `V=<N>` the diagram version, and `IMG=$EX/output/diagrams/diagram-v$V.png`.

### 1. Render the image (deterministic, reproducible)

```bash
python -m archharness diagram -i $EX/output/designs/blueprint.yaml \
    -o $EX/output/diagrams/diagram-v$V.drawio \
    --d2 $EX/output/diagrams/diagram-v$V.d2 \
    --png $IMG --png-engine d2 --d2-scale 0.2
```

### 2. Validate the image (human step — LLM vision)

Attach `$IMG` and run the `arch-validate` skill. It writes `validation/v1` to
`$EX/output/validation/validate_result.json` and must set `source.path`
(project-relative, POSIX separators), `source.sha256`, `source.ruleset_digest`,
and `source.validated_at`. Confirm the hash independently:

```bash
python -c "import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" $IMG
```

### 3. Gate deterministically

```bash
python -m archharness enforce \
  --validation $EX/output/validation/validate_result.json \
  --output $EX/output/validation/enforce_result.json
```

### 4. Sanity-check the evidence

```bash
python -m archharness validate-check -v $EX/output/validation/validate_result.json \
  -r $EX/output/requirements/req.yaml -b $EX/output/designs/blueprint.yaml
python -m archharness trace-check -r $EX/output/requirements/req.yaml \
  -b $EX/output/designs/blueprint.yaml
python -m archharness backlog -v $EX/output/validation/validate_result.json \
  -r $EX/output/requirements/req.yaml -b $EX/output/designs/blueprint.yaml \
  -o $EX/output/reports/backlog.md
```

### 5. Re-record provenance

`archharness manifest` builds the `artifact/v1` document; `workflow record`
binds it to a workflow artifact name.

```bash
# image — workflow name "diagram.png", versioned path
python -m archharness manifest --file $IMG --id diagram.png \
  --type technical-deployment-view --schema diagram/png \
  --input blueprint.yaml -o /tmp/diagram.manifest.json
python -m archharness workflow record --name diagram.png --file /tmp/diagram.manifest.json

# validation result
python -m archharness manifest --file $EX/output/validation/validate_result.json \
  --id validate_result.json --type validation-result --schema validation/v1 \
  -o /tmp/validate.manifest.json
python -m archharness workflow record --name validate_result.json --file /tmp/validate.manifest.json

# enforcement decision (record the decision document itself)
python -m archharness workflow record --name enforce_result.json \
  --file $EX/output/validation/enforce_result.json

python -m archharness workflow complete validate
python -m archharness workflow complete enforce
```

### 6. Verify and update the matrix

```bash
python -m archharness workflow verify
python -m archharness migrate-status
python -m archharness metrics --project <id>
```

Update the Status column in `examples/README.md` if it changed, and remove the
example from `KNOWN_UNRESOLVED` in `tests/test_validation_bindings.py`.

## Determinism

Everything except step 2 is a deterministic transformation of committed inputs.
The image, the manifest, and the gate decision are reproducible byte-for-byte
from the same model and policy; only the standards review needs a model.
