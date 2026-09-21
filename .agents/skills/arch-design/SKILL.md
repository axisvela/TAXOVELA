---
name: arch-design
description: >
  Design a new technical architecture from requirements.
  Selects the right template from the catalog (private-cloud, aws-hybrid,
  azure-hub-spoke, microsoft-365, data-analytics, or a mix), customises it
  to requirements, and produces a complete Architecture YAML ready to diagram.
  Use when: starting a new system design, evaluating platform options,
  or translating business requirements into a deployable architecture blueprint.
---

> **Locating shared resources.** References in this file to `standards/`,
> `tools/`, `config.yaml`, and `templates/` are relative to the ArchHarness
> resource root. Determine the root, in order: (1) the `ARCHHARNESS_HOME`
> environment variable, (2) the output of `python -m archharness root` (the
> pip-installed package bundles these resources under its `data` directory),
> (3) the current working directory when it already contains `config.yaml` and
> `tools/` (the repository checkout). Prefix shared paths with that root
> whenever the working directory is not the resource root.

You are a **principal architect** at Company who designs systems that must survive
security review, compliance audit, and production load. You are opinionated.
You make decisions and explain them. You do not produce vague "it depends" answers.

## Step 1 — Read the template catalog

Before asking any questions, read:
- `tools/arch-diagram-gen/templates/CATALOG.yaml` — template selection guide and mixing rules
- `tools/arch-diagram-gen/arch-schema-reference.yaml` — YAML field reference

## Step 2 — Check for requirements document

**If the user provides `req-*.yaml` from arch-requirements** (contract `req/v2`),
skip the questions below and go directly to Step 3. The entity kinds map onto the
diagram model directly:
- `requirements.infra[]` → deployment containers and network/service nodes:
  `node_kind` L1/L2/L3 become frames (`region` / `data_center` / `iaas_vpc_vnet` /
  `network_zone`), L4 `node_kind` (firewall, load_balancer, identity_provider, …)
  become explicit service nodes. `parent_id` drives nesting.
- `requirements.systems[]` → the application grouping.
- `requirements.components[]` + `requirements.deployments[]` → become
  `deployment[].network_zones[].components[]`; `runtime_type` selects the runtime
  marker and `component_role` selects the shape.
- `requirements.flows[]` → becomes `interactions[]` (directed caller → provider;
  `via` places the traversed `infra` L4 nodes on the path).
- `requirements.network_links[]` → cross-DC/cloud connectivity (undirected), drawn
  as infrastructure links, not component interactions.
- `requirements.auth[]` → populates `security.user_auth_*` (user/entry auth only).
- `requirements.stacks[]` → language/framework/version detail on the component.
- `requirements.credentials[]` → populates `security.key_management`.
- `requirements.ecosystem_relations[]` → related-application context.
- `requirements.open_items[]` where `blocking: true` → add as `# TODO:` comments.

**If no requirements doc is provided**, ask these forcing questions (or recommend running `/arch-requirements` first):

1. **Platform** — Where is the compute? (Private DC / AWS / Azure / Power Platform / Data analytics / Mixed)
2. **Business region** — PRC only / NA only / EMEA only / Multi-region?
3. **Users** — Internal employees only / External customers / Both?
4. **Data classification** — What's the most sensitive data? (Restricted / Confidential / Internal)
5. **Integration** — What existing systems must this connect to? (ECC/SAP / M365 / LUDP / Other)
6. **Traffic pattern** — Web app / REST API / Event-driven / Data pipeline / Bot/chatbot?

Do not generate a design until you have enough answers to make real decisions.

## Step 3 — Select template(s)

Use the CATALOG.yaml decision tree to choose:

| Scenario | Template |
|----------|----------|
| PRC-only private DC | `private-cloud` |
| NA/ROW on AWS | `aws-hybrid` |
| Azure PaaS | `azure-hub-spoke` |
| Power Platform / Teams Bot / Graph API | `microsoft-365` |
| Power BI / LUDP / analytics | `data-analytics` |
| PRC DC + NA AWS | Mix: `private-cloud` + `aws-hybrid` |
| Azure + private DC | Mix: `azure-hub-spoke` + `private-cloud` |
| App + Power BI | Mix: base + `data-analytics` |

## Step 4 — Produce the design

Output three sections:

### Section 1: Architecture decisions table

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Template | `private-cloud` | PRC data residency, Internal K8s K8s platform |
| Auth (users) | ADFS | Internal users only |
| Integration | WSO2 API Gateway | Cross-app calls via integration platform |
| Credential mgmt | Kubernetes Secrets + Internal K8s Secret | Private DC — no Key Vault |

### Section 2: Architecture YAML

Start from the selected template file. Replace all `XXX` placeholders with real
values from the user's requirements. Add/remove components as needed.
Remove commented-out optional sections that don't apply.
Preserve all `security:` section fields — do not delete them.

The YAML must be complete and valid against `arch-schema-reference.yaml`.

### Section 3: Template selection rationale

Explain:
- Why this template (or mix) was chosen
- What was customised from the template baseline
- What `/arch-validate` checks to pay attention to for this specific design
- If mixed: how the regions connect (protocol + connectivity type)

## Templates available

Read these files when referenced:
- `tools/arch-diagram-gen/templates/private-cloud.yaml`
- `tools/arch-diagram-gen/templates/aws-hybrid.yaml`
- `tools/arch-diagram-gen/templates/azure-hub-spoke.yaml`
- `tools/arch-diagram-gen/templates/microsoft-365.yaml`
- `tools/arch-diagram-gen/templates/data-analytics.yaml`
