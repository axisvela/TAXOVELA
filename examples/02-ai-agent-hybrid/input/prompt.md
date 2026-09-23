# One-shot prompt — Data Agent Platform (hybrid)

> Codes-only prompt. Every system/service is referenced by a typed code
> (`INF-` infra · `APP-` systems · `CMP-` components · the `DEP`/`FLOW`/`LNK`/
> `AUTH` derived layers), resolved through `input/systems-registry.md` (include
> that registry as context when supplying this prompt to an agent). No literal
> system names appear outside the registry.

Design the technical architecture for an internal data-agent
platform, deployed hybrid across the primary private DC (China) and Azure.

Systems and infra in scope: APP-01 through APP-03; INF-01 through INF-10;
CMP-01 through CMP-07.

Requirements:

1. **Users & auth**: Tenant admins and platform admins access from the
   office network only. Authentication via INF-07
   with INF-05 as the internal STS fallback.
2. **Private DC, App Zone, Internal K8s**: three workloads —
   CMP-01 (nginx, static hosting + API proxy, also serves the
   dashboard UI), CMP-02 (Node.js: agent API, SSE streaming, agent
   tools), CMP-03 (Node.js: alerts and digests).
3. **Private DC, DB Zone**: CMP-04, reachable only from App Zone
   over TCP 5432; virtual IP TBD.
4. **Outbound control**: CMP-05 on a Rocky
   9.8 VM in App Zone is the ONLY path from the DC to Azure. No pod
   may have direct internet/cloud egress.
5. **Azure**: (a) CMP-06 in azure-eastus
   exposes governed data namespaces to the agent over HTTPS 443; (b) CMP-07
   in azure-eastus2 with two model pools (overseas / China), reachable
   only via private endpoint; CMP-02 calls it over HTTPS 443 through
   CMP-05.
6. **Classification**: Acme Confidential. Prompt/response payloads must not
   leave controlled paths; all traffic TLS 1.2+; DB credentials in K8s
   Secrets.
7. All cross-component calls must show protocol + port + auth on the diagram.

Produce: requirements YAML, architecture YAML, draw.io diagram, and a
validation report.
