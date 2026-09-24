# Requirements Document — Order Query Platform (OQP ROW)

**Version**: 2.0 | **Project ID**: OQP-ROW-001 | **Classification**: Acme Confidential

All inventory is referenced by typed ID; resolve names only in
`input/systems-registry.md`.

## Scope

APP-01 is an AWS US order-query application. CMP-01 is deployed in INF-02;
CMP-02 through CMP-19 run in INF-03; and CMP-21 through CMP-24 are in INF-04.
The Kubernetes platform is deployment runtime detail, not a component or infra
node. INF-05, INF-06, and INF-07 are the WAF/firewall appliance controls.

## Identity And Integration

AUTH-01 uses INF-12 for employees and AUTH-02 uses INF-13 for partners. CMP-25
through CMP-32 are mandatory API/Kafka mediation boundaries. APP-02 through
APP-07 are existing system boundaries represented by their CMP endpoints.

## Data And Connectivity

LNK-01 through LNK-04 are MPLS links to INF-01 with application TLS. PRC source
data remains in China: FLOW-10 contains approved requests only and FLOW-11
executes the query in-country. No direct source-to-APP-01 integration is allowed.

## Open Items

1. Confirm ports, topic-to-cluster assignment, source mapping, and database sizing.
2. Confirm managed-service selection, encryption settings, secret rotation, and RBAC.

Systems and infra in scope: APP-01 through APP-07; INF-01 through INF-28;
CMP-01 through CMP-55.
