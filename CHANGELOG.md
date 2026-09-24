# Changelog

Notable changes to ArchHarness, newest first. A release is tagged `v<version>`
matching `archharness/__init__.py`; `.github/workflows/release.yml` refuses to
publish when the tag and the package version disagree.

See [Compatibility](#compatibility) for the interfaces that consumers pin.

## Unreleased

### Added

- `req/v2` requirements model with one table per entity kind (`INF-`, `APP-`,
  `CMP-`, `DEP-`, `FLOW-`, `LNK-`, `AUTH-`, `STK-`), cross-field validation,
  and a worked reference in example 06.
- Registry checker rules for prompt coverage, `OUT-OF-SCOPE` rows, and literal
  entity names leaking into documents.
- Deterministic draw.io edge router: endpoint ports, Manhattan waypoints,
  region/zone gutters, lane separation for parallel and reverse edges, and a
  bounded visibility-graph detour, with automatic-routing fallback.
- `archharness diagram --routing-diagnostics` writes per-edge strategy, lane,
  waypoint count, timing, and fallback flags as JSON.
- `archharness workflow verify` reports structured artifact findings, and the
  `can` / `status` / `complete` gates re-verify recorded SHA-256 digests before
  a stage may advance.
- `archharness migrate-status` reports each example's req/v2 migration state
  (`scaffold` / `reqv1` / `reqv2-partial` / `reqv2-complete`) and fails when a
  migrated example no longer passes its registry or requirements checks. The
  example matrix in `examples/README.md` is verified against it.
- `archharness trace-check -r req.yaml -b blueprint.yaml` verifies req/v2
  inventory references in a typed blueprint, including the documented CN/NA
  site suffix for components deployed at more than one site.
- `archharness arch-check` runs deterministic rules on an architecture YAML
  with stable rule ids and evidence (`A-01` duplicate id, `A-02` undeclared
  endpoint, `A-03`/`A-04` missing protocol or authentication label, `A-05`
  self-reference, `A-06` unknown lifecycle status), with `--json` output and a
  fail-closed exit code.
- Standard component shapes (pentagon, card, stored_data, double ellipse,
  diamond, document, note, step, pyramid, cube, cloud) render in draw.io, PNG,
  and D2, and load balancers are trapezoids distinct from firewall hexagons.
- `docs/ROADMAP.md` records the repository priorities.

### Changed

- Example 01 is migrated to req/v2. Its registry separates Azure topology and
  security appliances (`INF`), black-box systems (`APP`), workload artifacts
  (`CMP`), runtime deployments, component flows, and carrier/peering links;
  Kubernetes remains deployment runtime detail. A versioned v2 draw.io/D2/PNG
  view is added while historic validation and enforcement stay bound to v1.
- Component colours, zone palettes, shapes, and router controls come from
  `standards/diagram-style.yaml` instead of renderer-local constants;
  ownership colours take precedence over lifecycle colours.
- Draw.io cell IDs are stable per diagram, so regenerating the same YAML
  produces byte-identical XML.
- Examples 01–05 and 07–08 ship with the repository; example 04 carries role
  names for carriers and vendors and the platform acronym is `SDP`.
- Example 05 joins example 06 as a fully migrated reference: its blueprint nodes
  carry the req/v2 typed codes, with `CMP-nn-CN` / `CMP-nn-NA` for a component
  deployed in both sites, and its v2 diagram is rendered from that blueprint.
- Examples 02 and 04 are migrated too. Example 04's registry now holds 208 rows
  across the seven tables, its appliances (router, F5, ADFS, external IdP) are
  infra nodes rather than components, and flows carry the contracted appliance
  hops in `via`.
- Example 03 is migrated to req/v2: its seven-table registry separates AWS and
  DC topology, security appliances, systems, components, deployments, flows,
  links, and entry authentication. The v2 diagram is versioned separately so
  historic validation and enforcement remain bound to the original diagram.

- `archharness validate-check` joins a `validation/v1` result back to the model:
  a finding that cites a typed code the model does not declare is an error
  (the unverifiable / false-positive path), an unanchored finding or one still
  citing the retired `SYS-nn` space is a warning. Every shipped example passes
  the error rule; four validation records still cite the retired id space and
  are flagged for re-validation.
- Gate policy profiles: `standards/arch-gate-policy.yaml` can declare named
  profiles over the baseline (`production`, `poc`) and `archharness enforce
  --profile <name>` selects one. The decision records which profile gated the
  artifact. A profile may tighten the baseline freely; a looser one must
  declare `allow_looser: true` with a rationale, so a gate cannot be relaxed
  silently.

### Fixed

- Reading an architecture YAML back into requirements now also derives the
  deployment layer (one row per component, with its zone resolved as the infra
  node), the WAN/peering links that connect containers, and one authentication
  declaration per identity provider, anchored to the ingress component rather
  than to the network appliance in front of it. It also disambiguates labels
  the merger keys by name, so repeated zones ("Intranet", "DB Zone") and shared
  partner locations no longer displace one another or lose their parent DC.
- Two identity providers serving one entry point (an internal STS and an
  external IdP) are recorded as two declarations instead of being reconciled
  into one, and an identity server that cannot be resolved is reported rather
  than written into the model as a bare name.
- Reading an architecture YAML back into requirements works again: the reader
  emitted flow endpoints as diagram ids while the model references entities by
  name, so the merge dropped every flow of a complete model. Key-store labels
  outside the contract enum (`partner_keys`) are now recorded as `other` and
  reported as a gap instead of failing the merge, and the merge no longer
  leaks its internal `_source` provenance key into `req/v2` credentials.
- The plugin contract kit is skipped rather than failed when a subclass does
  not set `plugin`, so `unittest` and `pytest` agree.
- `sensitivity: null` no longer breaks draw.io generation.
- Interactions between containers (Azure VNet peering, DC-to-DC WAN links)
  render again: the draw.io router resolves region and zone endpoints and
  fails closed on an endpoint with no rendered geometry, and D2 records
  container paths. `tests/test_example_artifacts.py` now regenerates every
  shipped example so this cannot regress silently.
- The standard's `in_plan` lifecycle status renders its defined green instead
  of falling back to the unspecified colour.
- Example workflow records no longer embed machine-specific absolute paths or a
  truncated SHA-256 digest.

## v0.7.0 — 2026-09-14

- Apply semantic change sets to models with a dry-run review.
- Cache-test matrix with wheel smoke, version consistency, and mirror gates.

## v0.6.0 — 2026-09-14

- Semantic change sets with verifiable apply.

## v0.5.0 — 2026-09-14

- Viewpoint recommendation and atomic artifact delivery.
- One-shot `A -> B` sketch rendered into a typed model and diagram.

## v0.4.0 — 2026-09-14

- `req/v1` and `artifact/v1` contracts with manifest primitives.
- Plugin discovery, capabilities, and contract kit.
- Stable application API with argv and exit-code contracts.
- Executable workflow state machine, `validation/v1` results, and the
  deterministic `enforcement/v1` gate.

## v0.3.5 — 2026-09-13

- `doctor` tolerates a missing default project.

## v0.3.4 — 2026-09-13

- Milestone 0 stabilization: installed-package detection, wheel smoke test,
  hardened req temp handling, strict YAML checks.

## v0.3.3 — 2026-09-09

- Automated PyPI release and mirror drift checks in CI.

## v0.3.2 — 2026-09-09

- Claude Code plugin marketplace and PyPI packaging metadata.

## v0.3.1 — 2026-09-09

- Resource-root guidance, workflow spec, and the pipeline gatekeeper skill.
- Self-contained runtime data shipped in the wheel.

## v0.3.0 — 2026-09-09

- Multi-project workspace CLI, cross-tool distribution, CI, and repo checks.
- Codex skill mirror, Copilot agents, and root `standards/` + `tools/` layout.

## 0.1 / 0.2 — 2026-04-02 / 2026-05-30

- Initial repository and benchmark harness. These predate the `v` tag scheme.

## Compatibility

| Interface | Version | Notes |
|---|---|---|
| `req/v1` | stable | Still accepted by the readers and validator. |
| `req/v2` | new | Entity-separated model; examples migrate individually. |
| `artifact/v1` | stable | The document shape is unchanged, but digests are now re-verified when a workflow gate runs: an artifact edited after it was recorded blocks the stage until it is re-recorded. |
| `validation/v1`, `enforcement/v1` | stable | Unchanged shapes; `workflow verify` can surface stale bindings. |
| `standards/diagram-style.yaml` | v2.0 | Gained a `routing` block (`gutter`, `lane_gap`, `max_visibility_nodes`). Renderers fall back to built-in defaults when a key is absent. |
| `standards/workflow.yaml` | stable | Stage order and `requires` unchanged. |
| Plugin API (`PLUGIN_API_VERSION`) | stable | Discovery and capability contract unchanged. |
| Diagram XML | changed | Cell IDs are now stable sequential ids instead of random GUIDs. Regenerating an older diagram produces a one-off ID diff, then repeated runs are byte-identical. |
