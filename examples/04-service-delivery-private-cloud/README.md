# Example 4 — Service Delivery Platform (SDP): Private Cloud Multi-DC

Reverse-engineered from a real service-delivery architecture diagram
(restricted and intentionally not scrubbed). The most complete demonstration
of the **private-cloud standard**: three-tier zoning, INF-04 ingress,
CMP-04/CMP-05-only integration, SAP RFC, CMP-11 MFT, 3PL EDI/SFTP, and a
7-group HA DB tier.

> **Name policy:** `input/systems-registry.md` is the only file that contains
> literal entity names. Every other file — `input/prompt.md`,
> `input/documents/requirements.md`, `README.md`, `config.yaml` — references
> `SYS-nn` codes only. The original reference diagram is intentionally not
> scrubbed and is restricted input.

## Scenario

**SDP** is the service supply-chain operations platform (~40 Java/SpringCloud
microservices) being migrated to serve NA. It runs in the CN
primary DC and integrates with satellite systems in three other DCs, Azure,
SAP, and external 3PL partners.

- **CN primary DC (`dc-cn-primary`, three-tier)**
  - Ingress: INF-04 (TLS termination, OAuth2) → DMZ, INF-03
  - DMZ K8s cluster: CMP-01, CMP-02, CMP-03 (external entry points)
  - Intranet: CMP-04, CMP-05, CMP-06, CMP-07, CMP-08, and two
    microservice groups: CMP-09 (10 services) and CMP-10 (22 services,
    members listed in `input/documents/requirements.md` §2)
  - DB Zone: CMP-12, CMP-13, CMP-14, CMP-15, CMP-16 (1 master + 2 slaves
    each), CMP-17 (3 master + 3 slave), CMP-18 (3 replicas),
    CMP-19 (3 nodes)
- **SAP**: CMP-31 ↔ CMP-32 / CMP-33 / CMP-34 via TCP/RFC; CMP-35 object storage
- **Other DCs**: US DC (CMP-20, CMP-21, CMP-22, CMP-23, INF-09,
  INF-10) via CMP-04/VPN-MPLS; CN secondary DC (CMP-24, CMP-25, CMP-26,
  CMP-27, CMP-28); Support DC (CMP-29, CMP-30)
- **Azure**: CMP-36 / CMP-37 / CMP-38 (HTTPS/OAuth2), CMP-39
  (TCP SASL/SCRAM)
- **External 3PL**: CMP-40, CMP-41, CMP-42, CMP-43, CMP-44, CMP-45
  (HTTPS/OAuth2 or TCP/EDI); partner file hub systems CMP-46, CMP-47, CMP-48 (SFTP)

## What it demonstrates

| Pipeline stage | Highlight |
|---|---|
| private-cloud-standard | Full three-tier coverage incl. DB Zone HA topology |
| interaction-rules | CMP-04/CMP-05/CMP-11 as the only legal mediators; EDI/SFTP external patterns |
| security-rules | OAuth2 vs BasicAuth per hop, SAP RFC trust boundary, INF-04 TLS termination |
| accuracy-rules | Four DCs with distinct zone models |

## Inputs

- ★ `input/systems-registry.md` — code → name registry; the only file with literal names
- `input/prompt.md` — SYS-numbered one-shot prompt (Path A)
- `input/documents/requirements.md` — structured requirements (Path B)
- `input/diagrams/reference-architecture.png` — original, intentionally not scrubbed, restricted input

## Name policy

| Area | Policy |
|---|---|
| Registry | `input/systems-registry.md` — the only file containing literal names |
| Documents | `prompt.md`, `requirements.md`, `README.md`, `config.yaml` reference typed codes only (`INF-` / `APP-` / `CMP-` and the `DEP`/`FLOW`/`LNK`/`AUTH` derived layers) |
| Reference diagram | original image, intentionally not scrubbed; restricted input only |
| DC names | mapped to config ids (`dc-cn-primary`, `dc-us`, `dc-cn-secondary`, `dc-cn-support`) |
| IP addresses | none present / removed |
| 3PL carriers | CMP-40..CMP-45 carry role names rather than carrier brands; the brands survive only in the registry's 参考图原名 column |
| File-transfer partners | CMP-46..CMP-48 carry role names; CMP-11 is the generic managed-file-transfer node |
| SaaS applications | CMP-36..CMP-38 keep their SaaS application names; only carrier and vendor brands are scrubbed |
| Generated artwork | `output/diagrams/diagram.*` is regenerated from the scrubbed blueprint; the recorded validation re-binds to that render |

## Diagram artwork

| Artifact | What it is |
|---|---|
| `output/diagrams/diagram.drawio` / `.png` | Artwork the recorded validation and enforcement decision were produced from, on the earlier `SYS-nn` id space. |
| `output/diagrams/diagram-v2.drawio` / `.d2` | Editable source and image source, rendered from the migrated blueprint where appliances are `INF-` L4 nodes and every service carries its `CMP-` code. |
| `output/diagrams/diagram-v2.png` | **D2 render** of `diagram-v2.d2` — the image. Its automatic layout differs from the retired draw.io artwork, so it is not the validation target. |

The blueprint and requirements were migrated to the req/v2 model after the
recorded validation: the router, F5, ADFS, and the external IdP are now infra
nodes rather than components, appliance hops are carried in each flow's `via`
list, and the requirements document is `req/v2` with 208 registry rows.
Promoting v2 means re-running validate → enforce against it and re-recording
`diagram.png`.
