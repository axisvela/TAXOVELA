# Requirements Document — Data Agent Platform
**Version**: 1.0  |  **Project ID**: DAP-001  |  **Classification**: Acme Confidential
**Scope**: New hybrid application (textual names scrubbed; reference image unchanged)

> Resolve the typed codes (`INF-` / `APP-` / `CMP-` and the `DEP`/`FLOW`/`LNK`/`AUTH`
> derived layers) via `input/systems-registry.md` — include that file as LLM context.

---

## 1. Project Overview

This is an internal data-agent platform: admins ask data questions in natural
language; the agent queries governed data namespaces on Azure and
calls models through a controlled service. The agent runtime must remain in the
private DC (China) for data sovereignty; Azure hosts only the data source and
the model service.

## 2. Applications in Scope

| App | Type | New/Existing | Scope |
|-----|------|-------------|-------|
| CMP-01 (web entry + dashboard UI) | Web layer | New | Full stack |
| CMP-02 (Node.js, SSE streaming, agent tools) | Backend | New | Full stack |
| CMP-03 (Node.js, alerts and digests) | Backend | New | Full stack |
| CMP-04 (relational database) | Database | New | Full |
| CMP-05 (nginx egress proxy, Rocky 9.8 VM) | Integration | New | Full |
| INF-05 | Identity | Existing | Integration boundary only |
| INF-07 | Identity | Existing (cloud) | Integration boundary only |
| CMP-06 (governed namespaces) | Data source | Existing (cloud) | Integration boundary only |
| CMP-07 (overseas / China pools) | AI platform | Existing (cloud) | Integration boundary only |

## 3. Physical Deployment

| Component | Location | Zone / RG |
|-----------|----------|-----------|
| CMP-01, CMP-02, CMP-03 | dc-cn-primary | App Zone (Internal K8s) |
| CMP-05 VM | dc-cn-primary | App Zone |
| CMP-04 | dc-cn-primary | DB Zone |
| INF-05 | dc-cn-primary | App Zone |
| INF-07 | Azure (global) | cloud identity zone |
| CMP-06 | Azure East US | data RG, private subnet |
| CMP-07 | Azure East US2 (TBD) | model RG, PE Subnet |

**Data residency**: agent runtime, prompts metadata, and CMP-04 stay in
China. Only query payloads cross to Azure via CMP-05.

## 4. Integration Points

| # | From | To | Protocol | Port | Auth |
|---|------|----|----------|------|------|
| 1 | Office browser | CMP-01 | HTTPS | 443 | INF-07 redirect |
| 2 | CMP-01 | CMP-02 | HTTPS | 443 | User token forward |
| 3 | CMP-01 | CMP-03 | HTTPS | 443 | Internal service auth |
| 4 | CMP-02 | CMP-04 | TCP | 5432 | Password (K8s Secret) |
| 5 | CMP-03 | CMP-04 | TCP | 5432 | Password (K8s Secret) |
| 6 | CMP-02 | CMP-05 | HTTPS | 443 | Internal service auth |
| 7 | CMP-05 | CMP-06 | HTTPS | 443 | Service credential |
| 8 | CMP-05 | CMP-07 | HTTPS | 443 | API key (private endpoint) |
| 9 | CMP-01 | INF-05 | HTTPS | 443 | SAML 2.0 (fallback) |

## 5. Security Requirements

- **Single outbound path**: no K8s pod egress to the internet or Azure;
  everything hairpins via the CMP-05 VM.
- CMP-07 reachable only via private endpoint (no public IP).
- DB credentials and model API keys in K8s Secrets (encrypted at rest).
- TLS 1.2+ everywhere; SSE streams authenticated per-session.

## 6. Constraints

- Agent runtime must remain in `dc-cn-primary` (data sovereignty).
- Data access restricted to governed namespaces (row-level governance).
- Model pool selection (overseas vs China) is policy-driven per tenant.

## 7. Open Items

| ID | Item | Blocking |
|----|------|----------|
| TBD-01 | CMP-04 VIP / physical hosts | No |
| TBD-02 | Model RG region confirmation (East US2 TBD) | No |
| TBD-03 | CMP-07 China pool model list | No |
