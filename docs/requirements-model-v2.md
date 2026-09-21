# Requirements Model v2 — Entity-Separated Input Model

| | |
|---|---|
| **Status** | DRAFT — for review |
| **Target contract** | `req/v2` |
| **Supersedes** | `req/v1` (frozen, not modified) |
| **Reference model** | `eam-rebuild` tech-management PRDs (`01`–`07`) + `architecture-diagram-connection-plan.md` |
| **Artifacts in this change** | this document + `schemas/req-v2.schema.json` (draft) |

---

## 1. Problem with `req/v1`

`req/v1` carries the whole architecture in two flat, overloaded collections:

- **`applications[]`** — one row per "named thing": a VNET, an Azure Firewall, an
  ExpressRoute circuit, an AKS cluster, a database subnet, a data centre, a
  third-party carrier. The only discriminator is `type: new | existing`.
- **`components[]`** — keyed by `app_id`, so a component's parent is whatever the
  previous list happened to call an application.

Observed consequences (all visible in `examples/01-ecommerce-azure`):

| # | Symptom | Root cause |
|---|---|---|
| 1 | A VNET, a firewall and a database are all `applications[]` entries | topology role, hosting category and network domain collapse into one row |
| 2 | `components[]` invents layers `SEC`, `LB` for firewall / load balancer | infrastructure/security appliances are modelled as application components |
| 3 | An ExpressRoute circuit appears both as a node (`SYS-22`) **and** inside `network_connections[].type` ("ExpressRoute via SYS-22") | a link is modelled as a node and an edge at once |
| 4 | `network_connections[]` and `interactions[]` both describe connections, split by *medium* | connection semantics are not separated (component flow vs infra link) |
| 5 | Auth lives in `interactions[].auth_method`, `user_auth[]` and `credentials[]` | authentication is not a first-class entity |
| 6 | No stable join key to the target EA system | harness IDs (`SYS-nn`) are opaque |

This is exactly the anti-pattern `07-infra-topology-prd` §9.1 forbids: it requires
`node_kind` (topology role), `infra_type` (hosting category) and `network_type`
(network/security domain) to be **three separate fields**, precisely so that
"不再将三者混为同一字段职责".

---

## 2. Goals and non-goals

**Goals**

1. Separate the model by *what a thing is*, never by *where it sits*.
2. Align 1:1 with the `eam-rebuild` entity model so harness output is comparable
   with the tech-management system and traceable in both directions.
3. Give every entity a **typed, stable ID** so a reference makes its kind obvious.
4. Separate the two connection categories by semantics, not by medium:
   **component communication flow** (directed) vs **infrastructure network link**
   (undirected) — as fixed by `architecture-diagram-connection-plan.md`.
5. Make **user / entry authentication** a first-class entity; keep
   service-to-service authentication as an inline enum on flows.
6. Produce output that maps directly onto the diagram generator's node/edge model.

**Non-goals**

- Replacing CMDB / application-catalog master data (systems are *referenced*, not governed).
- Runtime state, drift detection, capacity modelling.
- Change/version governance (`change_id`, exception flows).
- EOL / vulnerability intelligence scoring.

---

## 3. Model overview

```
                         ┌───────────────────────────────────────────┐
                         │              infra  (INF-nn)              │
                         │  node_kind · infra_type · network_type     │
                         │  L1 region                                 │
                         │  L2 data_center | iaas_vpc_vnet | paas |   │
                         │     saas | third_party | office_network |  │
                         │     factory_network | lab | internet       │
                         │  L3 network_zone | subnet                  │
                         │  L4 firewall | waf | router | vpn_gateway |│
                         │     identity_provider | load_balancer |    │
                         │     bastion_host | key_management | ...    │
                         └───────────────▲───────────────────────────┘
                                         │ referenced by (never copied)
   systems (APP-nn)                      │
        │ 1                               │
        │                                 │
        ▼ *                               │
   components (CMP-nn) ────── deployments (DEP-nn) ── environment
        │  │                          deployment_type
        │  │                          location_type
        │  │                          runtime_type
        │  │                          instance_count
        │  │
        │  │ source/target            ┌────────────────────────────────┐
        └──┴──────────────────────────► flows (FLOW-nn) — DIRECTED     │
                                      │ caller → provider               │
                                      │ protocol · port                 │
                                      │ auth_method  (inline enum)      │
                                      │ encryption   (inline enum)      │
                                      │ cross_border (+ basis)          │
                                      │ via → [INF-nn L4 path, ordered] │
                                      └─────────────────────────────────┘

   infra ─(L2/L3/L4 nodes)───────────► network_links (LNK-nn)
                                      UNDIRECTED
                                      source_infra ↔ target_infra
                                      method (MPLS, ExpressRoute, …)

   components carry at-rest encryption (a component attribute):
        encryption_at_rest · key_management → INF-nn(key_management)

   auth (AUTH-nn) — USER / ENTRY authentication only
                   subject = user | application
                   entry · auth_server → INF-nn(identity_provider)
                   protocol · authorization · roles · mfa
                   (service-to-service auth is INLINE on flows)

   supporting: stacks (STK-nn) · ecosystem_relations · credentials ·
               constraints · open_items
```

Two invariants carry most of the value:

- **A component flow's endpoints are always components** (the external sentinel
  `internet` may be a *source*). Infrastructure/security nodes may appear only as
  an explicit `via` path — never as an endpoint
  (`architecture-diagram-connection-plan.md`, "Forbidden strategy B").
- **A network link's endpoints are always infra nodes.** Never components.

---

## 4. Entity kinds

Field marks: **R** = required, **C** = conditional, o = optional.

### 4.1 `infra` — hosting location & network topology (INF-nn)

Mirrors `tech_infra_node` + `tech_infra_node_attr` (`07-infra-topology-prd`).

| Field | Req | Notes |
|---|---|---|
| `id` | R | `INF-nn` |
| `name` | R | document name (registry-only literal) |
| `node_kind` | R | topology role — see enum below |
| `infra_type` | C | hosting category — see enum below |
| `network_type` | C | network/security domain — see enum below |
| `parent_id` | o | `INF-nn`; forms the L1→L2→L3 containment tree |
| `country` | o | ISO code |
| `vendor` | o | e.g. `Microsoft Azure`, `Carrier A` |
| `region_code` / `dc_code` | o | cloud region / data-centre code |
| `vpc_vnet` / `subnet_code` / `zone_code` | o | network identifiers |
| `biz_owner` / `infra_owner` | o | |
| `status` | o | `planned｜active｜restricted｜retired` |
| `notes` | o | |

**`node_kind` enum** (role, not category):

| Level | Kind | Diagram behaviour |
|---|---|---|
| L1 | `region` | top grouping |
| L2 | `data_center`, `iaas_vpc_vnet`, `paas`, `saas`, `third_party`, `office_network`, `factory_network`, `lab`, `internet_network` | site/cloud frame |
| L3 | `network_zone`, `subnet` | zone frame inside L2 |
| L4 | `firewall`, `security_gateway`, `waf`, `router`, `switch`, `vpn_gateway`, `identity_provider`, `soc_monitoring`, `load_balancer`, `bastion_host`, `logging_service`, `policy_service`, `key_management` | explicit service node |

**`infra_type` enum** — `private_cloud｜public_cloud｜saas｜third_party｜office｜factory｜lab`

**`network_type` enum** — `office_network｜factory_network｜lab_network｜prod_network｜dmz`

> **Rule R-INF-1** — `node_kind`, `infra_type` and `network_type` are three
> independent fields. No field may carry the meaning of another.
>
> **Rule R-INF-2** — firewall / WAF / router / VPN gateway / load balancer /
> bastion / identity provider / SOC / key management MUST be `infra` L4 nodes,
> never `components` (`architecture-diagram-connection-plan.md`, "Security and
> network shapes").
>
> **Rule R-INF-3** — allowed parent/child combinations follow the type policy
> matrix (`07-infra-topology-prd` §9.3), e.g.
> `public_cloud`: `region → iaas_vpc_vnet → subnet`;
> `private_cloud`: `region → data_center → network_zone/subnet`.

### 4.2 `systems` — application / system (APP-nn)

Mirrors the application-catalog reference (`02-application-catalog-dependency-prd`).

| Field | Req | Notes |
|---|---|---|
| `id` | R | `APP-nn` |
| `name` | R | |
| `type` | R | `new｜existing｜modified` |
| `owner` | o | `org_it｜biz_owned｜third_party` |
| `vendor` | C | required when `owner=third_party` |
| `lifecycle_status` | o | reference value from catalog |
| `source_system` | o | `cmdb｜manual｜servicenow｜…` |
| `description` | o | |
| `data_classification` | o | org classification label |

> Existing systems in an E2E scope are still **black boxes**: only the fields
> above plus their integration boundary are required — no internal components.

### 4.3 `components` — technical component / service (CMP-nn)

Mirrors `tech_component` (`03-components-services-prd`).

| Field | Req | Notes |
|---|---|---|
| `id` | R | `CMP-nn` |
| `system_id` | R | `APP-nn` |
| `subsystem` | o | subsystem name or `SUB-nn` |
| `name` | R | |
| `kind` | R | `service｜component` |
| `layer` | o | broad layout/filter dimension (`fe｜be｜api｜bff｜db｜mq｜ip｜…`) |
| `component_role` | C | fine-grained **shape selector** — see enum below |
| `function_desc` | o | responsibility |
| `sensitivity` | o | data sensitivity |
| `encryption_at_rest` | o | at-rest encryption for data this component stores (e.g. `AES-256`, `TDE`) — a **component attribute**, not a separate collection |
| `key_management` | o | `INF-nn` of a `key_management` L4 node holding this component's keys |
| `status` | o | `draft｜active｜deprecated｜retired` |

**`component_role` enum** (authoritative shape selector,
`architecture-diagram-connection-plan.md`):

`application_service`, `web_frontend`, `backend_service`, `bff`, `ai_agent`,
`api_gateway`, `load_balancer`, `message_bus`, `data_integration`,
`integration_service`, `database`, `cache`, `file_storage`, `object_storage`,
`metadata_store`, `data_processing`, `data_lake`, `data_warehouse`, `bi_report`,
`batch_processing`, `streaming_processing`, `large_scale_compute`

> **Rule R-CMP-1** — `layer` is a coarse filter; `component_role` drives the
> diagram shape. Never infer the shape from `layer`, language or framework.
>
> **Rule R-CMP-2** — an application-layer load balancer may be a component with
> `component_role=load_balancer`; an infrastructure appliance must be `infra` L4
> `load_balancer` instead.

### 4.4 `stacks` — component ↔ technology stack (STK-nn) *(supporting)*

Mirrors `tech_component_stack` + `tech_stack_master_data`
(`04-component-stack-mapping-prd`). Optional in v2 — needed only when EOL /
licence / vulnerability analysis is in scope.

| Field | Req | Notes |
|---|---|---|
| `id` | R | `STK-nn` |
| `component_id` | R | `CMP-nn` |
| `component` | R | technology name (`Spring Boot`) |
| `component_package` | o | package / artifact |
| `version` | R | `major.minor.patch` |
| `category` / `sub_category` | o | classification |
| `eol_date` | o | |
| `license` | o | SPDX |
| `standard_flag` | o | is the org-standard entry |

### 4.5 `deployments` — component runtime placement (DEP-nn)

Mirrors `tech_deployment` (`05-deployment-runtime-prd`). The chain is
`Application → Component → Deployment → Infra`; deployments **reference** infra
by id and never copy infra dictionaries.

| Field | Req | Notes |
|---|---|---|
| `id` | R | `DEP-nn` |
| `component_id` | R | `CMP-nn` |
| `environment` | R | `dev｜test｜staging｜prod｜dr` |
| `deployment_type` | R | `private_cloud｜public_cloud｜public_cloud_paas｜saas｜third_party` |
| `location_type` | R | `data_center｜public_cloud_region｜saas` |
| `infra_id` | C | `INF-nn`; required in `prod` |
| `runtime_type` | R | `vm｜container｜physical｜serverless` — drives the runtime marker |
| `runtime_detail` | o | e.g. K8s version |
| `instance_count` | o | |
| `network_vpc` / `network_zone` / `network_subnet` | o | override only; authoritative values resolve through `infra_id` |
| `owner` | o | |
| `status` | o | `planned｜active｜migrating｜retired` |

> **Rule R-DEP-1** — one component with N environments has N deployments; the
> diagram renders one node per deployment.
>
> **Rule R-DEP-2** — if `infra_id` is present, `deployment_type` must be
> compatible with the infra node's `infra_type`
> (`05-deployment-runtime-prd` §9.2/§9.3).

### 4.6 `flows` — component communication flow (FLOW-nn)

Mirrors `tech_component_flow`. **Directed**: caller/consumer → provider, one
arrowhead on the provider.

| Field | Req | Notes |
|---|---|---|
| `id` | R | `FLOW-nn` |
| `source_component_id` | R | `CMP-nn` (caller) — or the sentinel `internet` for external ingress |
| `target_component_id` | R | `CMP-nn` (provider) |
| `protocol` | R | `HTTPS｜Kafka｜SFTP｜JDBC｜gRPC｜RFC｜TCP｜…` |
| `port` | C | required for non-standard TCP |
| `auth_method` | R | **inline enum** — see below |
| `encryption` | o | **inline enum** — `TLS1.3｜TLS1.2｜mTLS｜IPSec｜none｜TBD` |
| `cross_border` | o | bool — does this flow cross a legal border? |
| `cross_border_basis` | C | required when `cross_border=true` (compliance basis) |
| `via` | o | ordered list of `INF-nn` L4 nodes the flow path passes through |
| `notes` | o | |

**`auth_method` enum** (inline — service-to-service auth is *not* an entity):

`OAuth2_ClientCredentials｜mTLS｜ClientCertificate｜SASL_SCRAM｜Basic｜ApiKey｜
UserPassword｜Kerberos｜IAM_Role｜ManagedIdentity｜none`

> **Rule R-FLOW-1** — endpoints MUST be components, except that the external
> sentinel `internet` may be a *source*. Routing a flow through a network-zone
> edge, data-centre anchor or infra node as an endpoint is forbidden ("forbidden
> strategy B") — it changes the relationship's meaning.
>
> **Rule R-FLOW-2** — protocol does not create a new connection category; `HTTP`,
> `Kafka`, `JDBC` remain labels on the same flow type.
>
> **Rule R-FLOW-3** — `auth_method`, `encryption` and the cross-border fields are
> **inline enums scoped to this flow**. An identity product is reached through
> `via` (or `components[].key_management`), never by embedding an `AUTH-nn`.

### 4.7 `network_links` — infrastructure network connection (LNK-nn)

Mirrors `tech_infra_network_link` (global `/infra/network-links`). **Undirected**
for visual purposes.

| Field | Req | Notes |
|---|---|---|
| `id` | R | `LNK-nn` |
| `source_infra_id` | R | `INF-nn` |
| `target_infra_id` | R | `INF-nn` |
| `method` | R | `mpls｜expressroute｜direct_connect｜vpc_peering｜vnet_peering｜vpn｜internet｜sdwan｜leased_line` |
| `bandwidth` | o | |
| `encrypted` | o | |
| `encryption_method` | C | |
| `managed_by` | o | |
| `redundancy` | o | `primary｜secondary｜backup` |
| `notes` | o | |

> **Rule R-LNK-1** — endpoints MUST be infra nodes. A carrier circuit
> (ExpressRoute/MPLS) is a **link**, not a node — it must not also appear in
> `infra`.

### 4.8 `auth` — user / entry authentication (AUTH-nn)

**Scope narrowed:** this entity models **user-facing / entry-point**
authentication only (it plays the role of v1 `user_auth[]`).
**Service-to-service authentication is inline** on each `flows` row
(`auth_method` enum) and is NOT an entity here.

The identity product itself is an infra L4 node
(`node_kind=identity_provider`); `auth.auth_server` references it.

| Field | Req | Notes |
|---|---|---|
| `id` | R | `AUTH-nn` |
| `subject` | R | `user｜application` — `application` means *application entry* auth, not service-to-service |
| `applies_to` | C | entry point: `CMP-nn` / `INF-nn` / `internet` |
| `auth_server` | C | `INF-nn` of an `identity_provider`, or a product name |
| `protocol` | R | see enum below |
| `authorization` | o | `RBAC｜ABAC｜PBAC｜DAC` |
| `authorization_platform` | o | |
| `user_roles` | C | required when `subject=user` |
| `mfa` | o | bool |
| `notes` | o | |

**`protocol` enum** — `OIDC｜OAuth2_AuthCode｜SAML2｜CAS｜Kerberos｜Basic｜ApiKey`

> **Rule R-AUTH-1** — every user-facing entry point has one `AUTH-nn` row.
> "No auth because it is internal" is a finding, not a value.
>
> **Rule R-AUTH-2** — `service` / `machine` subjects are **not** valid here;
> they belong to `flows[].auth_method`.

### 4.9 Cross-cutting

| Collection | Purpose | Keyed by |
|---|---|---|
| `stacks` | component ↔ technology stack (EOL / licence) | `CMP-nn` |
| `ecosystem_relations` | app↔app upstream/downstream/partner (`06-connections-ecosystem-prd`) | `APP-nn` |
| `credentials` | secret/key storage per environment | `environment` |
| `constraints` | non-negotiable technical/compliance constraints | free |
| `open_items` | TBDs with owner + blocking flag | free |

**Encryption is modelled as attributes, not a collection** (decision):

- **At rest** → `components[].encryption_at_rest` (+ `key_management` → `INF-nn`):
  it is a property of the component that stores the data. When the key store is a
  topology object, point `key_management` at the `key_management` infra L4 node
  instead of using a free-text field.
- **In transit** → `flows[].encryption` inline enum.
- **Cross-border** → `flows[].cross_border` + `cross_border_basis` (the flow is
  what crosses a border); data residency stays on `project` /
  `systems[].data_classification`.

---

## 5. ID scheme

Typed prefixes make a reference self-describing and let the validator check kind
consistency without a lookup. Zero-padded 2 digits, matching the eam `CMP`/`CMPV`
convention.

| Prefix | Entity | Prefix | Entity |
|---|---|---|---|
| `INF-nn` | infra node | `DEP-nn` | deployment |
| `APP-nn` | system / application | `FLOW-nn` | component flow |
| `CMP-nn` | component / service | `LNK-nn` | infra network link |
| `SUB-nn` | subsystem | `AUTH-nn` | user / entry auth |
| `STK-nn` | stack binding | | |

Range citation is supported per kind: `INF-06–INF-13`, `FLOW-02..FLOW-04`.

---

## 6. Relation and integrity rules

```
systems   1 ── * components
components 1 ── * stacks            (optional)
components 1 ── * deployments
deployments * ── 1 infra            (infra_id; required in prod)
infra      * ── 1 infra             (parent_id — containment tree)
flows      * ── 1 components (source)   ┐ endpoints must be components
flows      * ── 1 components (target)   ┘ (`internet` source sentinel allowed)
flows      * ── * infra (via)       (ordered L4 path, optional)
components * ── 0..1 infra (key_management)   (at-rest key store)
network_links * ── 1 infra (source) ┐ endpoints must be infra
network_links * ── 1 infra (target) ┘
```

Global rules:

1. Prefix must match entity kind; every FK resolves.
2. `infra.parent_id` must form a valid hierarchy per the type policy matrix.
3. An infrastructure/security `node_kind` must never appear as a component.
4. Flow endpoints are components; network-link endpoints are infra.
5. `deployments.infra_id` required for `environment=prod`.
6. Every flow has an inline `auth_method`; every user-facing entry point has an `AUTH-nn` row.

---

## 7. Registry v2 — multi-table format

`input/systems-registry.md` remains **the only file that contains literal entity
names**. Instead of one mixed table it becomes one table per entity kind, each
with columns that fit that kind. It carries the same conventions as today
(codes-only elsewhere, `OUT-OF-SCOPE` marker, IP addresses removed).

### 7.1 Table schemas

| § | Table | Columns |
|---|---|---|
| R1 | Infra nodes | 编号 \| 参考图原名 \| node_kind \| infra_type \| network_type \| 父节点 \| 位置/国家 \| 文档用名 \| 备注 |
| R2 | Systems | 编号 \| 参考图原名 \| type \| owner \| vendor \| 文档用名 \| 备注 |
| R3 | Components / services | 编号 \| 参考图原名 \| 所属系统 \| 子系统 \| kind \| layer \| component_role \| 静态加密 \| 文档用名 \| 备注 |
| R4 | Deployments | 编号 \| 参考图原名 \| 组件 \| 环境 \| deployment_type \| location_type \| infra 节点 \| runtime_type \| 实例数 \| 文档用名 \| 备注 |
| R5 | Component flows | 编号 \| 参考图原名 \| 发起组件 \| 提供组件 \| protocol \| port \| auth_method \| 加密 \| 跨境 \| via \| 备注 |
| R6 | Infra network links | 编号 \| 参考图原名 \| 源 infra \| 目标 infra \| method \| 带宽 \| 加密 \| 管理方 \| 备注 |
| R7 | Auth (user / entry) | 编号 \| 参考图原名 \| subject \| 适用入口 \| auth_server \| protocol \| authorization \| MFA \| 备注 |

For derived rows (flows, links, auth) that have no reference-image name, the
「参考图原名」cell may be blank.

### 7.2 Worked example — de-mixing example 01

The rows below are the example-01 entities reclassified. Note how the v1
`applications[]` entries fan out into four different kinds, and how the
ExpressRoute circuit becomes a link rather than a node.

**R1 — Infra nodes**

| 编号 | 参考图原名 | node_kind | infra_type | network_type | 父节点 | 位置/国家 | 文档用名 | 备注 |
|---|---|---|---|---|---|---|---|---|
| INF-01 | Azure East US | region | public_cloud | — | — | US | azure-eastus | L1 |
| INF-02 | vNet-eCom-CoreService-EUS | iaas_vpc_vnet | public_cloud | prod_network | INF-01 | US | vnet-ecom-coreservice-eus | hub VNet |
| INF-03 | EastUS-VNET-A-BU | iaas_vpc_vnet | public_cloud | prod_network | INF-01 | US | vnet-ecom-bu-eus | BU spoke |
| INF-04 | AzureFirewallSubnet firewall | firewall | public_cloud | dmz | INF-02 | US | Azure Firewall (EastUS) | L4, forced egress |
| INF-05 | GatewaySubnet gateway | vpn_gateway | public_cloud | dmz | INF-02 | US | ExpressRoute gateway (EastUS) | L4 |
| INF-06 | APPGW subnet App Gateway | security_gateway | public_cloud | dmz | INF-03 | US | Application Gateway | L4, WAF ingress |
| INF-07 | dc-us | data_center | private_cloud | prod_network | — | US | US HQ DC | L2 |
| INF-08 | Japan DC, Osaka | data_center | private_cloud | prod_network | — | JP | Japan DC | L2 |

**R2 — Systems**

| 编号 | 参考图原名 | type | owner | vendor | 文档用名 | 备注 |
|---|---|---|---|---|---|---|
| APP-01 | eCom BU Platform | new | org_it | — | ecom-bu-platform | BU-facing application |
| APP-02 | eCom Shared Services | existing | org_it | — | ecom-shared-services | E2E black box |

**R3 — Components / services**

| 编号 | 参考图原名 | 所属系统 | 子系统 | kind | layer | component_role | 静态加密 | 文档用名 | 备注 |
|---|---|---|---|---|---|---|---|---|---|
| CMP-01 | BU order API | APP-01 | order | service | be | backend_service | — | order-api | |
| CMP-02 | BU web frontend | APP-01 | web | component | fe | web_frontend | — | order-web | |
| CMP-03 | BU primary DB | APP-01 | order | component | db | database | AES-256 | order-db | engine TBD; key_management → INF-12 |
| CMP-04 | Shared notification svc | APP-02 | — | service | be | integration_service | — | notify-svc | boundary only |

**R4 — Deployments**

| 编号 | 参考图原名 | 组件 | 环境 | deployment_type | location_type | infra 节点 | runtime_type | 实例数 | 文档用名 | 备注 |
|---|---|---|---|---|---|---|---|---|---|---|
| DEP-01 | AKS subnet cluster | CMP-01 | prod | public_cloud | public_cloud_region | INF-03 | container | 3 | order-api-eus | AKS |
| DEP-02 | APP subnet VMs | CMP-02 | prod | public_cloud | public_cloud_region | INF-03 | vm | 2 | order-web-eus | |
| DEP-03 | DB subnet | CMP-03 | prod | public_cloud | public_cloud_region | INF-03 | vm | 1 | order-db-eus | host TBD |

**R5 — Component flows**

| 编号 | 参考图原名 | 发起组件 | 提供组件 | protocol | port | auth_method | 加密 | 跨境 | via | 备注 |
|---|---|---|---|---|---|---|---|---|---|---|
| FLOW-01 | Internet → App Gateway | internet | CMP-02 | HTTPS | 443 | OIDC | TLS1.3 | 否 | INF-06 | public ingress; user auth = AUTH-01 |
| FLOW-02 | App Gateway → BU app | CMP-02 | CMP-01 | HTTPS | 443 | OAuth2_ClientCredentials | TLS1.3 | 否 | — | |
| FLOW-03 | BU app → DB | CMP-01 | CMP-03 | TBD | TBD | UserPassword | TLS1.3 | 否 | — | engine TBD |
| FLOW-04 | BU app → notify | CMP-01 | CMP-04 | TBD | TBD | mTLS | TLS1.3 | 否 | — | cross-app |

**R6 — Infra network links**

| 编号 | 参考图原名 | 源 infra | 目标 infra | method | 带宽 | 加密 | 管理方 | 备注 |
|---|---|---|---|---|---|---|---|---|
| LNK-01 | Azure-US-ER primary | INF-02 | INF-07 | expressroute | 1 Gbps | 是 | Carrier A | primary |
| LNK-02 | Azure-US-ER secondary | INF-02 | INF-07 | expressroute | 1 Gbps | 是 | Carrier B | secondary |
| LNK-03 | MPLS | INF-02 | INF-07 | mpls | TBD | TBD | InfraSec | backup |
| LNK-04 | Internet VPN | INF-02 | INF-07 | vpn | TBD | 是 | InfraSec | backup |
| LNK-05 | Azure JP ER | INF-09 | INF-08 | expressroute | TBD | 是 | Carrier C | primary |

**R7 — Auth (user / entry authentication only)**

| 编号 | 参考图原名 | subject | 适用入口 | auth_server | protocol | authorization | MFA | 备注 |
|---|---|---|---|---|---|---|---|---|
| AUTH-01 | External customer login | user | INF-06 | INF-10 | OIDC | TBD | 否 | identity provider node TBD |
| AUTH-02 | Internal admin login | user | CMP-01 | INF-11 | SAML2 | RBAC | 是 | ADFS |

Service-to-service auth (FLOW-02/03/04) is **inline enum** on the flow rows — it
does not appear here.

`INF-10` (identity provider) and a `region` wrapper for Japan are omitted here
for brevity.

---

## 8. Contract shape (`req/v2`)

`schemas/req-v2.schema.json` (draft, in this change) defines:

```yaml
schema_version: req/v2
requirements:
  project:      { name, id, scope, department, author, date, data_classification }
  infra:        [ ... ]     # INF-nn
  systems:      [ ... ]     # APP-nn
  components:   [ ... ]     # CMP-nn
  stacks:       [ ... ]     # STK-nn   (optional)
  deployments:  [ ... ]     # DEP-nn
  flows:        [ ... ]     # FLOW-nn   (inline auth_method + encryption + cross-border)
  network_links:[ ... ]     # LNK-nn
  auth:         [ ... ]     # AUTH-nn   (user / entry only)
  ecosystem_relations: [ ... ]   # APP-nn ↔ APP-nn
  credentials:  [ ... ]
  constraints:  [ ... ]
  open_items:   [ ... ]
```

Required top-level collections: `project`, `infra`, `systems`, `components`,
`flows`. `network_links`, `auth`, `deployments`, `stacks` are required as
*collections* (possibly empty) so consumers never branch on absence.

---

## 9. Migration from `req/v1`

`req/v1` stays frozen and readable. v1 → v2 reclassification of each
`applications[]` row:

| v1 row nature | v2 destination |
|---|---|
| VNet / VPC / subnet / zone | `infra` (`iaas_vpc_vnet` / `subnet` / `network_zone`) |
| Region / data centre | `infra` (`region` / `data_center`) |
| Firewall / WAF / gateway / bastion / LB appliance / identity / SOC / KMS | `infra` L4 (matching `node_kind`) |
| Business application | `systems` |
| Runtime platform (AKS cluster, VM group) | `components` (platform component) + `deployments` |
| Database / storage service | `components` (`database` / `object_storage`) + `deployments` |
| Carrier circuit (ExpressRoute/MPLS/VPN) | `network_links` (edge), **not** a node |
| Third-party / SaaS / partner system | `systems` (`owner=third_party`) |
| External DC's internal systems | `systems` (`type=existing`, E2E black box) |

Other moves:

| v1 | v2 |
|---|---|
| `deployment[]` (app-keyed) | `deployments[]` (component-keyed) + `infra_id` |
| `components[]` (`app_id`) | `components[]` (`system_id`) |
| `interactions[]` | `flows[]` (endpoints are components; inline `auth_method` + `encryption`) |
| `interactions[].auth_method` | `flows[].auth_method` (inline enum) |
| `network_connections[]` | `network_links[]` (infra→infra, undirected) |
| `user_auth[]` | `auth[]` (`subject=user`) |
| `data_encryption[].at_rest` / `at_rest_method` | `components[].encryption_at_rest` (+ optional `key_management`) |
| `data_encryption[].in_transit` / `in_transit_protocol` | `flows[].encryption` |
| `data_encryption[].cross_border` / `cross_border_compliance` | `flows[].cross_border` + `cross_border_basis` |
| `credentials`, `open_items` | unchanged in spirit |

Because the reclassification of a flat list is exactly the judgement that was
missing, a migration is best done **once per example, by hand, during the
example rebuild** — not by an automatic script.

---

## 10. Validation (for the future `registry_check` / req validator)

1. **Kind/prefix** — every id's prefix matches its collection.
2. **Referential integrity** — every FK resolves to an existing id of the right kind.
3. **Hierarchy** — `infra.parent_id` respects the type policy matrix.
4. **No infra-as-component** — an infrastructure/security `node_kind` never appears in `components`.
5. **Flow endpoints are components**; **network-link endpoints are infra**.
6. **Prod deployment has `infra_id`**.
7. **Every flow has an inline `auth_method`**; every user-facing entry point has an `AUTH-nn` row.
8. **Registry scope guard** (per table) — every in-scope row is cited by `input/prompt.md`.
9. **Literal leakage** — literal names appear only in the registry.
10. **No IP/CIDR** in textual documents.

---

## 11. Decisions (resolved)

| # | Question | Decision |
|---|---|---|
| 1 | `stacks` in scope? | **Yes** — included in v2. |
| 2 | Authentication on flows: entity or inline? | **Inline enum** on `flows[].auth_method`. |
| 3 | `ecosystem_relations`? | **Included** now. |
| 4 | At-rest encryption | **Component attribute** `components[].encryption_at_rest` (+ `key_management` → `INF-nn`); no collection. |
| 5 | In-transit encryption | **Inline enum** on `flows[].encryption`. |
| 6 | `via` path | **Persist** the ordered L4 path on flows. |
| 7 | Prefix set | **Confirmed** — `INF/APP/CMP/SUB/STK/DEP/FLOW/LNK/AUTH`. |
| 8 | `AUTH-nn` after inline auth | **Retained, narrowed** to user / entry authentication; service-to-service auth is inline. |

Sub-decision resolved here: cross-border is a **flow** attribute
(`cross_border` + `cross_border_basis`); data residency stays on `project` /
`systems[].data_classification`.

---

## 12. Follow-up implementation (after sign-off)

Not part of this design change. In order:

1. `standards/requirements-model-v2.yaml` — machine-readable model spec (packaged for skills).
2. `schemas/req-v2.schema.json` — promote draft to accepted; register `req/v2`.
3. `.claude/skills/arch-requirements/SKILL.md` (+ `.agents/`, `.github/`, plugin mirrors) — interview phases keyed to the new entities.
4. `tools/arch-req-readers/` — readers emit per-kind partials; merger validated per kind.
5. `archharness/registry.py` — multi-table parser + per-kind scope guard.
6. `archharness/req` normalizer/validator — the rules in §10.
7. Rebuild examples 01–08 on the v2 model; only then resume the examples commit question.
