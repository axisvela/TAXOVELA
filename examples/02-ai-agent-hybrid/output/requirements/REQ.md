# Requirements Document - Data Agent Platform (GDA)
**Version**: 1.0 Draft | **Date**: 2026-09-14 | **Author**: TBD
**Project ID**: DAP-001 | **Classification**: Acme Confidential
**Scope**: E2E hybrid solution. SYS-01 through SYS-05 are new and receive full-stack treatment; existing SYS-06 through SYS-10 are treated as black boxes at their integration boundaries.

## 1. Project Overview

The Data Agent Platform is an internal service through which tenant administrators and platform administrators ask governed data questions in natural language, receive streamed agent responses, and configure alerts and digests. The new application runtime remains in the primary private data center in China, while governed data and model services are consumed from Azure only through a controlled outbound gateway. The target go-live date and owning department are TBD.

## 2. Applications in Scope

| Stable ID | Document Name | Type | New/Existing | Owner | Scope |
|-----------|---------------|------|--------------|-------|-------|
| SYS-01 | gda-gateway | Web layer | New | TBD | Full stack; dashboard, static hosting, API proxy |
| SYS-02 | gda-agent-api | Backend | New | TBD | Full stack; agent API, SSE streaming, agent tools |
| SYS-03 | gda-scheduler-worker | Backend | New | TBD | Full stack; alerts and digests |
| SYS-04 | PostgreSQL | Database | New | TBD | Full stack; relational persistence |
| SYS-05 | Outbound gateway | Integration | New | TBD | Full stack; sole private-DC egress path to Azure |
| SYS-06 | ADFS | Identity | Existing | TBD | Integration boundary only; internal STS fallback |
| SYS-07 | Microsoft Entra ID | Identity | Existing cloud service | TBD | Integration boundary only; primary user identity provider |
| SYS-08 | EDW Databricks | Governed data source | Existing cloud service | TBD | Integration boundary only; governed namespaces |
| SYS-09 | LLM Gateway | AI platform | Existing cloud service | TBD | Integration boundary only; overseas and China model pools |
| SYS-10 | Internal K8s Platform | Container platform | Existing | TBD | Hosting boundary for SYS-01, SYS-02, and SYS-03 |

## 3. Physical Deployment

| App/Component | Country/Region | DC / Cloud Region | Zone/Subnet | Owner |
|---------------|----------------|-------------------|-------------|-------|
| SYS-01 gda-gateway | China | dc-cn-primary | App Zone on SYS-10 | TBD |
| SYS-02 gda-agent-api | China | dc-cn-primary | App Zone on SYS-10 | TBD |
| SYS-03 gda-scheduler-worker | China | dc-cn-primary | App Zone on SYS-10 | TBD |
| SYS-04 PostgreSQL | China | dc-cn-primary | DB Zone; VIP and physical hosts TBD | TBD |
| SYS-05 Outbound gateway | China | dc-cn-primary | App Zone; Rocky Linux 9.8 VM | TBD |
| SYS-06 ADFS | China | dc-cn-primary | App Zone | TBD |
| SYS-07 Microsoft Entra ID | Azure global service | Azure | Cloud identity zone; tenant data location TBD | Microsoft/TBD |
| SYS-08 EDW Databricks | United States | Azure East US (`azure-eastus`) | Data resource group, private subnet; exact resource group/subnet TBD | TBD |
| SYS-09 LLM Gateway | United States | Azure East US 2 (`azure-eastus2`), confirmation TBD | Model resource group, private endpoint subnet | TBD |
| SYS-10 Internal K8s Platform | China | dc-cn-primary | App Zone | TBD |

The agent runtime, prompt metadata, and SYS-04 data must remain in China. Only governed query payloads and model prompt/response traffic may cross to Azure over the controlled SYS-05 path. No IP addresses or CIDR ranges are specified; any future addressing remains TBD and must be maintained outside this requirements baseline.

## 4. Network Topology

| Connection | Type | Encryption | Notes |
|------------|------|------------|-------|
| Office network to dc-cn-primary App Zone | Internal enterprise network; exact path TBD | TLS 1.2+ | Office-network users only; inbound publishing/load-balancing path TBD |
| dc-cn-primary App Zone to DB Zone | Internal cross-zone connection | TLS 1.2+ required | SYS-02 and SYS-03 only, TCP 5432; firewall policy and PostgreSQL TLS mode TBD |
| dc-cn-primary to Azure East US | Private connectivity type TBD | TLS 1.2+ | All application traffic must traverse SYS-05; no direct pod internet or cloud egress |
| dc-cn-primary to Azure East US 2 | Private connectivity type TBD | TLS 1.2+ | SYS-09 is private-endpoint-only; private route/DNS implementation TBD |
| Browser authentication to SYS-07 | HTTPS over controlled enterprise egress; exact path TBD | TLS 1.2+ | Primary identity flow; protocol TBD |

## 5. Technical Components (New Only)

| Stable ID / Document Name | Type | Language | Framework | Runtime | Sensitivity |
|---------------------------|------|----------|-----------|---------|-------------|
| SYS-01 gda-gateway | Web frontend / API proxy | N/A (static assets/configuration) | nginx, version TBD | SYS-10 Internal K8s Platform | Acme Confidential |
| SYS-02 gda-agent-api | Backend API / agent runtime | Node.js, version TBD | Framework TBD | SYS-10 Internal K8s Platform | Acme Confidential |
| SYS-03 gda-scheduler-worker | Background worker | Node.js, version TBD | Framework TBD | SYS-10 Internal K8s Platform | Acme Confidential |
| SYS-04 PostgreSQL | Relational database | N/A | PostgreSQL, version TBD | DB Zone hosts/service model TBD | Acme Confidential |
| SYS-05 Outbound gateway | Controlled egress proxy | N/A (configuration) | nginx, version TBD | Rocky Linux 9.8 VM | Acme Confidential |

## 6. Integration Points

| # | From | To | Protocol | Port | Auth Method | Notes |
|---|------|----|----------|------|-------------|-------|
| INT-01 | Office browser | SYS-01 gda-gateway | HTTPS | 443 | SYS-07 Microsoft Entra ID redirect; exact protocol TBD | Tenant and platform administrators only; office network only |
| INT-02 | SYS-01 gda-gateway | SYS-02 gda-agent-api | HTTPS, including authenticated SSE response stream | 443 | Forwarded SYS-07 user token; token format/validation TBD | Cross-workload call inside App Zone |
| INT-03 | SYS-01 gda-gateway | SYS-03 gda-scheduler-worker | HTTPS | 443 | Internal service authentication mechanism TBD | Cross-workload call inside App Zone |
| INT-04 | SYS-02 gda-agent-api | SYS-04 PostgreSQL | PostgreSQL over TCP with TLS 1.2+ | 5432 | Database username/password from encrypted SYS-10 K8s Secret | App Zone to DB Zone |
| INT-05 | SYS-03 gda-scheduler-worker | SYS-04 PostgreSQL | PostgreSQL over TCP with TLS 1.2+ | 5432 | Database username/password from encrypted SYS-10 K8s Secret | App Zone to DB Zone |
| INT-06 | SYS-02 gda-agent-api | SYS-05 Outbound gateway | HTTPS | 443 | Internal service authentication mechanism TBD | Mandatory egress hop; direct pod cloud/internet egress prohibited |
| INT-07 | SYS-05 Outbound gateway | SYS-08 EDW Databricks | HTTPS | 443 | Service credential type and rotation TBD | Governed namespaces and row-level governance only |
| INT-08 | SYS-05 Outbound gateway | SYS-09 LLM Gateway | HTTPS via private endpoint | 443 | API key; delivery to SYS-05 and rotation TBD | Policy selects overseas or China model pool per tenant |
| INT-09 | SYS-01 gda-gateway | SYS-06 ADFS | HTTPS / SAML 2.0 | 443 | SAML 2.0 federation | Internal STS fallback |

Every design and diagram must label protocol, port, and authentication for each interaction. Items marked TBD are explicit requirements gaps and must not be replaced with assumed values.

## 7. User Authentication

| Entry Point | User Roles | Auth Server | Protocol | Authorization |
|-------------|------------|-------------|----------|---------------|
| SYS-01 gda-gateway (primary) | Tenant administrator; platform administrator | SYS-07 Microsoft Entra ID | TBD (redirect-based federated sign-in) | Mechanism/platform and role mapping TBD |
| SYS-01 gda-gateway (fallback) | Tenant administrator; platform administrator | SYS-06 ADFS | SAML 2.0 | Mechanism/platform and role mapping TBD |

Access is restricted to the office network. SSE sessions must be authenticated per session, and authorization must preserve tenant isolation. The fallback trigger and failover behavior between SYS-07 and SYS-06 are TBD.

## 8. Credential & Key Protection

| Environment | Solution | Notes |
|-------------|----------|-------|
| SYS-10 private-DC K8s | Kubernetes Secrets encrypted at rest | Stores SYS-04 database credentials and model API keys; encryption provider, RBAC, injection method, and rotation schedule TBD; hardcoded credentials prohibited |
| SYS-05 Rocky Linux VM | TBD enterprise secret delivery/store | The SYS-09 API key is used on the SYS-05 to SYS-09 boundary; secure delivery from the declared K8s secret source or an approved VM secret store is TBD |
| Azure | Provider-side secret/key controls are outside the integration boundary; client credential handling TBD | SYS-08 credential type and any Azure-side key-vault ownership are TBD |

## 9. Data Encryption

| Component / Flow | At Rest | In Transit | Cross-Border | Compliance |
|------------------|---------|------------|--------------|------------|
| SYS-04 PostgreSQL | TBD; approved encryption method required | TLS 1.2+ | No | China data-residency requirement; detailed standard TBD |
| SYS-10 K8s Secrets | Encrypted at rest; implementation TBD | TLS 1.2+ for credential-consuming calls | No | Acme Confidential controls; detailed standard TBD |
| SYS-02 through SYS-05 to SYS-08 | Source/target platform controls TBD | TLS 1.2+ | Yes, China to United States; governed query payloads only | Legal/compliance basis and payload minimization controls TBD |
| SYS-02 through SYS-05 to SYS-09 | Source/target platform controls TBD | TLS 1.2+ | Yes, China to United States; controlled prompt/response payloads | Legal/compliance basis, redaction, retention, and pool-selection controls TBD |

Prompt and response payloads must remain on the defined controlled paths. No application pod may bypass SYS-05, and SYS-09 must not expose a public endpoint.

## 10. Open Items / TBDs

| ID | Item | Owner | Target Date | Blocking Design |
|----|------|-------|-------------|-----------------|
| TBD-01 | Confirm SYS-04 VIP/service endpoint and physical hosting model without placing addresses in this document | TBD | TBD | No |
| TBD-02 | Confirm SYS-09 production region as Azure East US 2 and identify the model resource group | TBD | TBD | No |
| TBD-03 | Define the SYS-09 China-pool model list and tenant pool-selection policy details | TBD | TBD | No |
| TBD-04 | Identify the owning department, application owners, infrastructure owners, author, and go-live date | TBD | TBD | No |
| TBD-05 | Confirm SYS-07 sign-in protocol, token format, authorization mechanism/platform, role mapping, and fallback behavior | Security/IAM owner TBD | TBD | No |
| TBD-06 | Select the exact service-to-service authentication for INT-03 and INT-06 | Security owner TBD | TBD | No |
| TBD-07 | Select the SYS-08 service credential mechanism and rotation policy | Data platform owner TBD | TBD | No |
| TBD-08 | Confirm private connectivity, routing, private DNS, firewall, and proxy implementation between the DC and both Azure regions | Network owner TBD | TBD | No |
| TBD-09 | Confirm SYS-04 encryption at rest, PostgreSQL TLS enforcement, certificate trust, backup encryption, and recovery requirements | Database owner TBD | TBD | No |
| TBD-10 | Define secure SYS-09 API-key delivery to SYS-05, storage, access control, and rotation | Security owner TBD | TBD | No |
| TBD-11 | Approve the legal/compliance basis, minimization, redaction, logging, and retention controls for China-to-US query and model payloads | Compliance owner TBD | TBD | No |
| TBD-12 | Confirm product versions, Node.js frameworks, K8s release/deployment details, availability targets, capacity, monitoring, backup, RTO, and RPO | Platform owner TBD | TBD | No |
| TBD-13 | Confirm exact SYS-08 resource group/private subnet and SYS-07 tenant data location | Cloud owner TBD | TBD | No |
| TBD-14 | Confirm inbound publishing/load-balancing and firewall path from the office network to SYS-01 | Network owner TBD | TBD | No |

No critical requirements gap is identified from the supplied baseline: every component has a physical platform/location at the precision available, every external-facing connection has a named authentication authority or credential class, no hardcoded credential is permitted, and the declared China-resident data remains in China. The TBDs above are non-blocking design refinements and must remain visible in subsequent artifacts.

## 11. Architecture Constraints

- The architecture is hybrid across `dc-cn-primary`, Azure East US, and Azure East US 2; the new agent runtime remains in China.
- SYS-01, SYS-02, and SYS-03 run in the App Zone on SYS-10. SYS-04 runs in the DB Zone and is reachable only from the App Zone on TCP 5432.
- SYS-05 on a Rocky Linux 9.8 VM is the only private-DC path to Azure. Direct internet or cloud egress from SYS-10 pods is prohibited and must be denied by network policy and perimeter controls.
- SYS-09 is reachable only through an Azure private endpoint and must have no public exposure.
- All traffic uses TLS 1.2 or later. All diagram interactions show direction, protocol, port, and authentication.
- SYS-08 access is limited to governed namespaces with row-level governance.
- SYS-09 model-pool selection is policy-driven per tenant.
- Acme Confidential prompt/response and query payloads must use only controlled paths; logging and telemetry must not create uncontrolled copies.
- Database credentials and model API keys are secrets, must be encrypted at rest, must never be hardcoded, and require least-privilege access and rotation.
- No IP address or CIDR is part of this requirements baseline; unresolved addressing is TBD.
