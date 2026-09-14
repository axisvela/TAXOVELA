"""Viewpoint registry and question-driven recommendation.

A viewpoint answers one stakeholder question with a defined projection of
the architecture model. Only viewpoints with renderer support can be
produced today; the rest are declared explicitly so requests fail with a
useful message instead of a silently wrong diagram.
"""

from __future__ import annotations

VIEWPOINTS = (
    {
        "id": "technical-deployment",
        "question": "Where is the system deployed and how is it connected?",
        "keywords": ("deploy", "infrastructure", "network", "topology", "server",
                      "database", "service", "vpc", "subnet", "zone", "datacenter"),
        "supported": True,
    },
    {
        "id": "application-cooperation",
        "question": "Which applications collaborate, and through which contracts?",
        "keywords": ("application", "collaborat", "dependenc", "integration",
                      "contract", "interface", "cooperat"),
        "supported": False,
    },
    {
        "id": "data-flow",
        "question": "Where does data originate, move, and persist?",
        "keywords": ("data flow", "lineage", "pipeline", "pii", "etl", "stream",
                      "where does data", "data move"),
        "supported": False,
    },
    {
        "id": "authentication-authorization",
        "question": "How are identities established and permissions enforced?",
        "keywords": ("auth", "login", "identity", "token", "permission", "role",
                      "sso", "oauth"),
        "supported": False,
    },
    {
        "id": "system-processing",
        "question": "How is one request processed across systems over time?",
        "keywords": ("sequence", "request flow", "timeline", "step by step",
                      "how is.*processed", "trace"),
        "supported": False,
    },
)

SUPPORTED_VIEWS = tuple(v["id"] for v in VIEWPOINTS if v["supported"])


def recommend(question: str) -> dict:
    """Recommend a viewpoint for a free-text question.

    Returns ``{"viewpoint": id, "supported": bool, "reason": str}``.
    Never raises on ordinary input; empty questions fall back to the
    default supported viewpoint.
    """
    import re

    text = (question or "").lower()
    best: dict | None = None
    best_hits = 0
    for viewpoint in VIEWPOINTS:
        hits = sum(1 for keyword in viewpoint["keywords"]
                   if re.search(keyword, text))
        if hits > best_hits:
            best, best_hits = viewpoint, hits
    if best is None:
        best = next(v for v in VIEWPOINTS if v["supported"])
        reason = "no specific signals; defaulting to the supported viewpoint"
    else:
        reason = f"matched {best_hits} signal(s): {best['question']}"
    return {"viewpoint": best["id"], "supported": best["supported"], "reason": reason}


def require_supported(view_id: str) -> None:
    """Raise ValueError unless ``view_id`` is a supported viewpoint."""
    known = {v["id"]: v for v in VIEWPOINTS}
    if view_id not in known:
        raise ValueError(
            f"unknown viewpoint {view_id!r} (known: {', '.join(known)})"
        )
    if not known[view_id]["supported"]:
        raise ValueError(
            f"viewpoint {view_id!r} is declared but has no renderer yet; "
            f"supported: {', '.join(SUPPORTED_VIEWS)}"
        )
