# One-shot prompt — Data Agent Platform (hybrid)

> Codes-only prompt. Every system/service is referenced by `SYS-nn`,
> resolved through `input/systems-registry.md` (include that registry as
> context when supplying this prompt to an agent). No literal system names
> appear outside the registry.

Design the technical architecture for an internal data-agent
platform, deployed hybrid across the primary private DC (China) and Azure.

Requirements:

1. **Users & auth**: Tenant admins and platform admins access from the
   office network only. Authentication via SYS-07
   with SYS-06 as the internal STS fallback.
2. **Private DC, App Zone, SYS-10**: three workloads —
   SYS-01 (nginx, static hosting + API proxy, also serves the
   dashboard UI), SYS-02 (Node.js: agent API, SSE streaming, agent
   tools), SYS-03 (Node.js: alerts and digests).
3. **Private DC, DB Zone**: SYS-04, reachable only from App Zone
   over TCP 5432; virtual IP TBD.
4. **Outbound control**: SYS-05 on a Rocky
   9.8 VM in App Zone is the ONLY path from the DC to Azure. No pod
   may have direct internet/cloud egress.
5. **Azure**: (a) SYS-08 in azure-eastus
   exposes governed data namespaces to the agent over HTTPS 443; (b) SYS-09
   in azure-eastus2 with two model pools (overseas / China), reachable
   only via private endpoint; SYS-02 calls it over HTTPS 443 through
   SYS-05.
6. **Classification**: Acme Confidential. Prompt/response payloads must not
   leave controlled paths; all traffic TLS 1.2+; DB credentials in K8s
   Secrets.
7. All cross-component calls must show protocol + port + auth on the diagram.

Produce: requirements YAML, architecture YAML, draw.io diagram, and a
validation report.
