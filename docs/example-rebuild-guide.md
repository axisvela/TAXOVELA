# Rebuilding an Example on the req/v2 Model

Procedure for migrating one `examples/<id>/` project from the flat `SYS-nn`
registry to the req/v2 entity model. Worked references: `06-factory-mes-industrial`
(done, validated), `05-supply-chain-order-private-cloud`, and
`01-ecommerce-azure` (Azure appliance/runtime/link classification).

The judgement is human; the rewriting and checking are mechanical.

---

## Step 1 — Read the source registry and classify every row

For each `SYS-nn` row decide **what the thing is**, using the three tests:

| Question | If yes |
|---|---|
| Is it a location or network/security topology node (DC, region, VNet, zone, firewall, WAF, load balancer appliance, VPN gateway, identity provider, bastion, KMS, SOC)? | `infra` (`INF-nn`) |
| Is it an application/system, or an external system seen as a black box? | `systems` (`APP-nn`) |
| Is it an application artefact (service, DB, cache, bus, API gateway, data lake, frontend)? | `components` (`CMP-nn`) |
| Is it a carrier circuit / WAN path (ExpressRoute, MPLS, VPN, peering)? | a `network_links` (`LNK-nn`) row — **not** a node |
| Is it an arrow between components? | `flows` (`FLOW-nn`) |
| Is it a user/entry login? | `auth` (`AUTH-nn`) |

Then apply these structural rules:

- **Appliance test** — firewall/WAF/router/VPN gateway/bastion/IdP/KMS/SOC are
  `infra` L4 nodes, never components. An application-layer load balancer may be
  a component with `component_role=load_balancer`.
- **Black-box systems** — an existing external system gets an `APP-nn` row *and*
  one boundary `CMP-nn` (`component_role=integration_service`) so flows have a
  component endpoint. A bare system is not enough.
- **Symmetric regions** — if CN and NA run the same logical stack active-active,
  model **one component with two deployments**, not two components. This is the
  main quality gain over `req/v1` (where `SYS-06` and `SYS-33` were separate
  "applications").
- **Site-qualified node ids in the diagram** — the requirements model carries one
  component with two deployments, but a diagram must draw one box per site, and
  two nodes sharing an id fail the duplicate-id check. Append the site:
  `CMP-03-CN` / `CMP-03-NA`, both traceable to the single `CMP-03` row. Use this
  only where the same component is deployed more than once; a component placed in
  one site keeps its bare code. `CN` maps to req/v2 country `CN`; `NA` is a
  business-site suffix and maps to deployments in `US`, `CA`, or `MX`.
  `output/` is not scanned by the registry check,
  so a qualified id is a diagram-view convention, never a registry row.
- **Derived layers** (`deployments`/`flows`/`network_links`/`auth`) are not
  inventory and are not required to be cited by `prompt.md`.

Assign typed IDs in table order: `INF-01…`, `APP-01…`, `CMP-01…`, `DEP-01…`,
`FLOW-01…`, `LNK-01…`, `AUTH-01…`, `STK-01…`.

## Step 2 — Write the seven-table registry

Replace `input/systems-registry.md` with one table per entity kind (headers
from `standards/requirements-model-v2.yaml > registry.tables`):

| Table | Columns |
|---|---|
| R1 Infra nodes | 编号 \| 参考图原名 \| node_kind \| infra_type \| network_type \| 父节点 \| 位置/国家 \| 文档用名 \| 备注 |
| R2 Systems | 编号 \| 参考图原名 \| type \| owner \| vendor \| 文档用名 \| 备注 |
| R3 Components | 编号 \| 参考图原名 \| 所属系统 \| 子系统 \| kind \| layer \| component_role \| 静态加密 \| 文档用名 \| 备注 |
| R4 Deployments | 编号 \| 参考图原名 \| 组件 \| 环境 \| deployment_type \| location_type \| infra 节点 \| runtime_type \| 实例数 \| 文档用名 \| 备注 |
| R5 Component flows | 编号 \| 参考图原名 \| 发起组件 \| 提供组件 \| protocol \| port \| auth_method \| 加密 \| 跨境 \| via \| 备注 |
| R6 Infra links | 编号 \| 参考图原名 \| 源 infra \| 目标 infra \| method \| 带宽 \| 加密 \| 管理方 \| 备注 |
| R7 Auth | 编号 \| 参考图原名 \| subject \| 适用入口 \| auth_server \| protocol \| authorization \| MFA \| 备注 |

**Choose `文档用名` values that do not already occur in the prose** — the literal
leakage check flags any doc-name found outside the registry. Avoid reusing a
location literal (e.g. do not use `dc-us-na` as a doc-name when the prose says
`dc-us-na`).

## Step 3 — Re-code the documents

Every `SYS-nn` in `input/prompt.md`, `input/documents/requirements.md`,
`README.md` and `config.yaml` becomes its typed code. Ranges are supported
(`CMP-05 through CMP-18`), which keeps the prompt readable.

`prompt.md` must cite **every in-scope inventory row** (`INF`/`APP`/`CMP`) or the
scope guard warns — close it with range lines, e.g.:

```
Systems and infra in scope: APP-01 through APP-07; INF-01 through INF-14;
CMP-01 through CMP-36.
```

`config.yaml > datacenters[].notes` is checked too (only the `platforms:` block
is ignored) — update the codes there as well.

## Step 4 — Author `output/requirements/req.yaml` in req/v2

Derive it from the registry + requirements document. Keep it schema-shaped (see
`schemas/req-v2.schema.json`). One deployment row per component × environment ×
site; `via` carries the traversed `INF` L4 nodes; service-to-service auth is the
inline `auth_method` enum.

## Step 5 — Verify

```bash
python tools/registry_check.py examples/<id>          # registry ↔ docs consistency
python -m archharness req-validate examples/<id>/output/requirements/req.yaml
python -m archharness trace-check \
    -r examples/<id>/output/requirements/req.yaml \
    -b examples/<id>/output/designs/blueprint.yaml
python -m pytest -q                                    # no regressions
```

All three must be clean. `req-validate` runs schema + rules V1–V7;
`trace-check` verifies that typed blueprint nodes resolve to req/v2 inventory
and that CN/NA site-qualified component nodes have matching deployments.

Alternatively regenerate the merged document from the readers:

```bash
python -m archharness req --diagram <arch>.yaml --doc requirements.md \
    -o output/requirements/req.yaml --report output/validation/gap-report.md \
    --manifest working/manifests/req.yaml.manifest.json
```

## Step 6 — Regenerate the derived artifacts

`output/designs/blueprint.yaml`, `output/diagrams/*`, `working/manifests/*` and
`output/validation/*` are downstream of `req.yaml`:

```bash
python -m archharness validate-yaml output/designs/blueprint.yaml
python -m archharness diagram -i output/designs/blueprint.yaml \
    -o output/diagrams/diagram-v6.drawio --png output/diagrams/diagram-v6.png
```

**Diagram naming.** Generated diagrams are versioned, not overwritten: each run
writes the next number, `diagram-v<N+1>.drawio` / `.png`. Take the highest number
already in `output/diagrams/` and add one, so an earlier render stays available
for comparison.

Validation (`validate_result.json` / `enforce_result.json`) needs the
LLM-driven `arch-validate` skill, or the deterministic gate:

```bash
python -m archharness enforce --validation output/validation/validate_result.json
```

## Step 7 — Update `examples/README.md`

Reflect the entity counts per example and the standards exercised. Leave example
07/08 as scaffolds until their reference input exists.

---

## Tracking the work

```bash
python -m archharness migrate-status          # one line per example
python -m archharness migrate-status --json   # machine-readable backlog
```

Each example resolves to `scaffold`, `reqv1`, `reqv2-partial`, or
`reqv2-complete`, and the example matrix in `examples/README.md` must agree —
`tests/test_migration_status.py` fails when the table and the measured state
diverge. Examples 02, 04, 05, and 06 measure as `reqv2-complete`; example 03 is
the remaining rebuild.

## Ordering recommendation

| Example | Effort | Note |
|---|---|---|
| 06 factory-mes | done | validated reference |
| 05 supply-chain | done | migrated; v2 diagram awaits re-validation |
| 02 ai-agent-hybrid | done | migrated; v2 diagram awaits re-validation |
| 04 service-delivery | done | migrated; 208 registry rows, v2 diagram awaits re-validation |
| 03 order-query-aws | medium | AWS standard + EDW |
| 01 ecommerce-azure | done | req/v2 rebuild; v2 diagram is rendered and historic validation remains v1-bound |
| 07/08 | blocked | awaiting reference input |
