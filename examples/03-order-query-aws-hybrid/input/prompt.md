# One-shot prompt — Order Query Platform (OQP ROW)

Use this prompt with `input/systems-registry.md`. The registry is the only file
that carries literal entity names; this prompt uses typed IDs only.

Design the AWS US order-query platform represented by APP-01. Deploy CMP-01 in
the INF-02 DMZ subnet and CMP-02 through CMP-19 in INF-03 using the internal
Kubernetes runtime. Deploy CMP-21 through CMP-24 in INF-04 and use INF-08 for
their key management.

Public ingress must traverse INF-05 then INF-06. INF-07 separates application
and data traffic. Internal users authenticate through INF-12 and partners through
INF-13; their entry authentication is AUTH-01 and AUTH-02.

All source integration is mediated through CMP-25 through CMP-32. LNK-01 through
LNK-04 connect the private DCs to INF-01. PRC data remains in China: FLOW-10
carries approved request messages only and FLOW-11 is the in-country query.

Produce req/v2 requirements, a typed architecture blueprint, and versioned
draw.io/D2/PNG diagrams. Every rendered interaction must have protocol and auth.

Systems and infra in scope: APP-01 through APP-07; INF-01 through INF-28;
CMP-01 through CMP-55.
