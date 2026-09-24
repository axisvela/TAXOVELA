# Requirements Document - Order Query Platform (OQP ROW)

**Version**: 2.0 | **Date**: 2026-09-24 | **Classification**: Acme Confidential

## Scope

APP-01 provides the AWS-hosted order-query workload. APP-02 through APP-07 are
existing black-box source and entry systems, represented by their CMP boundary
components. The authoritative entity inventory is `req.yaml` and
`input/systems-registry.md`.

## Topology

INF-01 is the AWS US VPC. INF-02, INF-03, and INF-04 provide the DMZ,
application, and data subnets. INF-05 is the WAF ingress appliance; INF-06 and
INF-07 are firewalls; INF-08 is the AWS key-management appliance. The internal
Kubernetes platform is deployment runtime detail for DEP-01 through DEP-19, not
an infra or component node.

INF-09, INF-14, INF-19, and INF-23 are the US, NA, PRC-primary, and
PRC-secondary DCs. INF-27 and INF-28 are the existing Azure source boundaries.
LNK-01 through LNK-04 are encrypted MPLS connectivity to INF-01.

## Identity And Data Controls

AUTH-01 uses INF-12 for internal employees and AUTH-02 uses INF-13 for partner
users. CMP-25 through CMP-32 are mandatory API and Kafka mediation boundaries.
PRC row data remains in-country: FLOW-10 carries approved requests only, and
FLOW-11 queries CMP-53 within INF-28.

## Open Items

- Confirm source mappings, ports, topic assignments, and database sizing.
- Confirm data-service selection, encryption settings, secret rotation, and RBAC.
