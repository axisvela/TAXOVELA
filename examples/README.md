# ArchHarness Examples

End-to-end, runnable examples for the full ArchHarness pipeline
(`requirements → design → diagram → validate → enforce → security/review → optimize → report`)
across typical enterprise deployment patterns.

Every example is self-contained:

```
examples/<id>/
├── README.md                     # Scenario, what it demonstrates, how to run
├── project.yaml                  # project id / platform / data classification
├── config.yaml                   # Example-specific infrastructure overlay
│                                 # (deep-merged on top of the root config.yaml
│                                 #  by tools/config_loader.py — innermost wins)
├── input/
│   ├── systems-registry.md       # ★ The ONLY file with literal names
│   ├── prompt.md                 # Path A: coded one-shot prompt
│   ├── documents/requirements.md # Path B: structured requirements document
│   ├── diagrams/                 # Original reference image (restricted; not scrubbed)
│   └── api/                      # (some examples) CMDB export CSV
└── output/                       # Golden outputs = expected pipeline results
    ├── requirements/  designs/  diagrams/  validation/  reports/
```

Every file outside `systems-registry.md` — including `README.md` and
`config.yaml` — references entities by **typed code** only:
`INF-` infra · `APP-` systems · `CMP-` components · `DEP-` deployments ·
`FLOW-` flows · `LNK-` network links · `AUTH-` user/entry auth · `STK-` stacks.

## Example matrix

| # | Example | Scenario | Deployment | Status |
|---|---------|----------|-----------|--------|
| 01 | `01-ecommerce-azure` | E-commerce platform network | Azure multi-region Hub-Spoke + ExpressRoute | `reqv2-complete` — typed inventory and v2 diagram rendered; historic validation remains bound to v1 diagram |
| 02 | `02-ai-agent-hybrid` | Data Agent platform (GDA) | Private DC + Azure hybrid | `reqv2-complete` — blueprint and requirements on typed ids; v2 diagram awaits re-validation |
| 03 | `03-order-query-aws-hybrid` | Order query over EDW data | AWS VPC (3-tier) + 4 private DCs | `reqv2-complete` — typed inventory and v2 diagram rendered; historic validation remains bound to v1 diagram |
| 04 | `04-service-delivery-private-cloud` | Service delivery platform (SDP) | Private cloud, 4 DCs + Azure | `reqv2-complete` — 208 registry rows; v2 diagram awaits re-validation |
| 05 | `05-supply-chain-order-private-cloud` | Supply-chain order platform (OSP) | Private cloud active-active CN+NA | `reqv2-complete` — blueprint migrated to typed ids; v2 diagram awaits re-validation |
| 06 | `06-factory-mes-industrial` | **Factory MES (PlantMES)** | Plant edge + central DCs | `reqv2-complete` — worked reference |
| 07 | `07-finance-core-banking` | Core banking / payments | Private cloud, two-site-three-center | `scaffold` — input pending |
| 08 | `08-telecom-bss` | Telecom BSS / charging | Hybrid | `scaffold` — input pending |
| 09 | `09-analytics-gcp-shared-vpc` | Analytics API (ANA) | Google Cloud Shared VPC + on-prem ERP | `reqv2-complete` — validation record pending a vision review |
| 10 | `10-power-platform-governed` | Expense approval app (EXP) | Governed Power Platform + on-prem backend | `reqv2-complete` — validation record pending a vision review |

The Status column starts with a migration token — `scaffold`, `reqv1`,
`reqv2-partial`, or `reqv2-complete` — measured by
`python -m archharness migrate-status`. `tests/test_migration_status.py` fails
when this table and the measured state disagree, so the backlog cannot drift.

Example 06 is the reference for the current model: seven-table registry,
`req/v2` requirements, a blueprint whose components carry explicit roles, and a
versioned diagram (`diagram-v<N>.drawio` / `.png`).

## How to run an example

```bash
# From the example directory — its config.yaml automatically overlays the root one
cd examples/<id>

# Path A — coded one-shot prompt:
#   use input/prompt.md + input/systems-registry.md (the registry is required context)

# Path B — structured document:
archharness req --doc input/documents/requirements.md -o req.yaml
# then: arch-design → arch-diagram → arch-validate → arch-security / arch-review
#       → arch-optimize → arch-report

# Verify what is committed
python ../../tools/registry_check.py .                      # registry ↔ docs
python -m archharness req-validate output/requirements/req.yaml
python -m archharness diagram -i output/designs/blueprint.yaml \
    -o output/diagrams/diagram-v<N+1>.drawio --png output/diagrams/diagram-v<N+1>.png
```

Generated diagrams are **versioned, not overwritten** — each run writes the next
`diagram-v<N+1>.*` so an earlier render stays available for comparison.

## Semantic roles in a blueprint

Diagram meaning comes from the model, not from word matching:

| Role | Declaration | Effect |
|---|---|---|
| Zone-boundary firewall | `role: zone_boundary` | Not drawn; the zone is marked `· FW` and flows are declared directly between the components that talk (rule R-INF-4) |
| Service provider | `role: service_provider` | Every edge points into it (producers and consumers both call a broker) |
| Logical group | `group: "<name>"` | Members fold into one named dashed frame |

Recognition is policy-driven (`standards/diagram-roles.yaml`): explicit attribute,
then structural signals, then optional name patterns — empty by default, because
matching on words is not portable. Edge labels use the shared code vocabulary in
`standards/diagram-codes.yaml` (`P-*` protocols, `AU-*` authentication).

## Sensitive-data policy

Examples are reverse-engineered from real-world reference diagrams. The
reference images are intentionally **not scrubbed** and must remain restricted
to the authorized environment; do not publish or redistribute them. They are
deliberately **not committed**.

Entity names are compiled into `systems-registry.md` — the only file that
contains them. All other files reference codes. `config.yaml` is the exception by
design: it is the deployment configuration overlay and names the platform
products (`platforms:`) the organization runs.

**IP addresses and CIDR blocks are removed from all textual documents** — subnet
and zone names are kept instead. CMDB IDs use the masked form `A-XXXX-nn`.

Validate registry consistency with:

```bash
python tools/registry_check.py examples/06-factory-mes-industrial
```
