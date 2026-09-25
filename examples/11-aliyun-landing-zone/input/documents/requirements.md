# Requirements Document — Order Service Platform on Alibaba Cloud
**Version**: 1.0  |  **Project ID**: ORD-ALI-001  |  **Classification**: Acme Confidential
**Scope**: New cloud workload with an existing on-premises ERP

> Resolve the typed codes (`INF-` / `APP-` / `CMP-` and the `DEP`/`FLOW`/`LNK`/`AUTH`
> derived layers) via `input/systems-registry.md` — include that file as LLM context.

---

## 1. Business context

The order service (APP-01) runs in a China region and publishes order status to
the on-premises ERP (APP-02), which remains the system of record for restricted
order data.

## 2. Scope

| Area | In scope | Out of scope |
|---|---|---|
| Alibaba Cloud land zone | INF-01 through INF-07, INF-10 through INF-17 | Billing and other business accounts |
| On-premises DC | INF-08, INF-09, CMP-05, CMP-06 | Other ERP modules |
| Application | CMP-01 through CMP-04 | Downstream reporting |

## 3. Deployment and network

| Component | Where | Runtime | Notes |
|---|---|---|---|
| CMP-01 Order service | INF-05 (application vSwitch, AZ-A) | ACK | 2 instances minimum |
| CMP-02 Order service (AZ-B) | INF-06 (application vSwitch, AZ-B) | ACK | Second availability zone |
| CMP-03 Order database | INF-07 (data vSwitch) | PolarDB/RDS | KMS-encrypted, private endpoint only |
| CMP-04 Object storage bucket | INF-07 | OSS | KMS-encrypted, private access only |
| CMP-05 ERP integration boundary | INF-09 (DC Intranet) | Internal K8s | Only boundary into the ERP zone |
| CMP-06 ERP core | INF-09 | Physical | Read by CMP-05 only |

- Two application vSwitches in different availability zones satisfy the
  availability requirement; a vSwitch is bound to one zone.
- Ingress: Anti-DDoS (INF-10) → WAF (INF-11) → SLB (INF-12). No workload holds
  an Elastic IP.
- Egress: NAT gateway (INF-14) only. Cross-VPC and hybrid traffic uses CEN
  (INF-15) with Express Connect.

## 4. Integrations

| Flow | Path | Protocol | Authentication | Encryption |
|---|---|---|---|---|
| Order service to database | CMP-01 → CMP-03 | JDBC 3306 | database account | TLS 1.3 |
| AZ-B to database | CMP-02 → CMP-03 | JDBC 3306 | database account | TLS 1.3 |
| Order service to archive | CMP-01 → CMP-04 | HTTPS 443 | RAM role (STS) | TLS 1.3 |
| Order status to ERP | CMP-01 → CMP-05 (via INF-13, INF-15) | HTTPS 443 | client certificate | IPSec |
| ERP read | CMP-05 → CMP-06 | JDBC 1433 | database account | TLS 1.2 |

LNK-01 attaches the business VPC to the hub through CEN; LNK-02 is the Express
Connect circuit to the DC.

## 5. Security

- **Identity**: internal users sign in through INF-18, federated to RAM SSO with
  MFA. Workloads assume RAM roles and receive STS tokens; long-lived AccessKeys
  are prohibited.
- **Secrets**: INF-17 holds database passwords with a rotation policy; the
  enterprise vault holds ERP credentials.
- **Data at rest**: KMS customer master keys for the order database and the
  archive bucket; AES-256 for the ERP.
- **Data in transit**: TLS 1.3 preferred; IPSec over Express Connect.
- **Segmentation**: the data vSwitch accepts connections from the application
  vSwitches only; the cloud firewall inspects east-west traffic.

## 6. Open items

| ID | Item | Owner | Blocking |
|---|---|---|---|
| TBD-001 | Confirm the resource-directory folder layout and account naming | Cloud Platform | Yes |
| TBD-002 | Confirm CEN bandwidth packages and the Express Connect circuit | Network team | Yes |
| TBD-003 | Confirm KMS key rotation and the OSS bucket policy | Security | No |
