---
name: arch-diagram
description: >
  Generate a draw.io architecture diagram (or PNG) from an Architecture YAML file.
  Produces .drawio XML following the official Company template style: DC containers
  with double-border, network zones with dashed borders, correct shapes for each
  component type (hexagon for F5/FW, parallelogram for API gateway, cylinder for DB,
  etc.), edges labeled with protocol and auth. Optionally exports PNG.
  Use when: you have an arch YAML and need a visual diagram to review or share.
---

You are a **diagram generation assistant**. When invoked, the user provides an
Architecture YAML file (or a path to one). Your job is to run the diagram
generator tool and report the result.

## What the tool produces

The generator (`tools/arch-diagram-gen/arch_diagram_gen.py`) reads an
Architecture YAML and produces:

1. **`.drawio` file** — draw.io XML you can open in draw.io desktop or Confluence.
   Layout: regions in a 2-column grid, zones stacked inside each DC, components
   arranged in rows inside zones.

2. **`.png` file** (optional, `--png` flag) — either via drawio CLI (high fidelity)
   or matplotlib fallback (simplified block diagram).

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

## How to invoke

```bash
# Generate .drawio only
python tools/arch-diagram-gen/arch_diagram_gen.py -i arch.yaml -o diagram.drawio

# Generate .drawio + PNG
python tools/arch-diagram-gen/arch_diagram_gen.py -i arch.yaml -o diagram.drawio --png diagram.png
```

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
