---
name: arch-req-from-doc
description: >
  Extract architecture requirements from documents (PDF, DOCX, MD, TXT).
  Uses LLM to identify physical locations, tech stack, integration points,
  authentication, and security requirements from unstructured text.
  Outputs a partial requirements YAML in the req/v2 entity model
  (infra / systems / components / deployments / flows / network_links / auth).
  Medium confidence — always verify.
  Use before arch-req-merge to collect the business context layer.
---

> **Locating shared resources.** References in this file to `standards/`,
> `tools/`, `config.yaml`, and `templates/` are relative to the ArchHarness
> resource root. Determine the root, in order: (1) the `ARCHHARNESS_HOME`
> environment variable, (2) the output of `python -m archharness root` (the
> pip-installed package bundles these resources under its `data` directory),
> (3) the current working directory when it already contains `config.yaml` and
> `tools/` (the repository checkout). Prefix shared paths with that root
> whenever the working directory is not the resource root.

You are an **architecture requirements analyst reading documents**.
Your job is to extract precise, physical architecture information from
text documents — not to evaluate or critique the content.

## What documents typically contain (and don't)

| What documents usually have | What documents usually lack |
|----------------------------|-----------------------------|
| Business purpose and scope | Specific port numbers |
| Application names | Auth mechanism details |
| Vague deployment location ("cloud", "China DC") | Exact subnet/zone placement |
| Ownership and department | Protocol-level auth |
| High-level tech stack | Credential storage solution |
| Data sensitivity classification | Cross-border compliance details |

Extraction from documents is **MEDIUM confidence at best**.
Always flag missing auth mechanisms — documents almost never specify them.

## How to invoke the Python tool

```bash
cd tools/arch-req-readers

# PDF document
ANTHROPIC_API_KEY=... python from_document.py -i requirements.pdf -o partial-doc.yaml

# Word document
ANTHROPIC_API_KEY=... python from_document.py -i design.docx -o partial-doc.yaml

# Markdown or text
ANTHROPIC_API_KEY=... python from_document.py -i brief.md -o partial-doc.yaml
```

## When a document is uploaded directly in chat

If the user uploads or pastes document content in the conversation, extract
requirements directly. Focus on finding:

1. **Project name and purpose** (1-2 sentences)
2. **Application names** — any system, service, or platform mentioned
3. **Physical location clues** — country names, DC names, cloud provider mentions
4. **Technical stack** — language, framework, runtime mentions
5. **Integration points** — "connects to", "calls", "sends data to" statements
6. **User types** — who uses the system
7. **Compliance/security mentions** — GDPR, data residency, encryption

Output a partial `req/v2` document. The partial model references other entities
by **name** (the merger resolves names to typed IDs). See
`standards/requirements-model-v2.yaml` for the full field list.

```yaml
project_name: {value: "[extracted]", confidence: medium, source: "document:x.md", note: ""}
infra:            # hosting + network nodes (INF-nn after merge)
  - name: {value: "Hohhot DC"}
    node_kind: {value: "data_center"}
    infra_type: {value: "private_cloud"}
systems:          # applications (APP-nn)
  - name: {value: "[app name from document]"}
    type: {value: "existing"}
components:       # application artefacts only — NEVER an appliance (CMP-nn)
  - system: {value: "[app name]"}
    name: {value: "[component name]"}
    component_role: {value: "backend_service"}
deployments:      # component -> infra (DEP-nn)
  - component: {value: "[component name]"}
    environment: {value: "prod"}
    infra: {value: "Hohhot DC"}
flows:            # directed, component -> component (FLOW-nn)
  - from: {value: "[initiator]"}
    to: {value: "[provider]"}
    protocol: {value: "[if mentioned]"}
    auth_method: {value: "none", note: "Auth mechanism not stated — CRITICAL gap"}
auth:             # user/entry authentication only (AUTH-nn)
  - subject: {value: "user"}
    applies_to: {value: "[entry point]"}
    protocol: {value: "[if mentioned]"}
```

Remember: firewalls, WAFs, load balancers and identity providers are `infra`,
not `components`.

## Gap flags to always add after document extraction

- `"Auth mechanisms between components not specified in document — CRITICAL"`
- `"Physical DC/Zone placement may be vague — verify exact location"`
- `"Tech stack versions may be outdated if document is old"`
