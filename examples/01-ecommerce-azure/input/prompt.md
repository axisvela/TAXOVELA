# One-shot prompt - E-commerce Platform (Azure)

> Resolve typed codes through `input/systems-registry.md`; literal entity names occur only there.

Design the Azure hub-spoke and hybrid architecture for this confidential platform.

1. INF-01 through INF-05 are the two regional hub-spoke VNet topologies.
2. INF-06 and INF-08 are mandatory inspection appliances. INF-10 is the public WAF ingress. INF-07 and INF-09 terminate hybrid connectivity.
3. East US hosts CMP-01 through CMP-06; Japan hosts CMP-07 through CMP-09. Kubernetes is deployment runtime detail, not an inventory node.
4. APP-03/CMP-10 and APP-04/CMP-11 are existing black-box corporate integration boundaries.
5. LNK-04 and LNK-05 are mandatory dual-carrier US dedicated paths. LNK-06/LNK-07 are backups; LNK-08 is the Japan dedicated path.
6. All spoke egress and cross-spoke routes are inspected through the relevant firewall. Storage access is private-endpoint only. Use TLS everywhere.

Systems and infra in scope: APP-01 through APP-04; INF-01 through INF-21; CMP-01 through CMP-11.
