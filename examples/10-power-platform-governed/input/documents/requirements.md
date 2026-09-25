# Requirements Document — Expense Approval App on Power Platform
**Version**: 1.0  |  **Project ID**: PPGOV-001  |  **Classification**: Acme Confidential
**Scope**: New business-authored app with an existing on-premises backend

> Resolve the typed codes (`INF-` / `APP-` / `CMP-` and the `DEP`/`FLOW`/`LNK`/`AUTH`
> derived layers) via `input/systems-registry.md` — include that file as LLM context.

---

## 1. Business context

The finance team wants a lightweight expense approval app they can maintain
themselves (APP-01). The expense records stay in the existing company backend
(APP-02); the app only holds approval state.

## 2. Scope

| Area | In scope | Out of scope |
|---|---|---|
| Power Platform tenant | INF-01 through INF-05, CMP-01 through CMP-03 | Other environments and apps in the tenant |
| Company backend | INF-06 through INF-10, CMP-04 through CMP-06 | The expense service's own consumers |
| Data | Approval state and expense records | Reporting and archiving |

## 3. Deployment and network

| Component | Where | Runtime | Notes |
|---|---|---|---|
| CMP-01 Expense approval app | INF-02 (production environment) | Managed environment | Canvas app, standard connectors only |
| CMP-02 Approval flow | INF-02 | Managed environment | Calls the company backend through the gateway |
| CMP-03 Dataverse table | INF-02 | Managed environment | Approval state only |
| CMP-04 On-premises data gateway | INF-07 (DMZ) | Hardened VM, 2 hosts | Sole inbound path; outbound-only relay |
| CMP-05 Expense service | INF-09 (App Zone) | Internal K8s | Not in the gateway's direct path |
| CMP-06 Expense database | INF-09 | Physical | Reached by the gateway's service account only |

- The tenant (INF-01) is a SaaS boundary: its environments are working areas, not
  network zones. No customer network segmentation is drawn inside it.
- The DMZ (INF-07) terminates all inbound traffic at the boundary firewall
  (INF-08); the gateway is the only permitted destination.

## 4. Integrations

| Flow | Path | Protocol | Authentication | Encryption |
|---|---|---|---|---|
| App to flow | CMP-01 → CMP-02 | HTTPS 443 | user context | TLS 1.3 |
| Flow to Dataverse | CMP-02 → CMP-03 | HTTPS 443 | OAuth2 client credentials | TLS 1.3 |
| Flow to gateway | CMP-02 → CMP-04 | HTTPS 443 | service account | TLS 1.2 |
| Gateway to database | CMP-04 → CMP-06 (via INF-08) | JDBC 1433 | service account | TLS 1.2 |
| User sign-in | declared in the auth table | HTTPS 443 | OIDC | TLS 1.3 |
| Gateway secret access | declared on CMP-04 `key_management` | HTTPS 443 | client certificate | TLS 1.3 |

The tenant relay (LNK-01) is outbound-only from the tenant's perspective: no
inbound listener is exposed and no private circuit exists.

## 5. Security

- **Identity**: Entra ID (INF-04) with MFA and conditional access for users;
  certificate credentials for the app registrations. Privileged roles via PIM.
  No platform-local accounts.
- **Governance**: the DLP policy (INF-05) classifies connectors by environment
  group; a business-authored flow cannot reach a blocked connector.
- **Secrets**: the enterprise vault (INF-10) holds and rotates the gateway
  service account secret. No secret appears in an app or flow definition.
- **Data at rest**: Dataverse is Microsoft-managed; the expense database is
  AES-256 with vault-held keys.
- **Data classification**: Acme Restricted data stays in the expense database.
  Dataverse holds approval state only.

## 6. Open items

| ID | Item | Owner | Blocking |
|---|---|---|---|
| TBD-001 | Confirm the environment group and DLP policy export | Business Platform | Yes |
| TBD-002 | Confirm the gateway host hardening baseline and service account scope | InfraSec | Yes |
| TBD-003 | Confirm retention and sensitivity labels for Dataverse tables | Data Platform | No |
