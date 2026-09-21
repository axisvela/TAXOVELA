# One-shot prompt — Factory MES (PlantMES)

> Codes-only prompt. Every entity is referenced by a typed code
> (`INF`/`APP`/`CMP`/`DEP`/`FLOW`/`LNK`/`AUTH-nn`), resolved through
> `input/systems-registry.md` (include that registry as context when supplying
> this prompt to an agent). No literal entity names appear outside the registry.

Design the technical architecture for **CMP-03 through CMP-20** — system APP-01
(PlantMES), the manufacturing execution system of a US plant (site INF-01). The
plant stack must be autonomous (survive WAN outages); integration with central
systems is asynchronous.

Requirements:

1. **Plant-local stack** (site INF-01, zone INF-02):
   - Ingress: INF-13 → CMP-01 / CMP-02 (HTTPS; Nginx).
   - K8s cluster: CMP-03 + CMP-04 + 13 Java/Spring services CMP-05 to CMP-18.
   - Persistence: CMP-19 / CMP-20 on VMs — plant-local only.
2. **Users**: plant intranet — a thick client (with label printing) and a web
   browser, both HTTPS to INF-13 (user auth AUTH-01).
3. **Identity**: external authorization via CMP-21 and INF-14 in INF-03
   (HTTPS through the firewall).
4. **Integration — Kafka only** between plant and central:
   - CN primary DC INF-04: CMP-22 + CMP-23; peers CMP-24 through CMP-27 (TCP).
   - NA DC INF-05 (multi-zone): CMP-28 in INF-08; CMP-29 over TCP/TLS 1.2
     (INF-10); CMP-26 / CMP-30 and CMP-31 in INF-09; **CMP-32 via IDOC**,
     CMP-33 and CMP-34 via RFC (INF-11).
   - CN secondary DC INF-06: CMP-35 over TCP/Kafka.
   - Azure US East INF-07: CMP-36 consumes plant events via Kafka SASL_SSL.
5. **Migration view**: mark each interface as EXISTING (black) or NEW (red) —
   this diagram supports a cut-over plan.
6. Every boundary crossing passes a boundary firewall: INF-15 (plant), INF-16
   (US DC), INF-17 (CN primary), INF-18 (CN secondary), INF-19 (NA DC),
   INF-20 (Azure EDW). TLS everywhere; DB credentials in K8s Secrets;
   classification Acme Confidential.

Systems and infra in scope: APP-01 through APP-07; INF-01 through INF-20;
CMP-01 through CMP-36.

Produce: requirements YAML, architecture YAML, draw.io diagram with new/existing
interface markers, and a validation report.
