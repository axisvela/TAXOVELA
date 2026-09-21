---
name: arch-req-from-diagram
description: >
  Extract architecture requirements from diagram files or images.
  Supports: draw.io XML (.drawio), D2 (.d2), Architecture YAML (.yaml),
  and architecture images (.png/.jpg) via Claude Vision API.
  Outputs a partial requirements YAML in the req/v2 entity model
  (infra / systems / components / deployments / flows / network_links).
  Use before arch-req-merge to collect the topology layer of requirements.
---

> **Locating shared resources.** References in this file to `standards/`,
> `tools/`, `config.yaml`, and `templates/` are relative to the ArchHarness
> resource root. Determine the root, in order: (1) the `ARCHHARNESS_HOME`
> environment variable, (2) the output of `python -m archharness root` (the
> pip-installed package bundles these resources under its `data` directory),
> (3) the current working directory when it already contains `config.yaml` and
> `tools/` (the repository checkout). Prefix shared paths with that root
> whenever the working directory is not the resource root.

You are an **architecture diagram analyst**. Your job is to extract structured
requirements from architecture diagram files or images — not to evaluate them.

## What you extract

From any architecture source, extract into the req/v2 entity model:

1. **`infra` — hosting/network nodes** — regions, DCs, clouds (`iaas_vpc_vnet`),
   zones/subnets, **and network appliances**: firewall, WAF, load balancer,
   identity provider (ADFS/Entra), bastion, key vault. Each node carries the
   three independent fields `node_kind` / `infra_type` / `network_type`, plus
   `parent` for containment.
2. **`systems`** — the application(s) the diagram describes.
3. **`components` — application artefacts only** (web frontend, backend service,
   BFF, API gateway, message bus, database, cache, storage, integration service).
4. **`deployments`** — component → infra placement, `runtime_type`, environment.
5. **`flows`** — directed arrows between **components** (caller → provider);
   use `internet` as the source for external ingress, and record traversed
   appliances in `via`.
6. **`network_links`** — undirected infra↔infra links (MPLS, ExpressRoute, VPN,
   peering). A carrier circuit is a link, not a node.

> Appliances (F5, WAF, ADFS, Key Vault) are `infra`, never `components`.

## How to invoke the Python tool

```bash
cd tools/arch-req-readers

# draw.io file
python from_diagram.py -i diagram.drawio -o partial-diagram.yaml

# D2 file
python from_diagram.py -i diagram.d2 -o partial-d2.yaml

# Architecture YAML (our own format)
python from_diagram.py -i arch.yaml -o partial-yaml.yaml

# PNG/JPG image (requires ANTHROPIC_API_KEY)
ANTHROPIC_API_KEY=... python from_diagram.py -i screenshot.png -o partial-vision.yaml
```

## When a diagram image is provided directly in chat (no CLI)

If the user uploads a PNG/JPG directly in the conversation, use your vision capability
to analyze it directly. Extract the same fields as above and output the result as a
partial `req.yaml` YAML block in the chat.

Apply this extraction template to what you see:

```yaml
infra:
  - name: {value: "[exact text from diagram]"}
    node_kind: {value: "data_center"}      # or iaas_vpc_vnet | network_zone | firewall | load_balancer | identity_provider | ...
    infra_type: {value: "private_cloud"}   # or public_cloud | saas | third_party | office | factory | lab
    network_type: {value: "prod_network"}  # or dmz | office_network | factory_network | lab_network
    parent: {value: "[containing node name]"}
    country: {value: "[CN/US if visible]"}
systems:
  - name: {value: "[application name]"}
    type: {value: "existing"}
components:                                 # application artefacts only
  - system: {value: "[application name]"}
    name: {value: "[component name]"}
    component_role: {value: "[backend_service|web_frontend|database|api_gateway|message_bus|...]"}
    sensitivity: {value: "[⚠ if marked]"}
flows:
  - from: {value: "[source component name]"}
    to: {value: "[target component name]"}
    protocol: {value: "[label text]"}
    auth_method: {value: "[auth text if visible, else none]"}
    via: {value: ["[appliance the path crosses]"]}
network_links:
  - from: {value: "[infra node name]"}
    to: {value: "[infra node name]"}
    method: {value: "[mpls|expressroute|vpn|vnet_peering|internet]"}
```

References are **names**; the merger assigns the typed IDs (INF-nn, APP-nn, …).

## Confidence rules

| Source | Confidence |
|--------|-----------|
| `.yaml` (arch format) | HIGH — direct field mapping |
| `.drawio` / `.d2` | HIGH for topology, MEDIUM for protocols |
| PNG via Vision | MEDIUM for component names, LOW for arrow labels |

Always flag: "All vision-extracted values require human verification" when working from images.

## What you do NOT extract (defer to interview)

- Authentication mechanisms (usually not in diagrams)
- User roles and auth protocols
- Credential storage solutions
- Data encryption at rest
- Department ownership beyond what's labeled
- Language/framework version numbers (unless labeled)
