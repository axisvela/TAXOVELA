# arch-req-readers

Multi-source requirements extraction toolkit for ArchHarness.

Extracts architecture requirements from five input types and merges them
into a single `req.yaml` that `arch-design` and `arch-requirements` consume.

## Quick start

```bash
cd tools/arch-req-readers

# Single source: existing draw.io file
python req_reader.py --diagram old-arch.drawio -o req.yaml

# Single source: architecture image
ANTHROPIC_API_KEY=... python req_reader.py --diagram screenshot.png -o req.yaml

# Multiple sources merged
ANTHROPIC_API_KEY=... python req_reader.py \
    --diagram old-arch.drawio \
    --doc requirements.pdf \
    --csv cmdb_export.csv \
    -o req.yaml --report gap-report.md
```

## Files

| File | Purpose |
|------|---------|
| `req_reader.py` | Main CLI orchestrator — combines all readers |
| `from_diagram.py` | draw.io / D2 / arch YAML / PNG via Vision |
| `from_document.py` | PDF / DOCX / MD / TXT via LLM extraction |
| `from_api.py` | ServiceNow CMDB / generic REST / CSV import |
| `merger.py` | Merge partial YAMLs, detect conflicts, gap report |
| `normalizer.py` | Shared data model (`PartialReq`, `FieldValue`, confidence) |

## Supported input types

| Input | Tool | Confidence | Notes |
|-------|------|-----------|-------|
| `.drawio` | `from_diagram.py` | HIGH topology, MEDIUM protocol | Best for existing Company arch diagrams |
| `.d2` | `from_diagram.py` | HIGH topology, MEDIUM protocol | D2 files from arch-diagram-gen |
| `.yaml` (arch:) | `from_diagram.py` | HIGH all fields | Direct field mapping |
| `.png/.jpg` | `from_diagram.py` + Vision API | MEDIUM components, LOW arrows | Requires `ANTHROPIC_API_KEY` |
| `.pdf` | `from_document.py` + LLM | MEDIUM | Requires `ANTHROPIC_API_KEY` + `pdfplumber` |
| `.docx` | `from_document.py` + LLM | MEDIUM | Requires `ANTHROPIC_API_KEY` + `python-docx` |
| `.md/.txt` | `from_document.py` + LLM | MEDIUM | Requires `ANTHROPIC_API_KEY` |
| ServiceNow | `from_api.py --profile servicenow` | HIGH location/owner | Set `SERVICENOW_*` env vars |
| Generic REST | `from_api.py --profile generic` | HIGH | Configure with `--config mapping.json` |
| CSV export | `from_api.py --csv file.csv` | HIGH | See README for column format |

## What each source covers

```
                        Location  Tech Stack  Protocols  Auth    User Auth
draw.io / D2              ✓✓        △           △         △        ✗
arch YAML                 ✓✓        ✓✓          ✓✓        ✓        △
PNG Vision                △         △           △         ✗        ✗
Documents                 △         △           △         ✗        △
CMDB API / CSV            ✓✓        ✗           ✗         ✗        ✗

✓✓ = HIGH confidence  △ = MEDIUM/partial  ✗ = Not available
```

Auth mechanisms are almost **never** in any external source — they must be
collected via the `arch-requirements` interview.

## Confidence model

Every extracted field carries:
```yaml
value: "Hohhot DC [CN]"
confidence: high      # high | medium | low | manual | unknown
source: "diagram:drawio:myarch.drawio"
note: ""              # "CONFLICT: ..." if two sources disagree
```

Merge priority: `manual > high > medium > low > unknown`

Conflicts (two HIGH+ sources disagree) are flagged but NOT auto-resolved.

## Environment variables

```bash
ANTHROPIC_API_KEY=...      # Required for: PNG vision, document LLM extraction

SERVICENOW_URL=https://company.service-now.com
SERVICENOW_USER=username
SERVICENOW_PASSWORD=password

CMDB_URL=https://your-cmdb.internal
CMDB_TOKEN=bearer-token-here
```

## CSV column format

```csv
name,app_id,dc_or_region,country,platform,zone,owner,infra_owner,language,framework,runtime,sensitivity
OrderMgmt,OMS-001,Hohhot DC,CN,private_dc,App Zone,SSG Team,InfraSec,Java-17,Spring Boot,Internal K8s,Company Confidential
```

Columns are case-insensitive with flexible aliases (e.g., `datacenter` = `dc_or_region`).

## Gap report example

After merging, `gap-report.md` shows:

```
## Critical gaps (3) — must resolve before arch-design
  - ❌ Interaction 'App A → PostgreSQL': auth_method is missing
  - ❌ Interaction 'BFF → WSO2': auth_method is missing
  - ❌ User authentication not defined for any entry point

## Conflicts (1) — same field, different values
  - ⚠ Application 'OMS': dc_or_region — CMDB says "Hohhot DC [CN]" vs diagram says "Neimeng DC [CN]"
```

Critical gaps block `arch-design`. Run `/arch-requirements` to fill them via interview.

## Install dependencies

```bash
pip install pyyaml pdfplumber python-docx
```
