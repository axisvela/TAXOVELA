# One-shot prompt — Supply-Chain Order Platform (OSP)

> Codes-only prompt. Every entity is referenced by a typed code
> (`INF`/`APP`/`CMP`/`DEP`/`FLOW`/`LNK`/`AUTH-nn`), resolved through
> `input/systems-registry.md` (include that registry as context when supplying
> this prompt to an agent). CN = INF-01, NA = INF-04 (multi-zone).

Design the technical architecture for **APP-01 (OSP)**, our supply-chain order
platform, deployed **active-active** in two private data centers (CN and NA)
with deep SAP integration and CDC-based synchronization.

Requirements:

1. **Symmetric regions** — the same logical stack (`CMP-01` through `CMP-24`)
   runs active-active in the CN primary DC (INF-01, three-tier) and the NA DC
   (INF-04, multi-zone); each region serves its own employees from INF-13.
   **One component, two deployment units**: Order Creation is `CMP-03`, with one
   deployment in CN and one in NA.
2. **Per-region stack**:
   - Ingress: INF-16 / INF-19 (CN/NA ingress) → INF-17 / INF-20 (CN/NA
     security, optional) → INF-18 / INF-21 (CN/NA edge routing) → CMP-01
     (web tier, Nginx, with internal access authentication).
   - Backend: CMP-02 (gateway, K8s) → CMP-03 through CMP-10 (backend ×8,
     Java/Spring, K8s).
   - Middleware: CMP-15 (messaging) + CMP-16 (CDC source, out of the order
     databases).
   - Persistence: CMP-17 through CMP-21 (HA groups in the DB zone; TCP/JDBC;
     search over HTTPS).
3. **SAP integration**: CMP-33 / CMP-34 in APP-05 (CN) and CMP-35 in APP-06
   (NA) — Function modules and SLT replication, over TCP/RFC/HTTPS;
   IDOC-not-present-here. CMP-35 requires INF-08.
4. **NA multi-zone discipline**: K8s workloads (CMP-01 through CMP-10 and
   CMP-22 through CMP-24) in INF-05; CMP-13 / CMP-14 in INF-06 (the ONLY zone
   allowed to mediate cross-app calls); CMP-15 / CMP-16 in INF-07;
   persistence CMP-17 through CMP-21 in INF-09; CMP-35 in INF-08.
5. **Integration**: internal API calls via CMP-11 / CMP-12 (CN) and CMP-13
   (CN + NA, over HTTPS); events via CMP-14 (TCP, SASL/SCRAM); CDC via
   CMP-16 → CMP-15 → CMP-14. Peer apps: CMP-25 through CMP-29 in APP-02;
   CMP-30 on INF-11 (AWS US); CMP-31 / CMP-32 on INF-12 (Azure US,
   HTTPS / messaging); CMP-22 through CMP-24 in NA (require INF-05).
6. **Auth**: employees via AUTH-01 (HTTPS/SAML to INF-22); RBAC via the
   authorization platform.
7. Classification Acme Confidential; TLS everywhere; credentials in K8s
   Secrets.

Systems and infra in scope: APP-01 through APP-06; INF-01 through INF-22;
CMP-01 through CMP-35.

Produce: requirements YAML, architecture YAML, draw.io diagram, and a
validation report — every arrow labeled with protocol, port, and auth.
