# One-shot prompt — Analytics API (ANA) on Google Cloud

> Codes-only prompt. Every system/service is referenced by a typed code
> (`INF-` infra · `APP-` systems · `CMP-` components · the `DEP`/`FLOW`/`LNK`/
> `AUTH` derived layers), resolved through `input/systems-registry.md` (include
> that registry as context when supplying this prompt to an agent). No literal
> system names appear outside the registry.

Design the technical architecture for an internal analytics API that runs on
Google Cloud and reads extracts from the on-premises ERP.

Systems and infra in scope: APP-01 through APP-02; INF-01 through INF-13;
CMP-01 through CMP-06.

Requirements:

1. **Location and zones**: one Google Cloud Shared VPC host project (INF-01)
   owns the network; workloads run in its shared subnets (INF-02 ingress,
   INF-03 egress, INF-04 runtime, INF-05 data). The service project owns no
   network of its own. The on-premises DC (INF-06) keeps its own zone (INF-07).
2. **Ingress**: all external traffic enters through Cloud Armor (INF-08) and the
   global HTTPS load balancer (INF-09); no workload holds an external IP.
3. **Egress**: outbound traffic leaves through Cloud NAT (INF-10); the private
   path to the DC is Cloud Interconnect (INF-11).
4. **Components**: CMP-01 serves analytics queries, CMP-02 loads ERP extracts,
   CMP-03 is the BigQuery warehouse, CMP-04 stages extracts, CMP-05 is the only
   boundary into the ERP zone, CMP-06 is the ERP system of record.
5. **Integrations**: every flow names its protocol and authentication method;
   the WAF, load balancer, and gateway hops it traverses are listed in `via`.
   ERP extracts cross the border and must be minimized and classified.
6. **Identity**: internal users and partner consumers sign in through the
   enterprise directory (INF-13), federated to Cloud Identity.
7. **Secrets and data**: runtime credentials come from Secret Manager (INF-12);
   BigQuery and Cloud Storage use CMEK; ERP credentials come from the enterprise
   vault. No component holds a static credential.
8. **Open items**: record what is still TBD with an owner.
