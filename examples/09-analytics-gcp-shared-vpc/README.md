# Example 9 — Analytics API (ANA): Google Cloud Shared VPC + On-Premises Hybrid

Reverse-engineered from a real analytics platform migration. Demonstrates the
**Google Cloud Shared VPC** pattern with an on-premises system of record:
a host project that owns the network, workloads in shared subnets, Cloud Armor
in front of a global HTTPS load balancer, Cloud NAT egress, Cloud Interconnect
to the DC, and a data tier inside a VPC Service Controls perimeter with CMEK.

> **Name policy:** `input/systems-registry.md` is the only file that contains
> literal entity names. Every other file — `input/prompt.md`,
> `input/documents/requirements.md`, `README.md`, `config.yaml` — references
> typed codes only (`INF-` infra · `APP-` systems · `CMP-` components · the
> `DEP`/`FLOW`/`LNK`/`AUTH` derived layers).

## Scenario

**APP-01 (ANA)** is an internal analytics API. It serves queries from the
BigQuery warehouse (CMP-03) and is fed by a loader (CMP-02) that stages ERP
extracts (CMP-04) produced by the on-premises extract service (CMP-05) from the
ERP system of record (CMP-06).

- **Google Cloud Shared VPC** — the host project (INF-01) owns the network:
  - Shared ingress subnet (INF-02): INF-08 Cloud Armor → INF-09 global HTTPS LB
  - Shared egress subnet (INF-03): INF-10 Cloud NAT, INF-11 Cloud Interconnect
  - Private runtime subnet (INF-04): CMP-01 and CMP-02 on a GKE private cluster
    (the cluster is their runtime, not an infra node)
  - Private data subnet (INF-05): CMP-03 BigQuery and CMP-04 staging with CMEK,
    plus INF-12 Secret Manager
- **Primary DC** (INF-06, `private_dc`) with zone INF-07 Intranet holding CMP-05,
  CMP-06, and the enterprise directory (INF-13)
- **Hybrid path**: LNK-01 Cloud Interconnect with IPSec; no direct database
  replication

## What it demonstrates

| Pipeline stage | Highlight |
|---|---|
| `arch-design` | Pick the `gcp-hub-spoke` template; one host project owns the network |
| accuracy rules | `E-GCP-001` Shared VPC present, `E-GCP-002` LB + Cloud Armor entry, `E-GCP-003` data services in the perimeter with CMEK |
| interaction rules | Every flow carries protocol + authentication; the entry hops appear in `via` |
| security rules | OIDC/SAML at the directory, cert-based ERP boundary, Secret Manager for runtime credentials |
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
