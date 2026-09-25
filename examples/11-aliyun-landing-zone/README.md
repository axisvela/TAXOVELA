# Example 11 — Order Service Platform: Alibaba Cloud Landing Zone + On-Premises ERP

Reverse-engineered from a real China-region workload. Demonstrates the
**Alibaba Cloud landing zone** pattern: a central account owning the hub VPC,
business workloads in a separate VPC linked by Cloud Enterprise Network, an
Anti-DDoS → WAF → SLB ingress with no Elastic IP on any workload, NAT-only
egress, cloud-firewall east-west inspection, RAM roles with STS tokens, and a
KMS-encrypted data tier.

> **Name policy:** `input/systems-registry.md` is the only file that contains
> literal entity names. Every other file — `input/prompt.md`,
> `input/documents/requirements.md`, `README.md`, `config.yaml` — references
> typed codes only (`INF-` infra · `APP-` systems · `CMP-` components · the
> `DEP`/`FLOW`/`LNK`/`AUTH` derived layers).

## Scenario

**APP-01 (ORD)** is an order service in a China region that publishes order
status to the on-premises ERP (APP-02), which keeps the restricted data.

- **Central VPC** (`aliyun-central-vpc`, `aliyun_vpc`)
  - Edge vSwitch (INF-02): INF-10 Anti-DDoS → INF-11 WAF → INF-12 SLB
  - Shared services vSwitch (INF-03): INF-13 cloud firewall, INF-14 NAT,
    INF-15 CEN, INF-16 log service
- **Business VPC** (`aliyun-business-vpc`, `aliyun_vpc`)
  - Application vSwitch AZ-A (INF-05): CMP-01 order service
  - Application vSwitch AZ-B (INF-06): CMP-02 order service
  - Data vSwitch (INF-07): CMP-03 database, CMP-04 archive bucket, INF-17 KMS
- **Primary DC** (INF-08) with zone INF-09 holding CMP-05, CMP-06, INF-18
- **Connectivity**: LNK-01 business VPC to hub through CEN; LNK-02 Express
  Connect with IPSec to the DC

## What it demonstrates

| Pipeline stage | Highlight |
|---|---|
| `arch-design` | Pick the `aliyun-landing-zone` template; two VPCs, one inspected hub |
| `E-ALI-001` | Resource directory with a central VPC and CEN as the only interconnect |
| `E-ALI-002` | Anti-DDoS → WAF → SLB entry; no workload holds an Elastic IP |
| `E-ALI-003` | RAM roles with STS tokens; KMS secret manager; no long-lived AccessKey |
| accuracy rules | Every flow names protocol and authentication; inspection and hybrid hops sit in `via` |
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
