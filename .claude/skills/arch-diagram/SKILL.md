---
name: arch-diagram
description: >
  Generate a draw.io architecture diagram (or PNG) from an Architecture YAML file.
  Produces .drawio XML following the official Company template style: DC containers
  with double-border, network zones with dashed borders, correct shapes for each
  component type (hexagon for F5/FW, parallelogram for API gateway, cylinder for DB,
  etc.), edges labeled with shared protocol/auth codes (P-* / AU-*), and a code
  legend. Optionally exports PNG.
  Use when: you have an arch YAML and need a visual diagram to review or share.
---

> **Locating shared resources.** References in this file to `standards/`,
> `tools/`, `config.yaml`, and `templates/` are relative to the ArchHarness
> resource root. Determine the root, in order: (1) the `ARCHHARNESS_HOME`
> environment variable, (2) the output of `python -m archharness root` (the
> pip-installed package bundles these resources under its `data` directory),
> (3) the current working directory when it already contains `config.yaml` and
> `tools/` (the repository checkout). Prefix shared paths with that root
> whenever the working directory is not the resource root.

You are a **diagram generation assistant**. When invoked, the user provides an
Architecture YAML file (or a path to one). Your job is to run the diagram
generator and report the result. Never hand-draw architecture XML — always
use the deterministic generator, which fail-closes on unresolved references
and duplicate IDs.

## What the tool produces

The generator (`archharness diagram`) reads an Architecture YAML and produces:

1. **`.drawio` file** — draw.io XML you can open in draw.io desktop or Confluence.
   Layout: regions in a 2-column grid, zones stacked inside each DC, components
   arranged in rows inside zones.

2. **`.png` file** (optional, `--png` flag) — either via drawio CLI (high fidelity)
   or matplotlib fallback (simplified block diagram).

3. **`.d2` / `.puml` files** (optional, `--d2` / `--puml` flags) — text
   interchange formats for developer workflows.

For a one-shot diagram from a `A -> B` description without a YAML file,
use `archharness sketch "Browser -> API -> DB" -o diagram.drawio` instead.

## Shape mapping (matches Company template)

| YAML type/shape | draw.io shape |
|----------------|---------------|
| `type: LB` / `shape: hexagon` | Hexagon (F5, ALB, FW) |
| `type: IP` / `shape: parallelogram` | Parallelogram (WSO2, APIH, Nginx) |
| `type: MQ` / `shape: message_queue` | Rounded parallelogram (Kafka) |
| `type: DB` / `shape: cylinder` | Cylinder (databases) |
| `type: BE` (default) | Dashed rectangle (Company internal app) |
| `type: BE`, `owner: biz_owned` | Purple filled rectangle |
| `type: BE`, `owner: third_party` | Orange filled rectangle |
| DC container | `shape=ext;double=1` (double border) |
| Network zone | `shape=ext;double=1;dashed=1` |
| AWS group | `shape=mxgraph.aws4.group` with cloud icon |
| Internet | `shape=mxgraph.aws4.internet` |

Sensitivity markers:
- Components with `Company Confidential` or `Company Restricted` get a ⚠ prefix on their label.

## Edge labels — shared code vocabulary

Edge labels are **codes**, not prose. The vocabulary lives in
`standards/diagram-codes.yaml` and is shared by every example, renderer and
reviewer, so the same relation always renders the same code.

| Kind | Form | Examples |
|---|---|---|
| Protocol | `P-<code>` | `P-HTTPS`, `P-KAFKA`, `P-JDBC`, `P-RFC`, `P-IDOC`, `P-OPCUA`, `P-MQTT` |
| Authentication | `AU-<minor>` | `AU-T1`, `AU-C1`, `AU-P4`, `AU-S1`, `AU-K1`, `AU-N0` |

A combination joins with `+` and the prefix is written once: `mTLS + SASL/SCRAM`
→ `AU-C1+S1`. Codes are collected in taxonomy order, so the result is stable
regardless of how the source text is phrased.

**Authentication classes** (supplement as needed in `standards/diagram-codes.yaml`):

| Class | Codes | Meaning |
|---|---|---|
| Token / federation | `T1`–`T6` | OAuth2 client credentials · OAuth2/OIDC user login · SAML2 · session token · JWT/bearer · personal access token |
| Certificate / key | `C1` `C2` | mTLS / client certificate · SSH public key |
| SASL | `S1`–`S4` | SCRAM · PLAIN · GSSAPI · OAUTHBEARER |
| Kerberos / OS | `K1` `K2` | Kerberos / logon ticket · NTLM / Windows integrated |
| Password / credential | `P1`–`P6` | user ID/password · HTTP Basic · API key · service account/secret · LDAP bind · RADIUS/TACACS+ |
| Cloud identity | `I1`–`I3` | IAM role · managed identity · service principal / workload identity |
| User factor | `M1` `M2` | MFA/OTP · FIDO2 / WebAuthn / passkey |
| Other | `X1`–`X4` | internal access auth · service auth (unspecified) · IP allowlist · anonymous |
| Authorization | `Z1`–`Z4` | topic ACL / least privilege · RBAC · ABAC/policy engine · OAuth2 scope |
| None | `N0` | no service authentication |

Each diagram renders a legend listing only the codes it actually uses.

**Edge colour = interface status** (the `[STATUS: …]` marker is never printed):

| Status | Colour |
|---|---|
| `EXISTING` | blue `#1565C0` |
| `NEW`, `CHANGE` | red `#C62828` |
| `REMOVE` | grey `#9E9E9E` |
| `TBD` / unspecified | blue-grey `#78909C` |

**Zone-boundary firewalls.** In a private cloud a firewall is a container-class
infra node on the network-zone boundary: all in/out traffic passes it implicitly,
so components are **not** connected to it individually — the zone is marked
`· FW` and flows are declared directly between the components that talk
(rule R-INF-4 in `standards/requirements-model-v2.yaml`). In a public cloud a
firewall may sit in its own subnet and is then drawn as an explicit node.

**Logical groups.** Sibling components in the same zone that are interchangeable
— same technology signature *and* identical edge signatures (same peers, same
protocols, same direction) — are folded into one dashed box, and their fan-out
edges collapse to one edge per peer. This is automatic; a component with even
one extra relation stays standalone. Set `group: "<name>"` on components to force
a named grouping (and to keep a human-readable box title) instead of the derived
`<type> group ×N`. The renderers use the same pass, so `.drawio` and `.png` agree.

**Font hierarchy.** Component labels use `fontSize=14`, edge labels `fontSize=9`.
Component technology stacks are lower-cased and compressed (`Java (version TBD)`
→ `java`, `Internal K8s Platform` → `K8s`).

## How to invoke

```bash
# Generate .drawio only
archharness diagram -i arch.yaml -o diagram.drawio

# Generate .drawio + PNG
archharness diagram -i arch.yaml -o diagram.drawio --png diagram.png

# One-shot sketch without a YAML file
archharness sketch "Browser -> API -> DB" -o diagram.drawio
```

(The legacy path `python tools/arch-diagram-gen/arch_diagram_gen.py`
still works via a compatibility shim; prefer the CLI above.)

## Requirements

```
pip install pyyaml          # required
pip install matplotlib      # optional, for PNG fallback
```

For high-fidelity PNG, install draw.io desktop and ensure `drawio` is on PATH.

## When asked to generate a diagram

1. Check if the user has provided a YAML file path or YAML content.
2. If YAML content is provided inline, write it to a temp file first.
3. Run the tool and report what was generated.
4. If the output .drawio path is in the project, confirm it's ready to open.
5. If PNG was requested but drawio CLI is unavailable, note that matplotlib
   fallback was used and recommend installing draw.io desktop for full fidelity.
