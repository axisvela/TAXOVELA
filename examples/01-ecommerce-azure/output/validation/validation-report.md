# Architecture Validation Report

## Result

- Project: `01-ecommerce-azure`
- Diagram: `output/diagrams/diagram.png`
- Detected platform: Azure with hybrid private-DC connectivity
- Validation score: **4.29 / 10.00**
- Finding status: **BLOCK** because the score is below 6.0 and 19 findings are `must_fix`
- Finding counts: 19 `must_fix`, 3 `should_fix`, 1 `consider`
- Source SHA-256: `d3e8422e8fcc77a855fd68795ee9b9975ea0feebf978d17a1e0bc5ab0e5e98c8`
- Ruleset digest: `108fb1df631d3340c93c32de423f14b61344465f991d9eb39fbec161675ab124`

This is a technical architecture diagram and passes the validation pre-check. It shows two Azure regions, hub and spoke VNETs, segmented subnets, two private data centers, directional interactions, and labeled hybrid connectivity. The strongest aspects are explicit TLS/authentication labels and the use of Application Gateway WAF v2 for the East US public path.

The design is not ready for enforcement approval. Mandatory Azure hub services and security control nodes are absent from the rendered view, the public API path bypasses APIM, application identities and runtimes remain generic or TBD, regional boundaries are duplicated, and the US-Japan flow lacks data-classification and compliance-basis labeling.

## Scoring

The six raw scores are on a 0-10 scale. Each weighted contribution is `raw_score * weight / 10`; weights total 10.0. The exact normalized total is `0.80 + 0.80 + 0.64 + 1.20 + 0.40 + 0.45 = 4.29`.

| Dimension | Raw score | Weight | Weighted score | Principal deductions |
|---|---:|---:|---:|---|
| Cloud_Network_Completeness | 4.0 | 2.0 | 0.80 | Incomplete regional hubs; duplicated Region boundaries; non-standard hub interconnect; no private DNS architecture; NSGs absent; DR/zone redundancy absent |
| Connectivity | 8.0 | 1.0 | 0.80 | Cross-boundary links generally identify type and encryption; Japan hybrid path has no independent failover |
| Technical_Component_Completeness | 3.2 | 2.0 | 0.64 | Generic component names; custom stacks and versions are TBD; multiple runtimes/database engines are unspecified; observability components absent |
| Interaction_Integration | 6.0 | 2.0 | 1.20 | Protocol/authentication labels and directional arrows are strong; APIM is absent and cross-application service calls are not mediated by an integration platform |
| Security_Compliance | 2.0 | 2.0 | 0.40 | Entra ID, AuthZ Platform, Key Vault, Bastion/JIT, at-rest encryption relationships, and cross-border compliance labeling are absent from the view |
| Terminology_Expression | 4.5 | 1.0 | 0.45 | Azure VNET terminology and a legend are present; physical boundaries use dashed lines, legend coverage is incomplete, generic icons and clipped labels impair review |

## Detailed Deductions

### Cloud And Network

1. **Incomplete hubs (`E-AZ-001`, must fix).** SYS-01 and SYS-04 show Azure Firewall and ExpressRoute gateways, but not Azure Bastion, DNS/DNS forwarding, or monitoring/SIEM collection. Add these services to each physical Region's hub VNET and show their operational relationships.
2. **Duplicated Region boundaries (`E-008`, must fix).** East US and Japan East are repeated as independent outer boxes around individual VNETs. Draw one Region boundary per Region, then nest the dedicated hub and spoke VNETs under it.
3. **Non-standard regional hub interconnect (`AZ-STD-TOPOLOGY-REGIONAL-HUB`, must fix).** Replace or formally justify Global VNet peering between SYS-06 and SYS-08. The supplied Azure standard requires ExpressRoute Global Reach or VPN between regional hubs.
4. **Incomplete Private Endpoint DNS (`E-AZ-008`, must fix).** SYS-16 is labeled as private-endpoint storage, but Private DNS Zone, DNS forwarding, and Firewall DNS proxy are not shown. Add independent DNS components and resolution paths; state that public network access is disabled.
5. **No NSG controls (`AZ-STD-AZURE-POLICY-NSG`, must fix).** Add an NSG association to every Azure subnet. Where a subnet hosts multiple applications, also identify ASGs and the permitted east-west flows.
6. **DR and high availability not demonstrated (`AZ-STD-DISASTER-RECOVERY`, must fix).** Add zone redundancy or regional replication for APIM, Key Vault, Storage, and DNS; identify multi-zone AKS node pools and Private Endpoint/Private DNS failover. If Japan is a service region, add equivalent ingress; otherwise relabel its role and recovery behavior.

### Connectivity

Cross-boundary ExpressRoute, MPLS, VPN, VNet peering, and Global VNet peering relationships are labeled with connection type and encryption/authentication details. This materially satisfies `E-009` and `E-010` for visible links.

7. **Japan circuit is a single point of failure (`AZ-STD-HYBRID-RESILIENCE`, should fix).** Add a second ExpressRoute circuit on an independent carrier and peering location, or an explicitly sized site-to-site VPN failover path. Show routing preference and failover behavior.

### Technical Components

8. **Generic component identity (`E-011`, must fix).** Replace names such as `AKS (BU)`, `App VMs`, `Shared services`, `App (AP)`, and `DC systems` with actual deployments/services and state component category. Black-box systems may remain grouped only if their interfaces and ownership boundary are explicit.
9. **Missing language/framework/version (`E-012`, must fix).** For each custom application, show language, framework, major version, and deployable name. The blueprint explicitly says these values remain TBD, preventing vulnerability and lifecycle assessment.
10. **Missing runtime/engine (`E-013`, must fix).** Specify runtimes for SYS-13, SYS-15, SYS-18, SYS-19, SYS-20, and SYS-21. Identify both database engines, hosting models, versions/SKUs, and whether they are managed PaaS reached by Private Endpoint.
11. **Observability absent (`AZ-STD-OBSERVABILITY`, should fix).** Add regional or centralized Log Analytics, Azure Monitor alerts, diagnostic settings, and flows from Firewall, Application Gateway, APIM, NSG flow logs, AKS/VM workloads, databases, Storage, Key Vault, and DNS.

### Interaction And Integration

The 36 blueprint relationships provide a useful protocol, authentication, and encryption inventory, and the rendered paths are directional rather than bidirectional. The blueprint was used to resolve labels that are clipped or overlapped in the PNG; it was not used to treat absent diagram nodes as present.

12. **No APIM on external API ingress (`E-AZ-004`, must fix).** Add Azure API Management in Internal VNET mode inside an application Spoke VNET. The required path is Internet to Application Gateway WAF v2 to APIM to private backend, with APIM authentication/authorization, throttling, quota, and policy responsibilities shown.
13. **Cross-application direct calls (`W-006`, must fix).** SYS-11 and SYS-12 call SYS-15 through a firewall hairpin but without API or message integration mediation. Insert APIM/APIH/Kafka as appropriate, represent it as an independent node in a named subnet, and label each caller-to-platform and platform-to-provider relationship.

### Security

14. **External identity provider absent (`S-005`, must fix).** Add Microsoft Entra ID as an independent node and connect customers, the entry point, and the relying application using OIDC Authorization Code with PKCE. An auth label alone does not expose the identity trust boundary.
15. **Authorization architecture absent (`S-006`, must fix).** Add AuthZ Platform or explicit application-level RBAC/ABAC components and show enforcement points and principal/role propagation.
16. **Key Vault absent (`E-AZ-005`, must fix).** Add regional Key Vault nodes with Private Endpoints and Private DNS; connect all workloads and infrastructure requiring secrets, certificates, or CMKs. Label managed identity, RBAC, automated rotation, soft-delete, purge protection, and recovery ownership.
17. **Operational access absent (`E-AZ-006`, must fix).** Add Azure Bastion Standard to each regional hub, show Corporate PAW to Bastion to private workload access, label Entra ID/MFA and Defender for Cloud JIT, and show NSGs allowing administrative ports only from Bastion ranges.
18. **Cross-border governance absent (`S-008`, must fix).** Classify the SYS-06 to SYS-08 data flow, resolve PII/payment-data scope, identify purpose and allowed fields, and record the applicable transfer mechanism/legal basis for US-Japan processing. If no regulated data crosses, state and enforce that restriction explicitly.
19. **At-rest control not visible (`AZ-STD-DATA-SECURITY-AT-REST`, must fix).** Label AES-256/TDE/platform encryption for SYS-13, SYS-16, and SYS-19 and connect CMKs to Key Vault where required. Resolve key ownership and rotation instead of leaving them as open items.

### Diagram Expression

20. **Physical boundaries shown as logical (`V-001`, must fix).** Change physical Subnet and private-DC Zone borders to solid under the supplied validation rule, reserving dashed borders for logical concepts. Ensure any approved style exception is reconciled in the governing ruleset rather than implied visually.
21. **Legend incomplete (`V-008`, must fix).** Expand the legend to explain every boundary line style, arrow semantics, ownership/status color, connection style, protocol/authentication label format, and service shape used in the diagram.
22. **Generic iconography (`V-104`, should fix).** Use official Azure icons for Firewall, Application Gateway, ExpressRoute Gateway, AKS, Storage, Key Vault, Bastion, APIM, Entra ID, Monitor, and DNS while retaining the shape semantics required by the company diagram specification.
23. **Clipped and colliding labels (`V-007`, consider).** Shorten labels or increase canvas/node spacing. Keep IDs in nodes and move full resource names, protocols, and control details to aligned callouts so every relationship can be reviewed directly from the PNG.

## Priority Recommendations

1. Rebuild each regional boundary around one hub and its spokes; add the mandatory Bastion, DNS, monitoring/SIEM, NSG, Key Vault, and Private Endpoint controls.
2. Correct the application edge to `Internet -> Application Gateway WAF v2 -> APIM Internal -> private workloads`, and mediate cross-application calls through an approved integration platform.
3. Resolve the TBD workload names, stacks, runtimes, database engines, data classifications, key ownership, and compliance obligations, then render those facts in the diagram.
4. Define multi-region recovery, zone redundancy, Japan hybrid failover, and the approved regional-hub interconnect before revalidation.
5. Correct physical boundary styles, expand the legend, and remove label clipping so the PNG is independently reviewable.

## Validation Provenance

The ruleset digest is SHA-256 over a deterministic ordered byte stream. Each input contributes its repository-relative path followed by LF and then its exact file bytes. Ordered inputs were:

1. `.agents/skills/arch-validate/rules/accuracy-rules.yaml`
2. `.agents/skills/arch-validate/rules/compliance/terminology.yaml`
3. `.agents/skills/arch-validate/rules/diagram-rules.yaml`
4. `.agents/skills/arch-validate/rules/interaction-rules.yaml`
5. `.agents/skills/arch-validate/rules/platform-rules.yaml`
6. `.agents/skills/arch-validate/rules/security-rules.yaml`
7. `standards/azure-standard.yaml`
8. `config.yaml`
9. `examples/01-ecommerce-azure/config.yaml`

The machine-readable contract is `validation/v1`. This report does not constitute an enforcement decision; the enforce stage has not been run.
