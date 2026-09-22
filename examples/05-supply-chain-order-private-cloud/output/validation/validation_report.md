# Strict Architecture Validation Report

## Result

- Schema: `validation/v1`
- Detected platform: mixed (`private_dc` primary with AWS and Azure peer deployments)
- Score: **5.81 / 10.00**
- Findings: **24 must_fix**, **4 should_fix**, **0 consider**
- Expected deterministic enforcement outcome: **BLOCK** because score is below 6.0 and `must_fix > 0`
- Enforcement was not run.

## Source Binding

- PNG: `output\diagrams\diagram.png`
- PNG SHA-256: `5833dcc6754605bdb4de12755ca580b517c11b2eaa424434c81140bfa509768d`
- Blueprint SHA-256: `7978252bb1e33a53d3e2563a2d1f4f30de8db6c806d057926382478a87b1dd8c`
- Project config SHA-256: `27f8f10e8b7e3a31c62272cc8097c5f6484461edd1bb2bdf1de2bd21fa1f266c`
- Private-cloud standard SHA-256: `5d4b58b20f7d7c51353d343b40ca4367d0bd583de7e7aa4e36fc3a998539329b`
- Accuracy rules SHA-256: `66fea97f1f49079fd82f1774b0ddae7471833e819d499faf196f092bddfae608`
- Platform rules SHA-256: `5100a4a1b29a6da375cad39b7dbeac25989f4eb7c6b4f8d7e422f54ebd7b5872`
- Interaction rules SHA-256: `d2ee56b20603e3b7176469faf2db4a11cf3782574b7d4604e9a3077f5fffbd8d`
- Security rules SHA-256: `19bec5060316d8f7387e00da0edb1c1876f6ab31c9a4f39a4ed984d8c8d29a13`
- Diagram rules SHA-256: `946a2b1f55089bd265ffb125577b6115daa1ca0cffad9d99ad67403e94fb2c7c`
- Terminology rules SHA-256: `bfb172e179930ee57c7392ea779e945cb41e7a1c5e712e7923b4049a570e0298`
- Ruleset digest: `sha256:dbead7910d2389e078f45c6074c13ddfe070a4b99c32634d3b551abcbaae90dd`
- Digest construction: SHA-256 over each rules/config path relative to repository root, NUL, exact file bytes, NUL, in the order listed above beginning with project config.

## Exact Inventory

- Deployment containers: 5 total (3 private DC, 1 AWS, 1 Azure)
- Zone/subnet containers: 12 total
- Components: 60 total
- Component types: 3 API, 27 BE, 9 DB, 2 FE, 8 IP, 4 LB, 4 MQ, 2 NW, 1 SEC
- Interactions/arrows: 103 total
- Protocols: 53 HTTPS, 2 HTTPS/SAML 2.0, 22 Kafka, 14 JDBC, 8 RFC/SNC, 2 AMQPS, 2 RESP/TLS
- Blueprint interaction fields: 0 missing protocol, 0 missing authentication, 0 missing encryption
- Draw.io arrows: 103 single-direction arrows, 0 bidirectional styles, 0 empty edge labels
- Physical-border violations: 34 component nodes plus 10 zone/subnet containers = 44

## Dimension Scores

| Dimension | Raw | Weight | Weighted | Principal deductions |
|---|---:|---:|---:|---|
| Cloud_Network_Completeness | 6.50 | 2.0 | 1.30 | Missing CN DMZ; unapproved NA EARTH ingress zone; duplicated City C DC; incomplete AWS/Azure network models; Azure Region absent |
| Connectivity | 2.10 | 1.0 | 0.21 | 7/7 cross-boundary paths lack connection type; 4/7 lack explicit encryption labels |
| Technical_Component_Completeness | 7.00 | 2.0 | 1.40 | 47/60 runtime environments absent from PNG; 2/60 placeholder service names |
| Interaction_Integration | 9.10 | 2.0 | 1.82 | 6 direct SAP calls bypass mediation; 2/103 Kafka arrows violate target direction |
| Security_Compliance | 3.50 | 2.0 | 0.70 | Ingress proof/firewalls, AuthZ, cloud credential nodes, cross-border basis, and all five deployment operations paths absent |
| Terminology_Expression | 3.80 | 1.0 | 0.38 | 44 physical entities dashed; severe label/line overplotting; nonstandard service shapes |
| **Total** |  |  | **5.81** | Weighted scores sum exactly to 5.81 |

## CN And NA Accuracy

- CN config requires `DMZ`, `Intranet`, `App Zone`, and `DB Zone`. The PNG has no `DMZ`; SYS-01 through SYS-04 are in `Intranet` even though the private-cloud standard requires the web ingress tier in DMZ.
- NA config requires `NA-PROD-INA-K8S`, `NA-PROD-INA-INTEGRATION`, `NA-PROD-INA-SAP`, `NA-PROD-INA-SERVER`, and `NA-PROD-INA-DB`. All five appear, but `NA-PROD-INA-EARTH` is an unapproved sixth zone holding ingress components, and no DMZ is shown.
- `dc-us` and `dc-us-identity` repeat `City C, State X [US]` as separate private-DC nodes, violating the single-container requirement for one physical DC/location.

## Ingress, F5, And WAF

- SYS-01 and SYS-28 are visible F5 nodes, and SYS-02/SYS-29 WAFs are symmetric.
- No interaction originates at the Internet symbol. The blueprint starts each path at F5, so the diagram does not prove that public ingress traverses F5.
- Both ingress stacks are inside intranet-style zones, not DMZ.
- Required Internet-to-DMZ and DMZ-to-internal firewall boundaries are absent.
- Both WAFs are `in_plan` and described as optional. This is not treated as a substitute for mandatory F5 or firewall controls.

## SAP And CDC Mediation

- Six SAP function-call paths bypass an integration platform: SYS-06/07/09 to SYS-20/21 and SYS-33/34/36 to SYS-45.
- The two CDC chains are correctly mediated: SAP -> Debezium -> RabbitMQ -> regional Kafka.
- Cross-region synchronization uses Kafka only and does not show direct database replication, which is compliant with the blueprint intent.
- Two Kafka consumer relationships are drawn Kafka -> consumer (`SYS-17 -> SYS-54`, `SYS-42 -> SYS-55`); V-003 requires consumer -> Kafka.

## Credentials And Data Protection

- Private-cloud/Kubernetes prose declares encrypted K8s Secrets, external vault synchronization, rotation, and no hardcoded credentials. Connection labels consistently reference K8s Secrets for SAP, RabbitMQ, and database credentials.
- AWS and Azure credential controls are prose-only. Required IAM Role plus Secrets Manager/KMS and Managed Identity plus Key Vault nodes/relationships are absent from the PNG.
- Both CN/NA Kafka arrows omit the data classification and an approved legal/compliance basis. Saying a legal basis is required does not establish one.
- Database-at-rest controls are present in blueprint notes but not visible on the nine store nodes.

## Operations

- Blueprint prose defines `Office Network -> PAW with MFA -> approved private management plane`, named privileged accounts, logging, and time-bounded access.
- No PAW, office network, management plane, MFA/JIT, or target path is drawn for any of the three private-DC containers.
- No PAW/Systems Manager path is drawn for AWS and no Azure Bastion Standard/JIT path is drawn for Azure.
- Result: 5/5 deployment containers lack a visible governed operations path.

## Visual Review

- The PNG is a technical architecture diagram and passes the basic pre-check.
- The diagram is materially over-dense: 103 opaque protocol/auth labels and many crossing lines are routed through narrow application columns containing 60 components.
- Labels obscure component names, other relationship labels, and zone contents across both regional stacks; central CN/NA and database paths are especially difficult to trace at normal scale.
- Tooltips contain runtime details but are not available in the PNG, so they cannot satisfy an exported-diagram review.
- The legend exists, but it does not cure the dashed-border misuse or dense relationship ambiguity.

## Must Fix

1. Restore approved CN/NA ingress zones, move ingress/web components into DMZ, and draw Internet -> F5 plus both required firewall boundaries.
2. Route all six SAP function calls through approved regional integration platforms while retaining the mediated CDC chains.
3. Add explicit MPLS/equivalent, Direct Connect, and ExpressRoute topology with encryption labels; correct the two Kafka consumer arrows.
4. Draw AuthZ, credential-management, cross-border compliance, and PAW/Bastion operational controls rather than leaving them only in prose.
5. Correct AWS/Azure Hub-Spoke and VPC/VNET/Subnet/Region representations, merge the duplicate City C DC, use solid physical borders, expose runtime labels, and split the interaction-heavy view into readable views.

The authoritative machine-readable finding list is `validate_result.json`.
