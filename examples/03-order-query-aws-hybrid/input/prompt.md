# One-shot prompt — Order Query Platform (OQP ROW)

> Codes-only prompt. Every system/service is referenced by `SYS-nn`,
> resolved through `input/systems-registry.md` (include that registry as
> context when supplying this prompt to an agent). No literal system names
> appear outside the registry.

Design the architecture for **OQP ROW**, a global order-query platform.
The platform runs on **AWS US**; order data is federated from systems in
four private DCs and two Azure EDW sources.

Requirements:

1. **AWS US VPC**, three-tier subnets mirroring our private-DC standard:
   - Public subnet (DMZ): front-end K8s cluster running SYS-05.
   - Private subnet (App Zone): backend K8s cluster — SYS-06 plus
     services SYS-07 through SYS-23 (portal, report, notification,
     transform, task, web UI, nine Kafka consumers SYS-13–SYS-21,
     consumer task, job scheduler). SYS-24 sits beside the cluster.
   - Private subnet (DB Zone): SYS-25 and SYS-26 (TCP/JDBC), SYS-27
     (TCP), and SYS-28 (HTTPS).
2. **Users**: internal employees via SYS-01 (SAML), external partners via
   SYS-02 (SAML). Both IdPs live in the US DC. SYS-03 and SYS-04 already
   exist in the US DC DMZ and link to OQP ROW.
3. **Integration — nothing direct**: every cross-system call goes through
   SYS-29 (external), SYS-30 (internal, US DC), or SYS-31 (NA-DC
   integration zone) over HTTPS/OAuth2, or through the designated Kafka
   cluster over TCP (SASL/SCRAM): SYS-32 (US DC), SYS-33 (CN primary DC),
   SYS-34 (CN secondary DC), SYS-35 + SYS-36 (NA-DC).
4. **Sources**: SYS-54 (SaaS), SYS-55 and SYS-56 (Azure US), SYS-57
   (Azure CN North — data stays in-country), SYS-48 + SYS-49 (CN primary),
   SYS-42–SYS-47 (CN secondary), and SYS-50–SYS-53 (NA-DC).
5. **US DC systems**: SYS-38, SYS-39, SYS-40, and SYS-41 are US DC
   backends reached through the mediations above; SYS-37 is the search
   store in the US DC / NA DB zone.
6. **Platform**: SYS-58 is the internal K8s platform underlying every
   K8s cluster in this design.
7. **WAN**: MPLS connects every DC to the AWS VPC; every boundary has a
   firewall; TLS everywhere.
8. **Classification**: Acme Confidential; PRC-sourced rows must remain in
   China (query via SYS-15 against SYS-57, no replication).

Produce: requirements YAML, architecture YAML, draw.io diagram, and a
validation report — every arrow must carry protocol, port, and auth.
