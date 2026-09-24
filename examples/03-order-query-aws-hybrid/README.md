# Example 3 — Order Query Platform (OQP ROW): AWS + Multi-DC Hybrid

This req/v2 example models APP-01 as an AWS-hosted order-query application with
existing source-system boundaries across US, NA, PRC, Azure, and SaaS locations.

## What It Demonstrates

| Area | Typed model coverage |
|---|---|
| AWS three-tier VPC | INF-01 through INF-08 and CMP-01 through CMP-24 |
| Appliance policy | INF-05/INF-06/INF-07 WAF/firewalls; INF-12/INF-13 identity providers |
| Runtime policy | Internal K8s platform in DEP runtime detail, not inventory |
| Mediation | CMP-25 through CMP-32 API/Kafka boundaries |
| Residency | FLOW-10/FLOW-11 and LNK-03/LNK-04 retain PRC rows in-country |

`input/systems-registry.md` is the only file with literal entity names. All
other prose uses typed identifiers. The original reference image remains
restricted input and is intentionally not scrubbed.

## Verify

```bash
python tools/registry_check.py examples/03-order-query-aws-hybrid
python -m archharness req-validate examples/03-order-query-aws-hybrid/output/requirements/req.yaml
python -m archharness trace-check -r examples/03-order-query-aws-hybrid/output/requirements/req.yaml -b examples/03-order-query-aws-hybrid/output/designs/blueprint.yaml
```
