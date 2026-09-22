# One-shot prompt — E-commerce Platform (Azure)

> Codes-only prompt. Every system/service is referenced by `SYS-nn`,
> resolved through `input/systems-registry.md` (include that registry as
> context when supplying this prompt to an agent). No literal system names
> appear outside the registry.

Design the network and application hosting architecture for our e-commerce
platform on **Azure**, with hybrid connectivity to two on-prem data centers.

Requirements:

1. **Two Azure regions**: EastUS (primary, serves the US business unit) and
   JapanEast (serves the AP e-commerce platform). Both regions must follow
   the corporate hub-spoke network standard.
2. **EastUS hub** (SYS-01): firewall instance SYS-06 and hybrid gateway
   SYS-07. All spoke egress must be forced through the firewall via UDR.
3. **EastUS BU spoke** (SYS-02): subnets for SYS-10, SYS-11, SYS-12, SYS-13,
   plus a DMZ subnet.
4. **EastUS common spoke** (SYS-03): shared-backend subnet SYS-15, workload
   cluster subnet SYS-14, and private-endpoint subnet SYS-16.
5. **JapanEast**: same hub-spoke pattern — hub SYS-04 with SYS-08 + SYS-09,
   spoke SYS-05 with SYS-17 / SYS-18 / SYS-19 plus a DMZ subnet.
6. **Hybrid connectivity**:
   - SYS-01 to SYS-20: SYS-22 as primary and SYS-23 as secondary dedicated
     circuits from different carriers, plus SYS-24 and SYS-25 as backup
     paths. Documented RTT ~4 ms.
   - SYS-04 to SYS-21: SYS-26 as primary dedicated circuit.
7. All inter-VNet traffic via peering; no VNet-to-VNet traffic may bypass
   the hub firewall.
8. Data classification: Acme Confidential. No cross-border data residency
   constraints, but all east-west traffic must be inspectable.

Produce: requirements YAML, architecture YAML, draw.io diagram, and a
validation report against the Azure hub-spoke standard.
