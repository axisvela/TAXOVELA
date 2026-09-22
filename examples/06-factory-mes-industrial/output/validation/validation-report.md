# Factory MES Architecture Validation

**Result:** BLOCK candidate for the subsequent deterministic enforcement stage  
**Score:** 6.171 / 10  
**Must-fix issues:** 11  
**Validated artifact:** `output\diagrams\diagram.png`

Enforcement was not run. The verdict above is descriptive only; `archharness enforce` remains the authority for the enforcement decision.

## Source Binding

| Input | SHA-256 |
|---|---|
| Project config | `c733b1dd175f7d3c327c2da27e1c9801ebfd0b1212a5d18ecf787427be4f3cf6` |
| Blueprint | `79fa16a4ded53929da20b050fd858ce05482fd8049cb45fffa4ebb214aa5c168` |
| PNG | `34683c8d655a36eaebe209766811a4241cc2f641e45c7a7b3c50b8c2f01d7514` |
| Private-cloud standard | `5d4b58b20f7d7c51353d343b40ca4367d0bd583de7e7aa4e36fc3a998539329b` |
| Accuracy rules | `66fea97f1f49079fd82f1774b0ddae7471833e819d499faf196f092bddfae608` |
| Platform rules | `5100a4a1b29a6da375cad39b7dbeac25989f4eb7c6b4f8d7e422f54ebd7b5872` |
| Interaction rules | `d2ee56b20603e3b7176469faf2db4a11cf3782574b7d4604e9a3077f5fffbd8d` |
| Security rules | `19bec5060316d8f7387e00da0edb1c1876f6ab31c9a4f39a4ed984d8c8d29a13` |
| Diagram rules | `946a2b1f55089bd265ffb125577b6115daa1ca0cffad9d99ad67403e94fb2c7c` |
| Terminology rules | `bfb172e179930ee57c7392ea779e945cb41e7a1c5e712e7923b4049a570e0298` |

Ruleset digest `03ee45548c349444517f61a49ff6e792f5d2b47c9003852bd6b9da24e9fb0d35` is SHA-256 over the concatenated lowercase SHA-256 strings, in the table order starting with project config and ending with terminology rules, excluding blueprint and PNG.

## Exact Inventory

| Item | Count |
|---|---:|
| Deployments | 6 |
| Network zones/subnets | 11 |
| Technical components | 44 |
| `SYS-*` components | 38 |
| Interactions / rendered edges | 73 |
| Rendered vertices | 73 |
| Kafka-labeled interactions | 24 |
| Bidirectional edges | 0 |
| Unlabeled edges | 0 |
| Dashed rendered vertices | 42 |
| PNG dimensions | 1254 x 2206 RGBA |

Lifecycle counts are exact: component labels are 4 EXISTING, 13 NEW, and 21 missing/TBD. Interaction labels are 9 EXISTING, 25 NEW, and 39 TBD.

## Dimension Scores

| Dimension | Raw / 10 | Weight | Contribution |
|---|---:|---:|---:|
| Cloud Network Completeness | 7.000 | 2.0 | 1.400 |
| Connectivity | 0.000 | 1.0 | 0.000 |
| Technical Component Completeness | 7.631 | 2.0 | 1.526 |
| Interaction Integration | 9.726 | 2.0 | 1.945 |
| Security Compliance | 5.000 | 2.0 | 1.000 |
| Terminology Expression | 3.000 | 1.0 | 0.300 |
| **Total** |  | **10.0** | **6.171** |

### Scoring Detail

Cloud Network Completeness deducted `1/5 x 0.25 = 0.05` for a private DC missing city-level labeling and `1/1 x 0.25 = 0.25` for absent Azure Hub-Spoke network structure. The resulting deduction ratio is `0.30`, raw score `10 x (1 - 0.30) = 7.00`.

Connectivity has six unique cross-site boundary pairs. All six show encryption, but none identifies an approved connection type: `6/6 x 1.0 = 1.0` deduction, raw score `0.00`.

Technical Component Completeness has no name/type misses. Stack misses are `8/23 x 0.333 = 0.115826`; runtime misses are `16/44 x 0.333 = 0.121091`. Total deduction ratio is `0.236917`, raw score `7.63083`, rounded to `7.631`.

Interaction Integration has four Kafka direction failures and four ambiguous `HTTPS or Kafka/TLS` contracts among 73 interactions. Deductions are `4/73 x 0.25` twice, total `0.027397`, raw score `9.72603`, rounded to `9.726`. There are no bidirectional or unlabeled edges.

Security Compliance applies the full system-auth boundary deduction for the one external path that lacks explicit F5 transit and an additional normalized private-cloud operational-access deduction because PAW is absent from the PNG. ADFS, application RBAC/license authorization, K8s Secrets, Key Vault, mTLS, SAP technical-user auth, and at-rest encryption are present in the blueprint and therefore were not treated as wholly absent controls.

Terminology Expression reflects 42 dashed rendered vertices used for physical zones/components and pervasive label collisions. The legend exists, database/gateway/firewall shapes are generally recognizable, no private-cloud VPC/VNET terminology appears, and no bidirectional arrow is present.

## Must Fix

1. Put an explicitly named F5 gateway on the plant external ingress, or relabel the source as an internal plant network if Internet access is not intended.
2. Draw Office Network -> MFA -> PAW -> management plane and the audited/JIT operational path.
3. Name the carrier on each of six cross-site pairs: MPLS/equivalent for private DC links and ExpressRoute/equivalent approved private connectivity for Azure.
4. Add Azure Hub VNET/Spoke VNET context and show the SYS-38 Private Endpoint and private DNS controls.
5. Reverse or remodel the four Kafka-hub-originating segments so every producer/consumer relationship points to Kafka under the mandated notation.
6. Split the four `HTTPS or Kafka/TLS` alternatives into selected, independently authenticated relationships.
7. Add the 16 missing runtime declarations and 8 missing custom stack declarations listed in `validate_result.json`.
8. Add City C to the `dc-us-na` container title.
9. Render physical zones and deployed components with solid borders; reserve dashed borders for logical concepts.

## Focus Checks

| Check | Result |
|---|---|
| Plant-edge ingress | Fail: Internet reaches a VIP without an explicitly identified F5; source semantics conflict with the intranet-only blueprint note. |
| Plant autonomy | Design evidence passes: local K8s, PgSQL HA, cached sessions/policy, durable outbox, retry/replay. PNG communication is insufficient. |
| Kafka mediation | Cross-application topology is hub-mediated, but 4 of 24 Kafka segments violate the mandated arrow notation. |
| EXISTING/NEW | Fail: 21 of 38 systems and 39 of 73 interactions remain missing/TBD. |
| SAP IDOC/RFC authentication | Pass: IDOC and two RFC paths specify TLS 1.3, mTLS, and least-privilege SAP technical users. |
| Secrets | Design evidence passes with encrypted K8s Secrets, vault-backed rotation, and Key Vault/managed identity; PNG visibility should improve. |
| PAW | Fail: declared in blueprint but no node or path appears in the PNG. |
| Zone model | Project-overlay zones are represented and components are contained; Azure lacks required Hub-Spoke context. |
| Dense labels | Fail: labels overlap heavily and obscure components, endpoints, and security semantics. |

## Coverage

Business is partial; Application, Integration, Data, Security, and Infrastructure are present; Governance and Operations are partial. The principal coverage gaps are operational access topology, carrier ownership/type, migration-state certainty, event-field/cross-border approval, and readable resilience annotations.
