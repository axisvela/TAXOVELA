# arch-diagram-gen

Converts an Architecture YAML file into a draw.io diagram (`.drawio`) and
optionally a PNG image. Follows the official Company architecture diagram template
style.

## Quick start

```bash
# Install (the D2 CLI renders the PNG image)
pip install pyyaml matplotlib
#   and install d2:  https://d2lang.com

# Generate .drawio (the editable source)
python arch_diagram_gen.py -i my_arch.yaml -o diagram.drawio

# Generate .drawio + .d2 + PNG (the image is rendered by D2)
python arch_diagram_gen.py -i my_arch.yaml -o diagram.drawio --d2 diagram.d2 --png diagram.png
```

draw.io is the **editable source**; the image is produced by **D2** (matplotlib
is the fallback when D2 is not installed). A draw.io render is available only
when asked for: `--png-engine drawio`.

## Output

### `.drawio` file
Full-fidelity draw.io XML. Open in:
- draw.io desktop app
- Confluence (draw.io plugin)
- app.diagrams.net

Shapes match the official Company template:
| Component | Shape |
|-----------|-------|
| F5 / Firewall / Load Balancer | Hexagon |
| API Gateway (WSO2/APIH/Nginx) | Parallelogram |
| Kafka / Message Bus | Rounded parallelogram |
| Database | Cylinder |
| IT Org app | Dashed rectangle |
| Biz Owned app | Purple filled rectangle |
| Third-Party app | Orange filled rectangle |
| Private DC | Double-border rectangle |
| Network Zone | Dashed double-border rectangle |
| AWS VPC/region | AWS cloud group shape |

### PNG file

The image is rendered by **D2** by default:

1. **D2 CLI** (default) — install [d2](https://d2lang.com) and ensure `d2` is on
   your PATH. The tool renders the `.d2` (compiling a temporary one if `--d2`
   was not given). For a very large diagram, add `--d2-scale 0.2`.

2. **matplotlib fallback** — pure Python, no external tools needed. Used when D2
   is unavailable. Renders distinct shapes, colored zones, directional arrows
   with protocol/auth labels, header, and legend.

3. **draw.io CLI** (opt-in) — `--png-engine drawio` renders through
   [draw.io desktop](https://github.com/jgraph/drawio-desktop/releases). Kept for
   compatibility; draw.io is otherwise the editable source, not the image renderer.

## YAML format

See `arch-schema-reference.yaml` for the complete field reference.

Minimal example:
```yaml
arch:
  id: "MyApp-TechDiagram-V1.0"
  name: "My Application"
  platform: "hybrid_cloud"
  deployment:
    - id: "hohhot-dc"
      type: "private_dc"
      location: "Hohhot DC, Inner Mongolia [CN]"
      owner: "InfraSec"
      network_zones:
        - id: "hohhot-dmz"
          type: "dmz"
          components:
            - id: "f5"
              name: "F5 Load Balancer"
              type: "LB"
        - id: "hohhot-app"
          type: "app_zone"
          components:
            - id: "my-svc"
              name: "My Service"
              type: "BE"
              language: "Java-17"
              framework: "Spring Boot"
              runtime: "Internal K8s"
  interactions:
    - from: "internet"
      to: "f5"
      protocol: "HTTPS"
      auth: "—"
    - from: "f5"
      to: "my-svc"
      protocol: "HTTPS/TLS 1.3"
      auth: "OAuth2.0"
```

## Platform types

| `type` value | Use for |
|-------------|---------|
| `private_dc` | Company private data centers (Hohhot, Shenyang, Reston, Frankfurt) |
| `aws_vpc` | AWS cloud regions |
| `azure_vnet` | Azure cloud regions |

## Network zone types

| `type` value | Background color | Typical use |
|-------------|-----------------|-------------|
| `dmz` | Yellow | Internet-facing layer, F5 gateway |
| `app_zone` | Green | Application tier |
| `db_zone` | Blue | Database tier |
| `intranet` | Purple | Combined app+DB (Shenyang style) |
| `hub` | Amber | AWS/Azure Hub VPC/VNET |
| `spoke` | Green | AWS/Azure Spoke VPC/VNET |

## Module structure

```
arch-diagram-gen/
├── arch_diagram_gen.py    CLI entry point
├── generator.py           draw.io XML builder
├── layout.py              Auto-sizing layout engine
├── styles.py              draw.io style strings (from official template)
├── png_renderer.py        matplotlib PNG renderer
└── arch-schema-reference.yaml  Full YAML field documentation
```

## Limitations

- Layout is auto-computed (2-column grid). Complex diagrams may need manual
  adjustment in draw.io after generation.
- PNG via matplotlib (the fallback): simplified shapes. Install the D2 CLI for
  the default, routed image; `--png-engine drawio` renders through draw.io desktop.
- Edges between cross-region components (not in `interactions:`) are not drawn.
  Always list all cross-DC interactions explicitly.

---

## D2 diagrams

D2 supports full 4-level nesting (DC → Zone → Component) and is version-control friendly.

```bash
# Generate .d2 file
python arch_diagram_gen.py -i arch.yaml --d2 diagram.d2

# Render to SVG (requires d2 CLI: https://d2lang.com/tour/install)
d2 --layout=elk diagram.d2 diagram.svg

# For deep nesting, elk layout is better than the default tala
```

D2 nesting syntax example (from generated output):
```d2
hohhot_dc: "Hohhot DC [CN]" {
  hohhot_dmz: "DMZ" {
    f5_hohhot: "F5 Load Balancer" {
      shape: hexagon
    }
  }
  hohhot_app_zone: "App Zone" {
    app_a: "Application A\n(Java-17, Spring Boot)" {
      style { stroke-dash: 5 }
    }
  }
}
hohhot_dc.hohhot_dmz.f5_hohhot -> hohhot_dc.hohhot_app_zone.app_a: "HTTPS/TLS 1.3\n(OAuth2.0)"
```

**Best use**: `git diff` on architecture changes, CI/CD validation.

---

## PlantUML Deployment Diagrams

PlantUML Deployment Diagram supports unlimited nested `node` blocks.

```bash
# Generate .puml file
python arch_diagram_gen.py -i arch.yaml --puml diagram.puml

# Render locally (requires plantuml CLI)
plantuml -tsvg diagram.puml

# Or paste into Confluence PlantUML macro
# Or import into draw.io: Extras → Edit Diagram → paste PlantUML
```

**Best use**: Confluence embedding (native PlantUML macro), draw.io import bridge.

---

## All formats at once

```bash
python arch_diagram_gen.py \
  -i arch.yaml \
  -o diagram.drawio \
  --png diagram.png \
  --d2 diagram.d2 \
  --puml diagram.puml
```

## Format comparison

| Format | Nesting | Shapes | CI/CD | Confluence | Edit GUI |
|--------|---------|--------|-------|------------|----------|
| draw.io | Full | All Company shapes | XML diff | Plugin needed | Best |
| D2 | Full (4-layer) | Approximated | Text diff | No native | No |
| PlantUML | Full | Approximated | Text diff | Native macro | No |
