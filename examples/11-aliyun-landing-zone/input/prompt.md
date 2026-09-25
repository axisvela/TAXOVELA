# One-shot prompt — Order Service Platform (ORD) on Alibaba Cloud

> Codes-only prompt. Every system/service is referenced by a typed code
> (`INF-` infra · `APP-` systems · `CMP-` components · the `DEP`/`FLOW`/`LNK`/
> `AUTH` derived layers), resolved through `input/systems-registry.md` (include
> that registry as context when supplying this prompt to an agent). No literal
> system names appear outside the registry.

Design the technical architecture for an order service that runs on Alibaba
Cloud and publishes order status to the on-premises ERP.

Systems and infra in scope: APP-01 through APP-02; INF-01 through INF-18;
CMP-01 through CMP-06.

Requirements:

1. **Accounts and VPCs**: a central account owns a hub VPC (INF-01) with an edge
   vSwitch (INF-02) and a shared services vSwitch (INF-03). Business workloads
   run in a separate VPC (INF-04) with two application vSwitches in different
   availability zones (INF-05, INF-06) and one data vSwitch (INF-07). Cross-VPC
   and cross-region traffic goes through CEN (INF-15), never the internet.
2. **Ingress**: Anti-DDoS (INF-10) then the web application firewall (INF-11)
   then the server load balancer (INF-12). No workload holds an Elastic IP.
3. **Egress and inspection**: all outbound traffic leaves through the NAT
   gateway (INF-14); east-west traffic is inspected by the cloud firewall
   (INF-13).
4. **Components**: CMP-01 and CMP-02 are the order service in two availability
   zones, CMP-03 the order database, CMP-04 the document archive bucket,
   CMP-05 the only boundary into the ERP zone, CMP-06 the ERP system of record.
5. **Integrations**: every flow names its protocol and authentication method;
   the inspection and hybrid hops it traverses appear in `via`. Order status
   travels over CEN and Express Connect with IPSec.
6. **Identity and secrets**: internal users sign in through the enterprise IdP
   (INF-18) federated to RAM SSO. Workloads assume RAM roles with STS tokens;
   database passwords live in the KMS secret manager (INF-17). Long-lived
   AccessKeys are prohibited.
7. **Data**: the order database and archive bucket use KMS customer master
   keys. Acme Restricted data stays in the ERP and never enters the cloud
   database.
8. **Open items**: record what is still TBD with an owner.
