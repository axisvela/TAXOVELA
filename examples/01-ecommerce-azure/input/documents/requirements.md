# Requirements Document - E-commerce Platform (Azure Multi-Region)
**Version**: 2.0 | **Project ID**: ECOM-AZ-001 | **Classification**: Acme Confidential

> Resolve typed codes via `input/systems-registry.md`.

## Scope

This req/v2 migration covers APP-01 through APP-04, INF-01 through INF-21, and CMP-01 through CMP-11. The workload uses two regional hub-spoke deployments with existing corporate boundaries at INF-20 and INF-21.

## Topology

INF-01/INF-02/INF-03 form the East US hub and spokes. INF-04/INF-05 form the Japan hub and spoke. INF-06 and INF-08 are mandatory inspection points; route tables force spoke egress and spoke-to-spoke traffic through them. INF-10 is public WAF ingress. INF-07 and INF-09 are hybrid gateways.

## Workloads

CMP-01 through CMP-06 run in East US; CMP-07 through CMP-09 run in Japan. DEP-01, DEP-04, and DEP-07 use Kubernetes solely as a runtime type. CMP-10 and CMP-11 are black-box integration boundaries for APP-03 and APP-04.

## Connectivity And Security

LNK-04 and LNK-05 provide dual-carrier dedicated connectivity to INF-20; LNK-06 and LNK-07 are backup paths. LNK-08 connects INF-04 and INF-21. FLOW-01 through FLOW-11 declare application communication and mandatory appliance hops. AUTH-01 controls customer entry. CMP-06 is private-endpoint only; all flows use TLS.

## Open Items

| ID | Item | Blocking |
|----|------|----------|
| TBD-01 | Confirm second dedicated path for INF-21. | No |
| TBD-02 | Confirm database engines, ports, and workload egress rules for CMP-01, CMP-04, and CMP-07. | No |
