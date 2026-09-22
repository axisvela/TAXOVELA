# Requirements Document — E-commerce Platform (Azure Multi-Region)
**Version**: 1.0  |  **Project ID**: ECOM-AZ-001  |  **Classification**: Acme Confidential

> Resolve SYS-nn codes via `input/systems-registry.md`.

**Scope**: Network & hosting architecture (textual names scrubbed; reference image unchanged)

---

## 1. Project Overview

E-commerce platform serving US and AP markets, hosted entirely on Azure with
hybrid connectivity to two on-prem data centers. The US business unit runs in
EastUS; the AP e-commerce platform runs in JapanEast. Both regions
follow the corporate hub-spoke network standard with centralized firewall
egress and dedicated-circuit hybrid attach.

## 2. Network Locations

| Location | Type | Region | Purpose |
|----------|------|--------|---------|
| Azure EastUS | Cloud region | NA | Primary e-commerce workload |
| Azure JapanEast | Cloud region | APAC-JP | AP e-commerce platform |
| SYS-20 | On-prem | NA | Corporate systems, hybrid attach |
| SYS-21 | On-prem | APAC-JP | Local systems, hybrid attach |

## 3. Azure EastUS — VNets and Subnets

| VNet | Role | Subnets |
|------|------|---------|
| SYS-01 | Hub | SYS-06, SYS-07 |
| SYS-02 | Spoke (BU) | SYS-10, DMZ, SYS-11, SYS-12, SYS-13 |
| SYS-03 | Spoke (shared) | SYS-15, SYS-14, SYS-16 |

- Route tables on every SYS-02 / SYS-03 subnet — default route goes to the
  hub firewall instance SYS-06 (forced tunnel).
- VNet peering: SYS-01 to SYS-02, SYS-01 to SYS-03, SYS-02 to SYS-03.

## 4. Azure JapanEast — VNets and Subnets

| VNet | Role | Subnets |
|------|------|---------|
| SYS-04 | Hub | SYS-08, SYS-09 |
| SYS-05 | Spoke | SYS-17, DMZ, SYS-18, SYS-19 |

- Route tables on every SYS-05 subnet — default route goes to the hub
  firewall instance SYS-08.
- Workload-cluster subnet SYS-17 is routable from on-prem via dedicated circuit.

## 5. Hybrid Connectivity

| Path | Type | Notes |
|------|------|-------|
| SYS-01 to SYS-20 | SYS-22 | Primary dedicated circuit |
| SYS-01 to SYS-20 | SYS-23 | Secondary carrier dedicated circuit |
| SYS-01 to SYS-20 | SYS-24 + SYS-25 | Backup paths |
| SYS-04 to SYS-21 | SYS-26 | Primary dedicated circuit |
| Reference RTT SYS-01 to SYS-20 | — | Baseline measurement ~4 ms |

## 6. Security & Traffic Rules

- All spoke egress and spoke-to-spoke traffic hairpins through the hub
  firewall instances SYS-06 and SYS-08; no bypass routes.
- Ingress subnet SYS-10 hosts the public ingress (WAF-enabled).
- The storage service (SYS-16) is reachable only via its private endpoint.
- Authentication: internal admins via the internal IdP; Azure control plane
  via the external IdP (RBAC).

## 7. Constraints

- Hub-spoke only; no direct spoke-to-spoke peering without firewall inspection.
- Dual-carrier dedicated circuits are mandatory for the US path (SYS-22 + SYS-23).
- Data classification Acme Confidential; encryption in transit everywhere.

## 8. Open Items

| ID | Item | Blocking |
|----|------|----------|
| TBD-01 | SYS-21 second dedicated circuit (currently single attach) | No |
| TBD-02 | Firewall rule-set review for workload egress FQDN tags (SYS-11, SYS-14, SYS-17) | No |
