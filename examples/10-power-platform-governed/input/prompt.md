# One-shot prompt — Expense Approval App (EXP) on Power Platform

> Codes-only prompt. Every system/service is referenced by a typed code
> (`INF-` infra · `APP-` systems · `CMP-` components · the `DEP`/`FLOW`/`LNK`/
> `AUTH` derived layers), resolved through `input/systems-registry.md` (include
> that registry as context when supplying this prompt to an agent). No literal
> system names appear outside the registry.

Design the technical architecture for a business-authored expense approval app
on Power Platform that submits to an on-premises expense backend.

Systems and infra in scope: APP-01 through APP-02; INF-01 through INF-10;
CMP-01 through CMP-06.

Requirements:

1. **Tenant boundary**: the Power Platform tenant (INF-01) is a SaaS boundary,
   not a customer network. Its environments are the working areas: a production
   environment (INF-02) and a governance area (INF-03). Do not draw DMZ, App
   Zone, or DB Zone inside the tenant.
2. **Environment governance**: production is a Managed Environment. A DLP policy
   (INF-05) classifies every connector as Business, Non-Business, or Blocked,
   and applies to the environment group.
3. **Identity**: Entra ID (INF-04) is the only identity source for both the
   business user (sign-in with MFA and conditional access) and the gateway's
   service account. Privileged roles use PIM.
4. **Components**: CMP-01 is the canvas app, CMP-02 the approval flow, CMP-03
   the Dataverse table holding approval state only, CMP-04 the on-premises data
   gateway, CMP-05 the company expense service, CMP-06 the expense database.
5. **Company-side path**: every call from the tenant lands on the gateway
   (CMP-04) in the DMZ (INF-07), behind the boundary firewall (INF-08). The
   gateway reaches the expense database (CMP-06) with a least-privilege service
   account and retrieves its secret from the enterprise vault (INF-10). No
   inbound database port is opened and no component holds a static secret.
6. **Integrations**: each flow names its protocol and authentication method;
   the firewall hop it traverses appears in `via`. Restated: flows are
   component-to-component, so user sign-in is declared in the auth table rather
   than as a flow.
7. **Data**: Acme Restricted data stays in the expense database; Dataverse holds
   approval state only. The database is AES-256 at rest, the vault holds its
   keys, and the tenant relay is TLS 1.2 minimum.
8. **Open items**: record what is still TBD with an owner.
