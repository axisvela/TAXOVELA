# Requirements Document — Data Agent Platform
**Version**: 1.0  |  **Project ID**: DAP-001  |  **Classification**: Acme Confidential
**Scope**: New hybrid application (textual names scrubbed; reference image unchanged)

> Resolve SYS-nn codes via `input/systems-registry.md` — include that file as LLM context.

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
| SYS-01 (web entry + dashboard UI) | Web layer | New | Full stack |
| SYS-02 (Node.js, SSE streaming, agent tools) | Backend | New | Full stack |
| SYS-03 (Node.js, alerts and digests) | Backend | New | Full stack |
| SYS-04 (relational database) | Database | New | Full |
| SYS-05 (nginx egress proxy, Rocky 9.8 VM) | Integration | New | Full |
| SYS-06 | Identity | Existing | Integration boundary only |
| SYS-07 | Identity | Existing (cloud) | Integration boundary only |
| SYS-08 (governed namespaces) | Data source | Existing (cloud) | Integration boundary only |
| SYS-09 (overseas / China pools) | AI platform | Existing (cloud) | Integration boundary only |

## 3. Physical Deployment

| Component | Location | Zone / RG |
|-----------|----------|-----------|
| SYS-01, SYS-02, SYS-03 | dc-cn-primary | App Zone (SYS-10) |
| SYS-05 VM | dc-cn-primary | App Zone |
| SYS-04 | dc-cn-primary | DB Zone |
| SYS-06 | dc-cn-primary | App Zone |
| SYS-07 | Azure (global) | cloud identity zone |
| SYS-08 | Azure East US | data RG, private subnet |
| SYS-09 | Azure East US2 (TBD) | model RG, PE Subnet |

**Data residency**: agent runtime, prompts metadata, and SYS-04 stay in
China. Only query payloads cross to Azure via SYS-05.

## 4. Integration Points

| # | From | To | Protocol | Port | Auth |
|---|------|----|----------|------|------|
| 1 | Office browser | SYS-01 | HTTPS | 443 | SYS-07 redirect |
| 2 | SYS-01 | SYS-02 | HTTPS | 443 | User token forward |
| 3 | SYS-01 | SYS-03 | HTTPS | 443 | Internal service auth |
| 4 | SYS-02 | SYS-04 | TCP | 5432 | Password (K8s Secret) |
| 5 | SYS-03 | SYS-04 | TCP | 5432 | Password (K8s Secret) |
| 6 | SYS-02 | SYS-05 | HTTPS | 443 | Internal service auth |
| 7 | SYS-05 | SYS-08 | HTTPS | 443 | Service credential |
| 8 | SYS-05 | SYS-09 | HTTPS | 443 | API key (private endpoint) |
| 9 | SYS-01 | SYS-06 | HTTPS | 443 | SAML 2.0 (fallback) |

## 5. Security Requirements

- **Single outbound path**: no K8s pod egress to the internet or Azure;
  everything hairpins via the SYS-05 VM.
- SYS-09 reachable only via private endpoint (no public IP).
- DB credentials and model API keys in K8s Secrets (encrypted at rest).
- TLS 1.2+ everywhere; SSE streams authenticated per-session.

## 6. Constraints

- Agent runtime must remain in `dc-cn-primary` (data sovereignty).
- Data access restricted to governed namespaces (row-level governance).
- Model pool selection (overseas vs China) is policy-driven per tenant.

## 7. Open Items

| ID | Item | Blocking |
|----|------|----------|
| TBD-01 | SYS-04 VIP / physical hosts | No |
| TBD-02 | Model RG region confirmation (East US2 TBD) | No |
| TBD-03 | SYS-09 China pool model list | No |
