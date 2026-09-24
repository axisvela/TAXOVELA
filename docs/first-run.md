# First run: from clone to a governed diagram

This walkthrough takes a new team from a fresh checkout to a diagram that has
passed the deterministic gate. Every step names the command that proves it
worked, and every command is offline and repeatable.

The reference for what "finished" looks like is
[`examples/06-factory-mes-industrial`](../examples/06-factory-mes-industrial):
seven-table registry, `req/v2` requirements, a blueprint whose nodes carry
typed codes, and a versioned diagram.

---

## 1. Install and check the installation

```bash
pip install -e .            # or: pip install "archharness[all]"
archharness --version
archharness root            # → the resource root holding config.yaml + standards/
archharness doctor
```

`doctor` does not just look for directories. It loads the gate policy and every
profile it declares, the workflow spec, the `req/v2` schema, and the diagram
style, and prints the loader's own message when one of them is broken:

```
  governance:
  [ok]  gate policy (profiles: baseline, production, poc; block < 6.0)
  [ok]  workflow spec (9 stages)
  [ok]  req/v2 schema (15 definitions)
  [ok]  diagram style (11 standard shapes; 3 roles)
```

## 2. Configure the organisation profile

Edit [`config.yaml`](../config.yaml) before the first project: company name,
classification prefix, data centres, and platform names. Nothing else in the
repository hard-codes them.

## 3. Create a workspace and a project

```bash
archharness init-workspace .
archharness init-project orders --name "Order Platform" --platform private_cloud --default
```

`init-project` scaffolds startable inputs under `projects/orders/`:
`input/systems-registry.md` (seven tables, one placeholder row each),
`input/prompt.md` (a coded one-shot prompt citing them), and a `README.md`
quick start. A fresh project already passes the registry checker:

```bash
python tools/registry_check.py projects/orders
# → OK (6 registry rows …, 3 codes cited)
```

Existing files are never overwritten, so re-running is safe.

## 4. Describe the system

Fill `input/systems-registry.md` first: it is the only file that contains
literal entity names. Everything else — `prompt.md`, `documents/`, `README.md`,
`config.yaml` — cites typed codes (`INF-` / `APP-` / `CMP-` and the
`DEP`/`FLOW`/`LNK`/`AUTH` derived layers).

Two rules keep the model checkable:

- a firewall, WAF, router, VPN gateway, identity provider, or key manager is an
  **infra** node (`INF-`), never a component;
- an external system gets an `APP-` row *and* one boundary `CMP-` row, so its
  flows have a component endpoint.

Then re-run the checker; it reports every code cited in the documents that the
registry does not define:

```bash
python tools/registry_check.py projects/orders
```

## 5. Gather requirements

```bash
archharness req --doc projects/orders/input/documents/requirements.md \
    -o projects/orders/output/requirements/req.yaml \
    --report projects/orders/output/validation/gap-report.md
archharness req-validate projects/orders/output/requirements/req.yaml
```

`req` reads documents, diagrams, and CMDB exports and merges them into one
`req/v2` document; the gap report lists what still has to be answered. You can
also read an existing architecture back into requirements:

```bash
archharness req --diagram projects/orders/output/designs/blueprint.yaml -o req.yaml
```

## 6. Design

Ask the design skill for a blueprint, or adapt one of the example blueprints.
Then check the model before drawing it:

```bash
archharness arch-check -i projects/orders/output/designs/blueprint.yaml
```

`arch-check` decides the objectively verifiable rules from the model itself —
duplicate ids, undeclared endpoints, a flow with no protocol or authentication
label, an unknown lifecycle status — and prints a rule id with each finding.

## 7. Draw

```bash
archharness diagram -i projects/orders/output/designs/blueprint.yaml \
    -o projects/orders/output/diagrams/diagram-v1.drawio \
    --d2 projects/orders/output/diagrams/diagram-v1.d2 \
    --png projects/orders/output/diagrams/diagram-v1.png
```

The same YAML always produces the same XML, so diagrams are reviewable in
version control. `--routing-diagnostics routes.json` records per-edge routing
strategy, lane, waypoint count, and whether a route fell back to draw.io.

If a node cannot be drawn, the generator stops and says which one — an
interaction endpoint must be a component, region, or zone of the deployment.

## 8. Validate

Ask the validation skill for a `validation/v1` result, then check that its
findings are joinable to the model:

```bash
archharness validate-check -v projects/orders/output/validation/validate_result.json \
    -r projects/orders/output/requirements/req.yaml \
    -b projects/orders/output/designs/blueprint.yaml
archharness trace-check -r projects/orders/output/requirements/req.yaml \
    -b projects/orders/output/designs/blueprint.yaml
```

- `trace-check` proves every blueprint node resolves to the requirements
  inventory and to a deployment;
- `validate-check` proves every finding cites an element that exists — a
  finding may also name the field it is about (`CMP-03.encryption_at_rest`),
  which is verified against the schema.

## 9. Gate and remediate

```bash
archharness enforce --validation projects/orders/output/validation/validate_result.json
# → decision: BLOCK (profile baseline)   exit 1
archharness enforce --validation ... --profile production
archharness backlog -v projects/orders/output/validation/validate_result.json \
    -r projects/orders/output/requirements/req.yaml \
    -b projects/orders/output/designs/blueprint.yaml -o backlog.md
archharness workflow status
```

The gate is deterministic: identical inputs always produce the same decision.
A profile may tighten the baseline freely; a looser one has to declare
`allow_looser: true` with a rationale. `backlog` orders the findings by
severity and disposition and groups them by the element that has to change.

## 10. Keep the pipeline honest

```bash
archharness workflow can design        # may this stage start?
archharness workflow verify            # do the recorded artifacts match disk?
```

Recorded artifacts are hash-verified, not just named: editing a diagram
underneath a recorded decision fails the gate closed.

---

## When something goes wrong

| Symptom | Diagnose with | Usual fix |
|---|---|---|
| `doctor` reports a governance problem | `archharness doctor` | the message names the file and the loader error |
| A code is cited that the registry does not define | `python tools/registry_check.py <project>` | add the row, or fix the citation |
| A blueprint node is missing from the inventory | `archharness trace-check -r … -b …` | add the `CMP-`/`INF-` row, or re-code the node |
| A stage will not start | `archharness workflow can <stage>` | the message names the missing artifact |
| `workflow verify` reports a digest mismatch | `archharness workflow verify` | re-record the artifact with `workflow record` |
| The gate blocks | `archharness enforce --validation …` | the reasons list the triggering rule |
| A finding is not actionable | `archharness validate-check -v …` | it cites nothing, or cites something that does not exist |

## Where the rules live

| Path | What it holds |
|---|---|
| `config.yaml` | organisation profile: company, data centres, platform names |
| `standards/diagram-style.yaml` | shapes, colours, zone palettes, router controls |
| `standards/workflow.yaml` | stage order and each stage's required artifacts |
| `standards/arch-gate-policy.yaml` | gate thresholds and policy profiles |
| `standards/diagram-roles.yaml` | which nodes act as boundaries and providers |
| `schemas/*.json` | the `req/v2`, `artifact/v1`, `validation/v1`, `enforcement/v1` contracts |
| `docs/example-rebuild-guide.md` | migrating a legacy example to the current model |
