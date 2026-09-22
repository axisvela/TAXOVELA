# One-shot prompt — Service Delivery Platform (SDP)

> Codes-only prompt. Every system/service is referenced by `SYS-nn`,
> resolved through `input/systems-registry.md` (include that registry as
> context when supplying this prompt to an agent). No literal system names
> appear outside the registry.

Design the technical architecture for **SDP**, our service supply-chain
operations platform, as it migrates to serve NA. Private cloud only, four
DCs, ~40 Java/SpringCloud microservices.

Requirements:

1. **CN primary DC, three-tier**:
   - Ingress via SYS-01 (TLS termination, OAuth2) into the DMZ, behind the
     network edge router SYS-52.
   - DMZ K8s cluster: SYS-02, SYS-03, SYS-04.
   - Intranet K8s cluster: SYS-07, SYS-08, SYS-09, plus two service
     groups — SYS-10 (10 services) and SYS-11 (22 services).
   - DB Zone: SYS-12, SYS-13, SYS-14, SYS-15, SYS-16 (1 master + 2 slaves
     each), SYS-17 (3 master + 3 slave), SYS-18 (3 replicas),
     SYS-19 (3 nodes). TCP/JDBC 3306 / TCP 6379 / HTTPS 19200 /
     TCP 5672.
2. **Integration — mediated only**: SYS-05 (HTTPS/BasicAuth) for
   internal cross-app calls; SYS-06 (TCP SASL/SCRAM) for events; SYS-51
   for managed file transfer. No direct app-to-app connections.
3. **SAP**: SYS-20 integrates with SYS-21, SYS-22, SYS-23 over TCP/RFC;
   SYS-24 object storage over HTTPS/BasicAuth.
4. **Other DCs**: US DC hosts SYS-25, SYS-26, SYS-27, SYS-28, SYS-29 and
   SYS-30 — reached via SYS-05 or VPN/MPLS; CN secondary DC hosts
   SYS-31, SYS-32, SYS-33, SYS-34, SYS-35; Support DC hosts
   SYS-36 and SYS-37 (HTTPS/OAuth2).
5. **Azure satellites**: SYS-38, SYS-39, SYS-40 (HTTPS/OAuth2) and
   SYS-41 (TCP SASL/SCRAM).
6. **External 3PL partners**: SYS-42, SYS-43, SYS-44, SYS-45, SYS-46,
   SYS-47 over HTTPS/OAuth2 or TCP/EDI; SYS-48, SYS-49, SYS-50
   over SFTP.
7. **Auth**: employees via SYS-29; external users via SYS-30;
   authorization via the central AuthZ platform.
8. Classification Acme Confidential; TLS everywhere; DB credentials in
   K8s Secrets.

Produce: requirements YAML, architecture YAML, draw.io diagram, and a
validation report — every arrow labeled with protocol, port, and auth.
