# Architecture Validation Report

**Project:** DAP-001 Data Agent Platform (GDA)  
**Diagram:** `output\diagrams\diagram.png`  
**Platform:** Hybrid private cloud and Azure  
**Validated:** 2026-09-15T00:56:16Z  
**Status:** BLOCK candidate; enforcement was not run

## Result

| Dimension | Raw score / 10 | Weight | Weighted score |
|---|---:|---:|---:|
| Cloud Network Completeness | 4.4 | 2.0 | 0.88 |
| Connectivity | 0.0 | 1.0 | 0.00 |
| Technical Component Completeness | 5.3 | 2.0 | 1.06 |
| Interaction and Integration | 8.0 | 2.0 | 1.60 |
| Security Compliance | 0.0 | 2.0 | 0.00 |
| Terminology and Expression | 6.0 | 1.0 | 0.60 |
| **Total** |  | **10.0** | **4.14 / 10** |

Issue counts are exact against `validate_result.json`: **18 must_fix**, **2 should_fix**, **2 consider**.

## Assessment

The diagram is a technical architecture and clearly shows the intended private-DC runtime, controlled CMP-05 outbound hop, Azure data/model boundaries, and single-direction application flows. It is not implementation-ready because visible `TBD` values leave mandatory network and security controls undefined.

The empty DMZ does not contain the required F5/firewall/load-balancing ingress stack. Both Azure hybrid paths leave the connection type, routing, inspection, and private DNS unresolved. The Azure regions do not show complete Hub VNET services, and the EDW private endpoint posture is not explicit.

Identity and credential controls are also incomplete. Entra ID is primary for office users while ADFS is only a fallback, the exact sign-in/token-validation flow and authorization mapping are TBD, and no AuthZ Platform is shown. Azure Key Vault, Managed Identity, the CMP-05 secret store, CMP-06 credential lifecycle, CMP-07 API-key lifecycle, private-DC PAW, and Azure Bastion are absent or TBD.

The two CN-to-US flows carry Acme Confidential data but do not visibly state the approved legal basis, final minimization/redaction controls, logging limits, or retention. PostgreSQL at-rest encryption, certificate trust, backup protection, HA, RTO, and RPO are unresolved.

## Scoring Basis

- Cloud/network deductions cover unresolved global identity jurisdiction, TBD infrastructure owners, incomplete Azure VNET/subnet and Hub-Spoke detail, and incomplete private endpoint/DNS controls. No duplicate region was observed.
- Connectivity receives zero because neither DC-to-Azure path identifies an approved transport such as ExpressRoute/IPSec nor network-layer encryption; application TLS alone does not resolve the transport requirement.
- Technical completeness credits named components and the K8s hosting boundary, but deducts unresolved custom frameworks/versions and TBD PostgreSQL/connectivity-gateway runtimes.
- Interaction/integration credits single-direction arrows, protocol labels, same-application database access, and the explicit CMP-05 intermediary. It deducts unresolved authentication and private-connectivity semantics.
- Security receives zero because all three security subcategories have mandatory failures: system/boundary authentication, user authentication/authorization, and credential/data protection.
- Terminology/expression credits the title, Azure/private-cloud terms, shapes, colors, and legend. It deducts generic Azure notation and materially overlapping relationship labels.

## Must Fix Before Enforcement Can Pass

1. Populate the DMZ with the approved F5/firewall/load-balancing ingress path and route user traffic through it.
2. Resolve both hybrid links to approved designs, including ExpressRoute or approved equivalent, gateway placement, routing, firewall inspection, private DNS, and link encryption.
3. Complete each Azure regional Hub VNET with required gateway, firewall, DNS, Bastion, and monitoring controls; show spoke peering and private endpoints explicitly.
4. Finalize ADFS/Entra user populations and protocols, token validation, fallback behavior, tenant role mapping, and an implemented AuthZ Platform or explicit RBAC/ABAC control.
5. Add Key Vault and Managed Identity where applicable; finalize approved storage, delivery, access, and rotation for CMP-05, CMP-06, CMP-07, database, and certificate secrets.
6. Show the office-to-PAW private-DC administration path and Azure Bastion/JIT administration paths.
7. Label cross-border payload classification and obtain the legal/compliance basis for minimization, redaction, logging, and retention.
8. Resolve owners, component stacks/runtimes, PostgreSQL encryption and certificate trust, backup protection, HA, RTO, and RPO.

## Provenance

- Diagram SHA-256: `e19b7f9035554e8b4112030036c103eda5b8ad2bc5d9fdcd957aa31e96e104cd`
- Ruleset SHA-256: `26ffb5197517453a4f91bb994cdea3fdce8ef3256390f131b4fb62d7b069db21`
- Ruleset digest algorithm: SHA-256 over each sorted path relative to `.agents/skills/arch-validate/rules`, followed by NUL, exact file bytes, and NUL.
- Rule files: `accuracy-rules.yaml`, `compliance/terminology.yaml`, `diagram-rules.yaml`, `interaction-rules.yaml`, `platform-rules.yaml`, `security-rules.yaml`.
- Supporting context read: root and example `config.yaml`, `blueprint.yaml`, `private-cloud-standard.yaml`, `azure-standard.yaml`, `diagram-style.yaml`, `eval-weights.yaml`, and `tools/arch-diagram-gen/templates/data-analytics.yaml`.
