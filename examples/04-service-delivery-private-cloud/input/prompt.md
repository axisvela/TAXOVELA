# One-shot prompt — Service Delivery Platform (SDP)

> Codes-only prompt. Every system/service is referenced by a typed code
> (`INF-` infra · `APP-` systems · `CMP-` components · the `DEP`/`FLOW`/`LNK`/
> `AUTH` derived layers), resolved through `input/systems-registry.md` (include
> that registry as context when supplying this prompt to an agent). No literal
> system names appear outside the registry.

Design the technical architecture for **SDP**, our service supply-chain
operations platform, as it migrates to serve NA. Private cloud only, four
DCs, ~40 Java/SpringCloud microservices.

Systems and infra in scope: APP-01 through APP-05; INF-01 through INF-23;
CMP-01 through CMP-48.

Requirements:

1. **CN primary DC, three-tier**:
   - Ingress via INF-04 (TLS termination, OAuth2) into the DMZ, behind the
     network edge router INF-03.
   - DMZ K8s cluster: CMP-01, CMP-02, CMP-03.
   - Intranet K8s cluster: CMP-06, CMP-07, CMP-08, plus two service
     groups — CMP-09 (10 services) and CMP-10 (22 services).
   - DB Zone: CMP-12, CMP-13, CMP-14, CMP-15, CMP-16 (1 master + 2 slaves
     each), CMP-17 (3 master + 3 slave), CMP-18 (3 replicas),
     CMP-19 (3 nodes). TCP/JDBC 3306 / TCP 6379 / HTTPS 19200 /
     TCP 5672.
2. **Integration — mediated only**: CMP-04 (HTTPS/BasicAuth) for
   internal cross-app calls; CMP-05 (TCP SASL/SCRAM) for events; CMP-11
   for managed file transfer. No direct app-to-app connections.
3. **SAP**: CMP-31 integrates with CMP-32, CMP-33, CMP-34 over TCP/RFC;
   CMP-35 object storage over HTTPS/BasicAuth.
4. **Other DCs**: US DC hosts CMP-20, CMP-21, CMP-22, CMP-23, INF-09 and
   INF-10 — reached via CMP-04 or VPN/MPLS; CN secondary DC hosts
   CMP-24, CMP-25, CMP-26, CMP-27, CMP-28; Support DC hosts
   CMP-29 and CMP-30 (HTTPS/OAuth2).
5. **Azure satellites**: CMP-36, CMP-37, CMP-38 (HTTPS/OAuth2) and
   CMP-39 (TCP SASL/SCRAM).
6. **External 3PL partners**: CMP-40, CMP-41, CMP-42, CMP-43, CMP-44,
   CMP-45 over HTTPS/OAuth2 or TCP/EDI; CMP-46, CMP-47, CMP-48
   over SFTP.
7. **Auth**: employees via INF-09; external users via INF-10;
   authorization via the central AuthZ platform.
8. Classification Acme Confidential; TLS everywhere; DB credentials in
   K8s Secrets.

Produce: requirements YAML, architecture YAML, draw.io diagram, and a
validation report — every arrow labeled with protocol, port, and auth.
