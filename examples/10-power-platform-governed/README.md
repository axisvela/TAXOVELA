# Example 10 — Expense Approval App: Governed Power Platform + On-Premises Backend

Reverse-engineered from a real business-authored app programme. Demonstrates the
**Microsoft SaaS** pattern in its most instructive form: the tenant is a black
box, so the diagram shows a **tenant container with environments as zones**, one
boundary component (the on-premises data gateway) as the only way in, a DLP
policy as a first-class governance node, and Acme Restricted data that never
leaves the company database.

> **Name policy:** `input/systems-registry.md` is the only file that contains
> literal entity names. Every other file — `input/prompt.md`,
> `input/documents/requirements.md`, `README.md`, `config.yaml` — references
> typed codes only (`INF-` infra · `APP-` systems · `CMP-` components · the
> `DEP`/`FLOW`/`LNK`/`AUTH` derived layers).

## Scenario

**APP-01 (EXP)** is a canvas app a business team maintains itself. It holds
approval state in Dataverse (CMP-03) and submits approved expenses to the
company backend through the on-premises data gateway (CMP-04).

- **Power Platform tenant** (`power-platform-tenant`, `power_platform`)
  - Production environment (INF-02): CMP-01 app, CMP-02 flow, CMP-03 Dataverse
  - Governance and identity (INF-03): Entra ID (INF-04), DLP policy (INF-05)
- **Primary DC** (INF-06, `private_dc`)
  - DMZ (INF-07): boundary firewall (INF-08), gateway host (CMP-04)
  - App Zone (INF-09): expense service (CMP-05), expense database (CMP-06),
    enterprise vault (INF-10)
- **Relay**: LNK-01, outbound-only from the tenant; no inbound listener and no
  private circuit

## What it demonstrates

| Pipeline stage | Highlight |
|---|---|
| `arch-design` | Pick the `power-platform` template; a tenant container, not a network |
| `E-MS-001` | No customer network segmentation inside the tenant; one boundary component |
| `E-MS-002` | Entra ID as the only identity source, certificate credentials, no client secrets |
| `E-MS-003` | Environment separation with DLP classification and a data gateway instead of an open database port |
| accuracy rules | Every flow names protocol and authentication; the firewall hop sits in `via` |
| traceability | `trace-check` joins every blueprint node to the inventory and a deployment |

## Inputs

- `input/systems-registry.md` — seven typed tables (infra / systems / components /
  deployments / flows / network links / auth)
- `input/prompt.md` — coded one-shot prompt (Path A)
- `input/documents/requirements.md` — structured requirements (Path B)

## Name policy

| Artifact | Policy |
|---|---|
| `input/systems-registry.md` | The only file with literal names: the code-to-name mapping and source of `文档用名` values. |
| `input/prompt.md` | Coded one-shot prompt. Resolve every code through the registry. |
| `input/documents/requirements.md` | Coded structured requirements. |
| IP addresses | None present in the maintained documents. |

## Diagram artwork

| Artifact | What it is |
|---|---|
| `output/diagrams/diagram-v1.drawio` / `.d2` / `.png` | Rendered from the committed blueprint. |

The diagram is regenerated, not hand-edited:

```bash
python -m archharness diagram -i output/designs/blueprint.yaml \
    -o output/diagrams/diagram-v2.drawio --d2 output/diagrams/diagram-v2.d2 \
    --png output/diagrams/diagram-v2.png
```

## Validation state

This example ships **without** a `validate_result.json`: validation needs the
vision step (`/arch-validate` on a rendered image), so the record is produced
when the example is reviewed rather than fabricated here. Everything that can be
decided deterministically already passes:

```bash
python tools/registry_check.py .
python -m archharness req-validate output/requirements/req.yaml
python -m archharness arch-check -i output/designs/blueprint.yaml
python -m archharness trace-check -r output/requirements/req.yaml \
    -b output/designs/blueprint.yaml
```
