---
name: arch-req-from-api
description: >
  Fetch application metadata from CMDB (ServiceNow, etc.) or Enterprise
  Architecture systems via REST API or CSV export.
  Provides high-confidence physical location and ownership data. Emits req/v2
  `systems` rows plus de-duplicated `infra` nodes, and additionally `components`
  / `stacks` / `deployments` when the CSV carries a technology stack.
  Does NOT provide protocols or auth — those must come from other readers or
  the interview. Use before arch-req-merge.
---

> **Locating shared resources.** References in this file to `standards/`,
> `tools/`, `config.yaml`, and `templates/` are relative to the ArchHarness
> resource root. Determine the root, in order: (1) the `ARCHHARNESS_HOME`
> environment variable, (2) the output of `python -m archharness root` (the
> pip-installed package bundles these resources under its `data` directory),
> (3) the current working directory when it already contains `config.yaml` and
> `tools/` (the repository checkout). Prefix shared paths with that root
> whenever the working directory is not the resource root.

You are an **integration specialist** connecting to CMDB and EA systems.
CMDB provides authoritative physical location and ownership data.
It does NOT contain tech stack, protocols, or authentication details.

## What CMDB/EA systems typically provide

| Field | Available in CMDB | Confidence |
|-------|------------------|------------|
| Application name | ✓ | High |
| Data center / location | ✓ | High |
| Application owner | ✓ | High |
| Department / BU | ✓ | High |
| Environment (prod/test) | ✓ | High |
| Technology category | Sometimes | Medium |
| Language/framework | Rarely | Low |
| Integration protocols | ✗ | N/A |
| Auth mechanisms | ✗ | N/A |

## ServiceNow CMDB

```bash
cd tools/arch-req-readers

# Set environment variables
export SERVICENOW_URL=https://your-company.service-now.com
export SERVICENOW_USER=your_username
export SERVICENOW_PASSWORD=your_password

# Fetch specific applications
python from_api.py --profile servicenow --app-id OMS-001 PORTAL-002 -o partial-cmdb.yaml

# Fetch all applications in CMDB
python from_api.py --profile servicenow -o partial-cmdb.yaml
```

## Generic REST API

```bash
# Custom field mapping via config file
python from_api.py --profile generic --config cmdb_config.json --app-id MY-APP -o partial.yaml
```

Config file format (`cmdb_config.json`):
```json
{
  "description": "Our internal EA system",
  "base_url_env": "EA_SYSTEM_URL",
  "auth_type": "bearer",
  "auth_env": ["EA_SYSTEM_TOKEN"],
  "endpoints": {
    "applications": "/api/v1/applications"
  },
  "field_map": {
    "app_name":   "displayName",
    "app_id":     "applicationId",
    "owner":      "businessOwner.email",
    "department": "businessUnit",
    "location":   "deploymentLocation",
    "platform":   "hostingType"
  },
  "query_params": {
    "status": "active"
  }
}
```

## CSV import (CMDB export)

Many CMDB systems allow CSV export. Supported columns:

```csv
name,app_id,dc_or_region,country,platform,zone,owner,infra_owner,language,framework,runtime
OrderMgmt,OMS-001,Hohhot DC,CN,private_dc,App Zone,SSG Team,InfraSec,Java,Spring Boot,Internal K8s
```

```bash
python from_api.py --csv cmdb_export.csv -o partial-csv.yaml
```

## When API is unavailable

If the user cannot connect to their CMDB, guide them to:
1. Export a CSV from CMDB manually
2. Use the CSV import option above
3. Or manually provide the application registry as a YAML list

Manual application registry format (req/v2 partial — references are names):
```yaml
systems:
  - name: {value: "Order Management System"}
    type: {value: "existing"}
    owner: {value: "org_it"}
infra:
  - name: {value: "Neimeng DC (Hohhot)"}
    node_kind: {value: "data_center"}
    infra_type: {value: "private_cloud"}
    network_type: {value: "prod_network"}
    parent: {value: "Neimeng DC (Hohhot)"}
    country: {value: "CN"}
    infra_owner: {value: "InfraSec"}
deployments:
  - component: {value: "Order Service"}
    environment: {value: "prod"}
    deployment_type: {value: "private_cloud"}
    location_type: {value: "data_center"}
    infra: {value: "Neimeng DC (Hohhot) / App Zone"}
    runtime_type: {value: "container"}
```

## Always note after API extraction

CMDB data is authoritative for location/ownership but DOES NOT replace the
requirements interview for: protocols, authentication, tech stack details,
data encryption, and user authentication.
