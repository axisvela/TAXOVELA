# Requirements Document - E-commerce Platform (Azure)
**Version**: 2.0 | **Project ID**: ECOM-AZ-001 | **Classification**: Acme Confidential
**Model**: `req/v2` entity-separated requirements

> Resolve typed codes via `input/systems-registry.md`.

## Scope

APP-01 through APP-04 are in scope. INF-01 through INF-21 describe the Azure and corporate topology; CMP-01 through CMP-11 describe workload and black-box boundary artifacts.

## Topology And Policy

INF-01/INF-02/INF-03 provide the East US hub-spoke topology and INF-04/INF-05 provide the Japan topology. INF-06 and INF-08 are zone-boundary firewalls. INF-10 is WAF ingress. INF-07 and INF-09 terminate hybrid paths. LNK-01 through LNK-03 are VNet peering; LNK-04 through LNK-08 are carrier paths.

Network appliances remain INF nodes. Dedicated circuits, MPLS, VPN, and peering remain LNK rows. Kubernetes is runtime detail in DEP-01, DEP-04, and DEP-07, not a topology or application inventory record.

## Workloads And Communication

CMP-01 through CMP-06 serve the US workload. CMP-07 through CMP-09 serve the AP workload. CMP-10 and CMP-11 provide the required integration boundaries for the existing APP-03 and APP-04 systems. FLOW-01 through FLOW-11 define encrypted component communication; the `via` path captures mandatory firewall and gateway traversals.

## Authentication And Credentials

AUTH-01 applies OIDC and RBAC to the CMP-01 entry path. Azure managed identity is required for service access. Azure Key Vault protects application credentials; hardcoded credentials are prohibited.

## Constraints

- East US cross-spoke and hybrid routes traverse INF-06.
- Japan hybrid routes traverse INF-08.
- CMP-06 permits private-endpoint access only.
- TLS 1.3 protects application flows; hybrid links use IPsec overlays.

## Open Items

| ID | Item | Blocking |
|----|------|----------|
| TBD-01 | Confirm a secondary dedicated path for INF-21. | No |
| TBD-02 | Confirm database engines and ports for CMP-03 and CMP-09. | No |
