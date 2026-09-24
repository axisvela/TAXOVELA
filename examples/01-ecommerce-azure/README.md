# Example 1 - E-commerce Platform (Azure Multi-Region Hub-Spoke)

Req/v2 migration of a two-region Azure hub-spoke deployment with hybrid corporate integration.

## Model

`input/systems-registry.md` is the only literal-name registry. Other documents use typed identifiers: INF-01 through INF-21, APP-01 through APP-04, CMP-01 through CMP-11, DEP-01 through DEP-11, FLOW-01 through FLOW-11, LNK-01 through LNK-08, and AUTH-01.

Network and security appliances are INF nodes. Kubernetes is runtime detail on DEP rows. Dedicated circuits, MPLS, VPN, and peering are LNK rows. Existing corporate systems are APP black boxes with CMP integration boundaries.

## Artifacts

- `diagram.drawio` / `diagram.png` and validation artifacts are frozen v1 history.
- `diagram-v2.drawio`, `diagram-v2.d2`, `diagram-v2.png`, and its preview are regenerated from the typed blueprint.

## Verify

```bash
python ../../tools/registry_check.py .
python -m archharness req-validate output/requirements/req.yaml
python -m archharness trace-check -r output/requirements/req.yaml -b output/designs/blueprint.yaml
```
