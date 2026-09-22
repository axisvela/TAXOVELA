# Example 1 — E-commerce Platform (Azure Multi-Region Hub-Spoke)

Reverse-engineered from a real e-commerce network architecture diagram.
Demonstrates the **Azure Hub-Spoke standard** across two regions plus hybrid
connectivity to on-prem DCs.

> **Name policy:** `input/systems-registry.md` is the only file that contains literal entity names. Every other file — `input/prompt.md`, `input/documents/requirements.md`, `README.md`, `config.yaml` — references `SYS-nn` codes only. The original reference diagram is intentionally not scrubbed and is restricted input.

## Scenario

An e-commerce platform runs on Azure in **EastUS** (primary)
and **JapanEast** (AP), each region following the hub-spoke pattern:

- **EastUS**
  - Hub SYS-01 — firewall instance SYS-06, hybrid gateway SYS-07
  - Spoke SYS-02 — SYS-10 / DMZ / SYS-11 / SYS-12 / SYS-13,
    all egress forced through SYS-06 via UDR
  - Spoke SYS-03 — SYS-15, SYS-14, SYS-16
  - Full-mesh VNet peering between hub and spokes
- **JapanEast** — same pattern: hub SYS-04 (SYS-08 + SYS-09) +
  spoke SYS-05 (SYS-17 / DMZ / SYS-18 / SYS-19)
- **Hybrid** — SYS-22 + SYS-23 for SYS-01 to SYS-20 with SYS-24
  and SYS-25 as backup; SYS-26 for SYS-04 to SYS-21

## What it demonstrates

| Pipeline stage | Highlight |
|---|---|
| arch-validate | azure-standard Hub-Spoke checks, forced-tunnel UDR to firewall, peering completeness |
| accuracy-rules | Subnet segments per VNet, DC locations, dedicated-circuit redundancy |
| arch-design | Reproducing hub-spoke + hybrid from a requirements doc |

## Inputs

- ★ `input/systems-registry.md` — code-to-name registry (single source of truth)
- `input/prompt.md` — human-maintained readable one-shot prompt (Path A)
- `input/documents/requirements.md` — structured requirements (Path B)
- `input/diagrams/reference-architecture.png` — original reference diagram
  (intentionally not scrubbed; restricted input)
  *(place the provided image here)*

## Run

```bash
cd examples/01-ecommerce-azure
archharness req --from-doc input/documents/requirements.md
# → arch-design → arch-diagram → arch-validate ...
```

## Name policy

| Category | Handling |
|---|---|
| Human-readable names | Maintain and manually scrub in `input/prompt.md`, then update registry `文档用名` |
| Reference diagram | Preserve the original image without scrubbing; treat it as restricted input |
| Addresses | Omitted from prompts and documentation |
