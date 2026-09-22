# Architecture Validation Report

## Result

| Field | Value |
|---|---:|
| Project | Service Delivery Platform (SDP) |
| Platform detected | Mixed: private cloud with Azure satellites |
| Score | **4.32 / 10.00** |
| Must fix | **22** |
| Should fix | 2 |
| Gate preview | **BLOCK** |
| Enforcement run | No |

The generated PNG is not review-safe. Four dense regions contain severe edge and label overlap, especially across the CN primary Intranet and DB Zone, making authentication, mediation, database access, SAP calls, and cross-boundary routes difficult to associate with the correct arrows.

## Provenance

- Diagram: `output\diagrams\diagram.png`
- Diagram SHA-256: `8fb5a859aec55cfd2c1a67caad08eeb2e2210021ce621332a51b7e151bf6e46e`
- Ruleset digest: `c2b8876f3c6fce43e21aff118d2412bbdcab068df922a1d5faf087c3d4f6283a`
- Ruleset digest algorithm: SHA-256 over each ordered UTF-8 relative path, NUL, then raw file bytes
- Validator: `arch-validate/2.0; archharness/0.7.0`
- Validated: `2026-09-15T00:56:09Z`

The ruleset digest binds all six arch-validate YAML rule files, `standards/private-cloud-standard.yaml`, repository `config.yaml`, and the project overlay `config.yaml`.

## Exact Inventory

| Item | Count |
|---|---:|
| Technical components | 52 |
| Infrastructure boundaries | 8 |
| Network zones | 11 |
| Communication arrows | 80 |
| Cross-boundary arrows | 37 |
| Integration-platform nodes | 4 |
| Data-store nodes | 10 |
| Bidirectional arrows | 0 |
| Arrows missing protocol | 0 |
| Arrows missing auth text | 0 |
| Arrows missing explicit port | 80 |
| Dashed physical components | 37 |
| Dashed physical zones | 9 |
| Visually congested regions | 4 |

## Six Dimensions

| Dimension | Raw | Weight | Weighted |
|---|---:|---:|---:|
| Cloud Network Completeness | 6.25 | 2.0 | 1.25 |
| Connectivity | 3.00 | 1.0 | 0.30 |
| Technical Component Completeness | 4.30 | 2.0 | 0.86 |
| Interaction Integration | 6.75 | 2.0 | 1.35 |
| Security Compliance | 1.00 | 2.0 | 0.20 |
| Terminology Expression | 3.60 | 1.0 | 0.36 |
| **Total** |  |  | **4.32** |

## Must Fix

1. Redraw the four congested regions so every label is readable and unambiguously attached to one arrow. Split the view into ingress/identity, application/data, SAP/integration, and external-partner views if necessary.
2. Change dashed borders on 37 physical components and 9 physical zones to solid borders. Reserve dashed borders for logical concepts.
3. Replace the Azure exact-region TBD and SAP/partner location TBD values with approved Region/country or jurisdiction labels.
4. Classify SYS-38 through SYS-41 correctly as SaaS endpoints or place Azure-owned workloads in explicit VNET/Subnet boundaries with private endpoint details.
5. Add infrastructure-level connectivity links. Identify MPLS/equivalent for DC-to-DC and SAP, and ExpressRoute/equivalent private connectivity for Azure. Twenty-six of 37 cross-boundary arrows currently lack connection type.
6. Add visible component categories to the 37 generic component boxes and visible runtime/platform placement to all 52 components.
7. Add explicit ports to all 80 arrows as required by `input/prompt.md`. Protocol and auth text are present on all 80, but ports are absent.
8. Reverse the SYS-41 consumer relation so it points to SYS-06 Kafka.
9. Mediate the ten SYS-07..SYS-11 to SAP SYS-20/SYS-24 calls through SYS-05 or another approved integration platform.
10. Remove the direct Internet-to-SYS-30 Intranet ingress. Show external identity and application callback paths through the approved F5/DMZ pattern.
11. Connect the user actor and application entry point to ADFS and Enterprise ID with complete request/callback semantics.
12. Add AuthZ Platform as a visible node and show policy enforcement connections, or visibly annotate application RBAC/ABAC enforcement.
13. Select and name the non-K8s enterprise vault, then show consumers and rotation. Kubernetes Secrets only covers workload DB credentials; TBD-009 remains blocking.
14. Label the eight known CN-US application/event flows with data classification, minimized fields, and approved transfer basis.
15. Add the mandatory Office Network -> MFA -> PAW -> management plane -> target-zone operational path.
16. Put SYS-24 and SYS-33 inside explicit DB/data segments or show equivalent enforceable isolation.
17. Complete the legend with arrow direction, line style, warning/status markers, and all boundary semantics.
18. Resolve and approve mTLS for F5/nginx and partners, SAP SNC/auth endpoints, and the Enterprise ID callback instead of rendering unresolved assumptions as final controls.

## Focus Findings

### F5 And DMZ

The main web path follows `Internet -> SYS-52 -> SYS-01 F5 -> SYS-02`, and SYS-01 is correctly shown as a hexagon in the DMZ. However, `Internet -> SYS-30` bypasses F5 into the US DC Intranet, and the external identity callback/application path is missing. Partner inbound traffic is not explicitly traceable through F5.

### Mediation And Boundaries

WSO2, Kafka, and MFT platform are independent nodes in the CN primary Intranet. Most remote APIs and files use those mediators. The ten direct SDP-to-SAP flows bypass mediation, while SAP and both 3PL boundary locations remain TBD. The 3PL paths are outbound from WSO2; required inbound termination at F5 is not demonstrated.

### Authentication And Secrets

All 80 arrows contain auth text, but several controls are unresolved assumptions. The User actor is disconnected, the Enterprise ID callback is absent, AuthZ Platform is not drawn, and the non-K8s vault remains unspecified. K8s Secrets are identified for database passwords but no visible credential-management node or complete rotation architecture exists.

### PAW And Database Zoning

The blueprint declares PAW and DB segmentation, but the PNG omits the PAW path entirely. The eight CN-primary stores are visibly in DB Zone; SYS-24 and SYS-33 lack explicit DB/data sub-segmentation. Dense overlaps over the CN-primary DB Zone materially reduce confidence in individual access-path interpretation.

## Enforcement Readiness

`validate_result.json` is intended to be schema-validated and recorded as an absolute-path `artifact/v1` manifest. Once recorded and the validate stage is completed, the workflow should report `enforce` ready. Enforcement was explicitly not run.
