# Example 4 — Service Delivery Platform (SSOC): Private Cloud Multi-DC

Reverse-engineered from a real service-delivery architecture diagram
(restricted and intentionally not scrubbed). The most complete demonstration
of the **private-cloud standard**: three-tier zoning, SYS-01 ingress,
SYS-05/SYS-06-only integration, SAP RFC, SYS-51 MFT, 3PL EDI/SFTP, and a
7-group HA DB tier.

> **Name policy:** `input/systems-registry.md` is the only file that contains
> literal entity names. Every other file — `input/prompt.md`,
> `input/documents/requirements.md`, `README.md`, `config.yaml` — references
> `SYS-nn` codes only. The original reference diagram is intentionally not
> scrubbed and is restricted input.

## Scenario

**SSOC** is the service supply-chain operations platform (~40 Java/SpringCloud
microservices) being migrated to serve NA. It runs in the CN
primary DC and integrates with satellite systems in three other DCs, Azure,
SAP, and external 3PL partners.

- **CN primary DC (`dc-cn-primary`, three-tier)**
  - Ingress: SYS-01 (TLS termination, OAuth2) → DMZ, SYS-52
  - DMZ K8s cluster: SYS-02, SYS-03, SYS-04 (external entry points)
  - Intranet: SYS-05, SYS-06, SYS-07, SYS-08, SYS-09, and two
    microservice groups: SYS-10 (10 services) and SYS-11 (22 services,
    members listed in `input/documents/requirements.md` §2)
  - DB Zone: SYS-12, SYS-13, SYS-14, SYS-15, SYS-16 (1 master + 2 slaves
    each), SYS-17 (3 master + 3 slave), SYS-18 (3 replicas),
    SYS-19 (3 nodes)
- **SAP**: SYS-20 ↔ SYS-21 / SYS-22 / SYS-23 via TCP/RFC; SYS-24 object storage
- **Other DCs**: US DC (SYS-25, SYS-26, SYS-27, SYS-28, SYS-29,
  SYS-30) via SYS-05/VPN-MPLS; CN secondary DC (SYS-31, SYS-32, SYS-33,
  SYS-34, SYS-35); Support DC (SYS-36, SYS-37)
- **Azure**: SYS-38 / SYS-39 / SYS-40 (HTTPS/OAuth2), SYS-41
  (TCP SASL/SCRAM)
- **External 3PL**: SYS-42, SYS-43, SYS-44, SYS-45, SYS-46, SYS-47
  (HTTPS/OAuth2 or TCP/EDI); partner file hub systems SYS-48, SYS-49, SYS-50 (SFTP)

## What it demonstrates

| Pipeline stage | Highlight |
|---|---|
| private-cloud-standard | Full three-tier coverage incl. DB Zone HA topology |
| interaction-rules | SYS-05/SYS-06/SYS-51 as the only legal mediators; EDI/SFTP external patterns |
| security-rules | OAuth2 vs BasicAuth per hop, SAP RFC trust boundary, SYS-01 TLS termination |
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
| Documents | `prompt.md`, `requirements.md`, `README.md`, `config.yaml` reference `SYS-nn` codes only |
| Reference diagram | original image, intentionally not scrubbed; restricted input only |
| DC names | mapped to config ids (`dc-cn-primary`, `dc-us`, `dc-cn-secondary`, `dc-cn-support`) |
| IP addresses | none present / removed |
| 3PL carriers | SYS-42 through SYS-47 use role names (`logistics partner A`..`E`); carrier brands are scrubbed everywhere except the registry's 参考图原名 column |
| File-transfer partners | SYS-48 through SYS-50 use role names (`file partner A`..`C`); SYS-51 is the generic `MFT platform` |
| Generated artwork | `output/diagrams/diagram.*` is regenerated from the scrubbed blueprint; the recorded validation re-binds to that render |
