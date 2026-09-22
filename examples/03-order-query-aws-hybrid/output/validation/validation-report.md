# Architecture Validation Report

## Result

- Project: `03-order-query-aws-hybrid`
- Diagram: `output\diagrams\diagram.png`
- Platform detected: mixed (`AWS + private cloud + existing Azure source boundaries`)
- Score: **5.54 / 10.00**
- Validation disposition: **BLOCK candidate** (`20 must_fix`); enforcement was not run
- Findings: **27 total** (`20 must_fix`, `5 should_fix`, `2 consider`)
- Diagram SHA-256: `bd924bd03b007f9bea6a20d1cab1892c1683f269eca4be6477080a3aa6e16633`
- Ruleset digest: `54f0a273accf65bde893b44e7b4f375f23929acf529b0e98f26d63147ed68425`
- Validator: `arch-validate/openai-gpt-5.6-sol+archharness-0.7.0`
- Validated at: `2026-09-15T00:55:02+00:00`

This is a technical architecture diagram and passes the Step 0 pre-check. It contains seven deployment boundaries, 65 technical components, and 61 one-way interaction edges. Every XML edge has protocol and authentication text and no bidirectional edge was found, but the delivered PNG is too dense for many labels to be reliably read or associated with their edge.

## Source Binding

The PNG hash was recomputed and exactly matches `working/manifests/diagram.png.manifest.json`. The ruleset digest is SHA-256 over this ordered sequence, including each absolute UTF-8 path, a NUL separator, the exact file bytes, and a trailing NUL separator:

1. `.agents/skills/arch-validate/rules/accuracy-rules.yaml`
2. `.agents/skills/arch-validate/rules/platform-rules.yaml`
3. `.agents/skills/arch-validate/rules/interaction-rules.yaml`
4. `.agents/skills/arch-validate/rules/security-rules.yaml`
5. `.agents/skills/arch-validate/rules/diagram-rules.yaml`
6. `.agents/skills/arch-validate/rules/compliance/terminology.yaml`
7. `standards/aws-standard.yaml`
8. `standards/private-cloud-standard.yaml`
9. `standards/eval-weights.yaml`
10. `standards/diagram-style.yaml`
11. `examples/03-order-query-aws-hybrid/config.yaml`

`output/designs/blueprint.yaml` was used as corroborating metadata and topology intent, but it is not included in the ruleset digest because it is design evidence, not a validation rule. A statement present only in the blueprint does not cure a missing or contradictory visual control.

## Weighted Score

| Dimension | Raw / 10 | Weight | Weighted | Principal deductions |
|---|---:|---:|---:|---|
| Cloud_Network_Completeness | 7.86 | 2.0 | 1.57 | 2/7 public-cloud regions unresolved; 1/7 infrastructure owners unresolved; 3/7 cloud domains lack required explicit topology/segmentation |
| Connectivity | 0.00 | 1.0 | 0.00 | 4/4 private-DC-to-AWS links lack compliant Direct Connect/equivalent termination through TGW/Hub firewall and tunnel-encryption definition |
| Technical_Component_Completeness | 6.29 | 2.0 | 1.26 | 19/38 custom app components lack concrete stack metadata; 40/65 components lack runtime metadata |
| Interaction_Integration | 6.00 | 2.0 | 1.20 | Required AWS external API path and S3 private endpoint are absent; dense labels prevent reliable protocol/auth association in the PNG |
| Security_Compliance | 5.55 | 2.0 | 1.11 | Secrets/KMS, AWS/private-DC operations, F5 ingress, AuthZ, tier enforcement, and cross-border control evidence are incomplete |
| Terminology_Expression | 4.00 | 1.0 | 0.40 | Private-DC cloud terminology, clipped labels, line crossings, generic cloud icons, and naming defects |
| **Total** |  | **10.0** | **5.54** | Sum of weighted scores |

The standard formula is `weighted_score = weight * (1 - deduction_ratio)`, equivalent to `raw_score / 10 * weight`. Scores are rounded to two decimals only after each dimension is assessed; the stored weighted scores sum exactly to `5.54`.

### Cloud And Network

- Location deduction: `0.25 * 2/7 = 0.07143`. Azure US and Azure CN have TBD Regions. All four private DCs have city-level labels and AWS identifies N. Virginia.
- Ownership deduction: `0.25 * 1/7 = 0.03571`. AWS ownership remains TBD.
- Segmentation/topology deduction: `0.25 * 3/7 = 0.10714`. AWS lacks explicit Hub/Spoke and VPC topology; both Azure boundaries lack explicit VNET/Subnet/endpoint placement.
- Duplication deduction: `0.25 * 0/7 = 0.00000`. No duplicate Region/DC boundary was found.
- Total deduction ratio: `0.21428`; raw score `7.86`; weighted score `1.57`.

The AWS boundary has public, app, and DB subnets, but a three-tier workload VPC is not the mandated Hub-Spoke topology. Missing Hub services include centralized Network Firewall/security appliance, Transit Gateway, Route 53 Resolver/private hosted zones, SIEM/monitoring services, and PAW/SSM operations. SYS-05 is improperly deployed in the public subnet.

### Connectivity

Four region-level private-DC-to-AWS edges are present. They are all labeled `MPLS with application TLS 1.2+`, so no edge is silently unlabeled. However, none defines the required AWS Direct Connect or documented equivalent termination, Transit Gateway attachment, central Hub firewall inspection, or IPSec/tunnel encryption. All four fail the applicable AWS/private-cloud hybrid baseline, producing raw and weighted scores of zero for this dimension.

Application-level Azure/DC and Internet paths show HTTPS or Kafka/TLS but do not establish the underlying cross-boundary network service. These are included in the remediation requirement but were not added again to the four region-link denominator, avoiding double counting.

### Technical Components

- Name/type: `0/65` structurally missing in the blueprint/XML inventory. Shape and identifiers make types machine-recoverable, although PNG clipping is scored under expression.
- Technology stack: `19/38` custom FE/BE/API components lack concrete language/framework information. Deduction ratio contribution: `0.333 * 19/38 = 0.16650`.
- Runtime: `40/65` components lack a runtime field or runtime frame. Deduction ratio contribution: `0.333 * 40/65 = 0.20492`.
- Total deduction ratio: `0.37142`; raw score `6.29`; weighted score `1.26`.

Version placeholders remain visible in 21 component annotations. This is distinct from complete stack absence: a named Java/Spring stack with unresolved versions is a should-fix, while no concrete stack at all is a must-fix.

### Interactions

The draw.io source confirms 61 edges, all single-direction and all carrying non-empty protocol and authentication values. Kafka-related interactions target Kafka nodes, and the known cross-system source paths generally terminate at APIM/APIH/Kafka mediation nodes.

The material failures are:

- AWS external API ingress does not implement `Internet -> ALB/WAF -> configured APIM in private Spoke -> backend via PrivateLink`.
- S3 is reached without a rendered VPC Endpoint and Private DNS/end-point policy.
- The PNG places many labels on top of other labels, components, and crossing lines. Metadata existing in XML is not sufficient when the governed image cannot be reviewed visually.
- All 61 ports remain TBD. Ports are not scored as missing protocol under the shape specification, but they must be resolved before implementation.

### Security

The positive controls are ADFS and Enterprise ID with SAML, TLS-bearing application protocols, OAuth/SASL labels, DMZ and private-zone separation, and Kafka/API mediation for the major source-system paths.

The score deduction covers three security families:

- System authentication/boundary controls: edge auth is present, but the private-DC Internet path bypasses mandatory F5 and two AWS DB paths bypass the drawn App firewall.
- User authentication/authorization: both IdPs are present, but one of three required identity control families, AuthZ Platform/application RBAC evidence, is not rendered and remains TBD in the blueprint.
- Credential/data protection: Secrets Manager/KMS is textual rather than a governed node/control path; private-DC credential storage is unresolved; and the PRC-to-US edge has no visible classification or legal basis.

No operational path is drawn for AWS or any private DC. The blueprint statement `PAW / AWS Systems Manager ... final operating model TBD` is not deployable evidence.

### Terminology And Visual Quality

The dc-us private data center incorrectly uses `Public subnet (DMZ)` instead of private-DC Zone/VLAN/Segment terminology. The legend exists, databases and API gateways mostly use recognizable shapes, and ownership/status colors are broadly consistent.

The image is 1238x2794 and is not reviewable at normal scale in its densest section. Component names visibly end in bracketed ellipses; the AWS app tier overlays technology annotations and protocol/auth labels; and crossing lines make source-to-target association ambiguous. Re-layout into separate views or pages is a must-fix, not a cosmetic suggestion.

## Must Fix

1. Add an AWS regional Hub VPC and a separate workload Spoke VPC/account boundary; show Network Firewall, TGW, Route 53 Resolver/private DNS, central logging/SIEM, and PAW/SSM.
2. Move SYS-05 out of the public subnet. Keep only ALB/WAF ingress components public and prevent workload public IP assignment.
3. Implement the configured private API gateway path behind ALB/WAF and show PrivateLink/private backend routing.
4. Add S3 VPC Endpoint, endpoint policy, and Private DNS; disable public S3 access.
5. Draw IAM-role, Secrets Manager, and KMS relationships and resolve automatic rotation.
6. Draw separate AWS and private-DC privileged operations paths with PAW/SSM, MFA, JIT, and audit/session logging.
7. Route every App-to-DB interaction through the actual boundary control or redraw the control topology accurately.
8. Put mandatory F5 on private-DC Internet ingress before DMZ-APIM.
9. Replace or qualify all four MPLS-to-AWS links with Direct Connect/equivalent termination, TGW, Hub firewall routing, redundancy, and tunnel/link encryption.
10. Resolve both Azure Regions, AWS ownership, Azure VNET/Subnet/endpoint placement, and dc-us Zone terminology.
11. Complete concrete stack metadata for 19/38 custom components and runtime metadata for 40/65 components.
12. Draw AuthZ Platform/RBAC enforcement relationships.
13. Label the PRC-to-US path with classification, permitted payload, prohibited row data, purpose, legal basis, and control owner.
14. Split/re-layout the diagram so every component and edge label is fully visible and unambiguous.

## Viewpoint Coverage

| PACT layer | Coverage | Note |
|---|---|---|
| Business | Partial | OQP purpose and owner labels exist; accountable AWS owner is TBD |
| Application | Present | Application/service inventory is extensive |
| Integration | Present | APIM/APIH/Kafka and 61 interactions are represented |
| Data | Present | Stores and residency intent are represented; cross-border semantics are incomplete |
| Security | Partial | Identity and edge auth exist; Hub, secrets, operations, AuthZ, and F5 controls are incomplete |
| Infrastructure | Partial | DC/cloud zones exist; required Hub-Spoke and hybrid termination are absent |
| Governance | Partial | Version/classification concepts exist; owners, legal basis, and approvals remain TBD |
| Operations | Absent | No deployable management, monitoring, SIEM, backup, or DR view is rendered |

## Enforcement Readiness

`validate_result.json` is the deterministic input expected by the enforce stage. It is intended to be schema-validated, hash-manifested with an absolute path, recorded under workflow artifact name `validate_result.json`, and followed by workflow completion of `validate`. No enforce command or policy evaluation is part of this report.
