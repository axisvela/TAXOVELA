# Requirements Document — Analytics API on Google Cloud
**Version**: 1.0  |  **Project ID**: ANA-GCP-001  |  **Classification**: Acme Confidential
**Scope**: New hybrid application (textual names scrubbed; reference image unchanged)

> Resolve the typed codes (`INF-` / `APP-` / `CMP-` and the `DEP`/`FLOW`/`LNK`/`AUTH`
> derived layers) via `input/systems-registry.md` — include that file as LLM context.

---

## 1. Business context

The analytics API (APP-01) gives internal consumers a query interface over order
and shipment data that currently lives in the on-premises ERP (APP-02). The API
and its loader run on Google Cloud; the ERP stays on-premises and remains the
system of record.

## 2. Scope

| Area | In scope | Out of scope |
|---|---|---|
| Google Cloud landing zone | INF-01 through INF-05, INF-08 through INF-13 | Billing account design |
| On-premises DC | INF-06, INF-07, CMP-05, CMP-06 | Other DC workloads |
| Application | CMP-01 through CMP-04 | Consumer-side dashboards |

## 3. Deployment and network

| Component | Where | Runtime | Notes |
|---|---|---|---|
| CMP-01 Analytics API | INF-04 (private runtime subnet) | GKE private cluster | 2 instances minimum |
| CMP-02 Analytics worker | INF-04 | GKE private cluster | 2 instances |
| CMP-03 BigQuery warehouse | INF-05 (private data subnet) | Managed | CMEK, inside the VPC-SC perimeter |
| CMP-04 Cloud Storage stage | INF-05 | Managed | CMEK, private access only |
| CMP-05 ERP extract service | INF-07 (DC Intranet) | Internal K8s | Only boundary into the ERP zone |
| CMP-06 ERP core | INF-07 | Physical | Read by CMP-05 only |

- The Shared VPC host project (INF-01) owns every subnet; the service project
  attaches to it and owns no network.
- Ingress: Cloud Armor (INF-08) then the global HTTPS LB (INF-09). No workload
  holds an external IP.
- Egress: Cloud NAT (INF-10) only. Hybrid traffic uses Cloud Interconnect
  (INF-11) with IPSec.

## 4. Integrations

| Flow | Path | Protocol | Authentication | Encryption |
|---|---|---|---|---|
| Consumer query | internet → CMP-01 (via INF-08, INF-09) | HTTPS 443 | OAuth2 client credentials | TLS 1.3 |
| API to warehouse | CMP-01 → CMP-03 | gRPC 443 | IAM role | TLS 1.3 |
| Loader to staging | CMP-02 → CMP-04 | HTTPS 443 | IAM role | TLS 1.3 |
| ERP extract | CMP-02 → CMP-05 (via INF-11) | HTTPS 443 | Client certificate | IPSec |
| ERP read | CMP-05 → CMP-06 | JDBC 5432 | Database username/password | TLS 1.3 |

The ERP extract flow crosses the border: fields are minimized and classified
before transfer, and Privacy/Legal approval is required before production.

## 5. Security

- **Identity**: human sign-in goes through INF-13, federated to Cloud Identity,
  with MFA. Both internal employees (SAML 2.0) and partner consumers (OIDC
  authorization code with PKCE) use the same directory.
- **Secrets**: INF-12 issues runtime credentials; the enterprise vault holds ERP
  credentials. No static credential is stored in an image or a manifest.
- **Data at rest**: CMEK for BigQuery and Cloud Storage; AES-256 for the ERP.
- **Data in transit**: TLS 1.3 preferred; mTLS for the ERP boundary; IPSec over
  Interconnect.
- **Segmentation**: data services accept connections from the runtime subnet
  only; the ERP schema is readable by CMP-05 only.

## 6. Open items

| ID | Item | Owner | Blocking |
|---|---|---|---|
| TBD-001 | Confirm the GCP region and Cloud Interconnect capacity | Network team | Yes |
| TBD-002 | Confirm BigQuery retention and the CMEK rotation period | Data Platform | No |
| TBD-003 | Privacy and Legal approval for the ERP extract scope | Privacy/Legal | Yes |
