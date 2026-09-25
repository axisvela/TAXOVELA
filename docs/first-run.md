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

The PNG is rendered by the **d2 CLI by default** (matplotlib is the fallback
when d2 is absent); the `.drawio` file is the editable source, not the image
renderer. `--png-engine drawio` opts into a draw.io PNG render instead.

A very large diagram can exhaust d2's raster backend at full size, so pass
`--d2-scale 0.2` (or render the `.d2` yourself with `d2 --scale`) to bring it
back; `--d2-timeout` raises the export timeout when a big diagram needs longer.

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

`archharness metrics` rolls the same artifacts up into a `metrics/v1` summary —
workflow completion, findings by category, routing readability, and stage
turnaround — with counts and standard labels only, no architecture payloads:

```bash
archharness metrics --project orders --json -o metrics.json
```

See [docs/pamp-integration.md](pamp-integration.md) for using that roll-up as a
governance-dashboard feed.

## 10. Keep the pipeline honest

```bash
archharness workflow can design        # may this stage start?
archharness workflow verify            # do the recorded artifacts match disk?
```

Recorded artifacts are hash-verified, not just named: editing a diagram
underneath a recorded decision fails the gate closed.

---

## Platform recipes

Each recipe is the shortest path from a platform standard to a model that
passes `arch-check` and `trace-check`: the template to copy, the placement
rules that trip people up, and a worked example. The region kind is the
`type:` of the top-level `deployment[]` entry; its zones hold the workloads.

### Private cloud — `standards/private-cloud-standard.yaml`

- **Template** `templates/private-cloud.yaml`; region kind `private_dc`.
- **Zones** `DMZ` / `App Zone` / `DB Zone` (Hohhot three-tier) or `DMZ` /
  `Intranet` (Shenyang two-tier). Web servers only in the DMZ; a DB is never
  in the DMZ.
- **Ingress** `Internet → [Anti-DDoS] → F5 → DMZ web → App Zone → DB Zone`.
  F5 is mandatory; nothing reaches the public network without it.
- **East–west** default deny. App-to-app goes through the integration platform,
  never straight to another application's database.
- **Identity** ADFS for internal users, Enterprise ID for external; permissions
  enforced by the AuthZ platform. **Secrets** have no central vault here: use
  OS-level encrypted storage, Windows DPAPI, a JKS/PKCS#12 keystore, or a
  Kubernetes Secret with encryption at rest — and never store a key beside the
  data it protects.
- **Ops** all administrative access via PAW; no public SSH/RDP.
- **Worked example** `examples/06-factory-mes-industrial` (dual-site, three-tier).

### AWS — `standards/aws-standard.yaml`

- **Template** `templates/aws-hybrid.yaml`; region kinds `private_dc` and
  `aws_vpc` (one per hub/spoke).
- **Topology** Hub–Spoke is mandatory; one hub VPC per physical Region; prod
  and non-prod in separate accounts and hub VPCs.
- **Ingress** `Internet → ALB (WAF) → backend via PrivateLink`; partner APIs add
  the WSO2 API Gateway in the **spoke** VPC, never the hub.
- **Egress** every spoke's egress goes through the hub firewall, default deny.
- **Placement** no workloads in public subnets, no public IPs; managed services
  (RDS/S3/DynamoDB) reachable only through VPC endpoints.
- **Identity / secrets** IAM roles, no hard-coded credentials; Secrets Manager
  plus KMS with rotation.
- **Worked example** `examples/03-order-query-aws-hybrid`.

### Azure — `standards/azure-standard.yaml`

- **Template** `templates/azure-hub-spoke.yaml`; region kind `azure_vnet`
  (hub, spoke, and an optional `private_dc` for on-prem integration).
- **Topology** Hub–Spoke is mandatory; one hub per Region; prod and non-prod in
  separate subscriptions.
- **Ingress** `Internet → App Gateway (WAF v2) → backend (Private Endpoint)`;
  partner APIs add APIM in Internal VNET mode in the **spoke**.
- **Egress** every spoke's egress goes through the hub firewall.
- **Placement** no public-subnet workloads, no public IPs; all PaaS via Private
  Endpoint + Private DNS; an NSG on every subnet.
- **Identity / secrets** Managed Identity only; Key Vault is mandatory with
  soft-delete and purge protection. **Ops** Azure Bastion is the only jump host.
- **Worked example** `examples/01-ecommerce-azure`.

### Google Cloud — `standards/gcp-standard.yaml`

- **Template** `templates/gcp-hub-spoke.yaml`; region kind `gcp_vpc` (host
  project + service project).
- **Topology** Organization → Folder → Project. A project is an IAM boundary,
  **not** a network boundary; production gets its own project. Subnets are
  regional: one subnet covers every zone of that Region, so plan subnets, not
  per-zone networks.
- **Ingress** `Internet → global external HTTPS LB + Cloud Armor → workloads`;
  a workload never holds an external IP.
- **Egress** workloads → Cloud NAT; a workload with no egress need gets no
  external IP at all.
- **Placement** GKE private clusters; data services (BigQuery/GCS/Spanner)
  inside a VPC Service Controls perimeter.
- **Identity / secrets** people via Cloud Identity federated to the enterprise
  IdP; workloads via service accounts with Workload Identity Federation (no
  long-lived keys); Secret Manager + Cloud KMS (CMEK), keyed per environment
  and data grade.
- **Worked example** `examples/09-analytics-gcp-shared-vpc`.

### Alibaba Cloud — `standards/aliyun-standard.yaml`

- **Template** `templates/aliyun-landing-zone.yaml`; region kind `aliyun_vpc`
  (central VPC + business VPC, joined by CEN).
- **Topology** resource directory with separate accounts for prod and non-prod;
  the central account holds the shared network and security services. A vSwitch
  is bound to one availability zone, so multi-AZ production needs several
  vSwitches.
- **Ingress** `Internet → Anti-DDoS → WAF → SLB/ALB → workloads`; no workload
  holds an EIP.
- **Egress** workloads → NAT gateway; cross-VPC and cross-Region traffic goes
  through CEN only, never a public endpoint.
- **Placement** ECS/ACK with no public IP; RDS/PolarDB/OSS via private endpoint
  and whitelist; Flow Logs on every VPC.
- **Identity / secrets** RAM users federated to the enterprise IdP with MFA;
  workloads assume RAM roles with STS tokens (long-lived AccessKeys are
  prohibited); KMS Secrets Manager + CMK per data grade.
- **Worked example** `examples/11-aliyun-landing-zone`.

### Microsoft SaaS — `standards/microsoft-saas-standard.yaml`

- **Templates** `templates/power-platform.yaml`, `templates/dynamics-365.yaml`,
  `templates/microsoft-365.yaml`; region kinds `m365_tenant`, `power_platform`,
  `dynamics365`.
- **Model it as a black box.** Each product is its own region container; the
  zones are workloads (Exchange Online / SharePoint / Teams) or environments
  (dev / test / prod). Never draw DMZ / App Zone / DB Zone inside a SaaS
  region.
- **Boundary** every integration enters and leaves through one boundary
  component; on-premises systems connect through an on-premises or VNet data
  gateway hosted on the **customer** side.
- **Identity** Entra ID is the only identity source; MFA and Conditional Access
  for people, PIM for privileged roles, no tenant-local accounts. Workload
  identity is an app registration with a certificate or managed identity —
  never a plaintext client secret.
- **Secrets** Entra ID certificates plus Key Vault for customer-side connection
  strings; platform credentials never appear in the blueprint.
- **Governance** a Power Platform DLP policy classifies every connector
  (Business / Non-Business / Blocked); a sandbox holding production data gets
  the same controls as production.
- **Worked example** `examples/10-power-platform-governed`.

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
