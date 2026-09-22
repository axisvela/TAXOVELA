"""
labels.py — Shared label normalisation for every diagram renderer.

Keeps labels short and consistent across the draw.io, PNG, D2 and PlantUML
generators:

* Every ``[STATUS: …]`` annotation is dropped from the label text — the status
  is carried by the **edge colour** instead: EXISTING = blue, NEW / CHANGE =
  red, REMOVE = grey, TBD / unspecified = blue-grey.
* Edge labels carry only **codes**: protocols as ``P-*``, authentication as
  ``AU-*`` (``UserPassword`` → ``AU-P1``). The legend maps codes back to methods.
* Component technology stacks are lower-cased and compressed to
  ``name: version`` pairs (``Java (version TBD)`` → ``java``); runtimes are
  abbreviated (``Internal K8s Platform`` → ``K8s``).

The code taxonomy itself lives in ``standards/diagram-codes.yaml`` so every
example, tool and reviewer uses one vocabulary. A compact table is kept inline as
a fallback for when the resource root is unavailable.
"""

from __future__ import annotations

import re

# ── Edge status → colour ──────────────────────────────────────────────────────

STATUS_COLORS = {
    "EXISTING": "#1565C0",   # blue
    "NEW":      "#C62828",   # red
    "CHANGE":   "#C62828",   # red
    "CHANGED":  "#C62828",
    "REMOVE":   "#9E9E9E",   # grey
    "REMOVED":  "#9E9E9E",
    "RETIRED":  "#9E9E9E",
    "TBD":      "#78909C",   # blue-grey
}
DEFAULT_EDGE_COLOR = "#78909C"   # blue-grey: status unspecified

_STATUS_RE = re.compile(r"\[\s*status\s*:\s*([^\]]+?)\s*\]", re.IGNORECASE)
_WS_RE = re.compile(r"[ \t]{2,}")


def _normalise_status(raw: str) -> str:
    return re.sub(r"[\s\-]+", "_", str(raw).strip().upper())


def parse_status(interaction: dict) -> str | None:
    """Return the normalised status token for an interaction, or None."""
    explicit = interaction.get("status")
    if explicit:
        return _normalise_status(explicit)
    match = _STATUS_RE.search(str(interaction.get("protocol", "")))
    return _normalise_status(match.group(1)) if match else None


def status_color(status: str | None) -> str:
    """Edge colour for a status token; blue-grey when unspecified/TBD."""
    if not status:
        return DEFAULT_EDGE_COLOR
    return STATUS_COLORS.get(status, DEFAULT_EDGE_COLOR)


# ── Component lifecycle status ────────────────────────────────────────────────
# The status is carried by the box colour; the text marker is never printed.

COMPONENT_STATUSES = {
    "NEW":      "newly_created",
    "CHANGED":  "changed",
    "EXISTING": "unchanged",
    "REMOVE":   "removed",
}

STATUS_FILL = {
    "NEW":      {"fill": "#D32F2F", "stroke": "#D32F2F", "text": "#FFFFFF"},
    "CHANGED":  {"fill": "#FBC02D", "stroke": "#B58A00", "text": "#000000"},
    "EXISTING": {"fill": "#FFFFFF", "stroke": "#000000", "text": "#000000"},
    "REMOVE":   {"fill": "#757575", "stroke": "#616161", "text": "#FFFFFF"},
}
STATUS_FILL_DEFAULT = STATUS_FILL["EXISTING"]
OWNERSHIP_FILL = {
    "biz_owned": {"fill": "#8E24AA", "stroke": "#6A1B9A", "text": "#FFFFFF"},
    "third_party": {"fill": "#FB8C00", "stroke": "#E65100", "text": "#000000"},
}

# Trailing markers like "CMP-28 | Kafka (NA) | NEW" are redundant with `status:`.
_STATUS_SUFFIX_RE = re.compile(
    r"\s*\|?\s*(NEW|CHANGED|CHANGE|EXISTING|UNCHANGED|REMOVE|REMOVED|RETIRED)\s*$",
    re.IGNORECASE)

_STATUS_ALIASES = {
    "NEWLY_CREATED": "NEW", "NEW": "NEW", "ADDED": "NEW", "PLANNED": "NEW",
    "CHANGED": "CHANGED", "CHANGE": "CHANGED", "MODIFIED": "CHANGED", "UPDATED": "CHANGED",
    "UNCHANGED": "EXISTING", "EXISTING": "EXISTING", "ACTIVE": "EXISTING",
    "REMOVED": "REMOVE", "REMOVE": "REMOVE", "RETIRED": "REMOVE", "DELETED": "REMOVE",
}


def component_status(comp: dict) -> str | None:
    """Lifecycle status of a component: NEW / CHANGED / EXISTING / REMOVE / None."""
    declared = comp.get("status")
    if declared:
        key = re.sub(r"[\s\-]+", "_", str(declared).strip().upper())
        if key in _STATUS_ALIASES:
            return _STATUS_ALIASES[key]
    match = _STATUS_SUFFIX_RE.search(str(comp.get("name", "")))
    if match:
        return _STATUS_ALIASES.get(match.group(1).upper().replace(" ", "_"))
    return None


def component_fill(comp: dict) -> dict:
    """Fill/stroke/text colour, with standard ownership colour precedence."""
    owner = comp.get("owner") or comp.get("owner_type")
    if owner in OWNERSHIP_FILL:
        return OWNERSHIP_FILL[owner]
    return STATUS_FILL.get(component_status(comp), STATUS_FILL_DEFAULT)


def component_name(comp: dict) -> str:
    """Component name with any trailing lifecycle marker removed."""
    return _STATUS_SUFFIX_RE.sub("", str(comp.get("name", comp.get("id", "")))).strip()


# ── Diagram header metadata ───────────────────────────────────────────────────
# standards/diagram-style.yaml §6 requires title, id, author, owner team,
# version, and last modified. Only the fields the model actually supplies are
# printed, so a partly filled design never shows an empty label.

_HEADER_DETAIL_FIELDS = (
    ("version", "Version"),
    ("owner_team", "Owner team"),
    ("author", "Author"),
    ("last_modified", "Last modified"),
)


def header_fields(arch: dict) -> list[tuple[str, str]]:
    """Return ``(label, value)`` header pairs in the standard's order."""
    meta = arch.get("arch", arch) if isinstance(arch, dict) else {}
    if not isinstance(meta, dict):
        meta = {}
    fields = [("Name", str(meta.get("name") or "Architecture"))]
    for key, label in (("id", "ID"), ("platform", "Platform")) + _HEADER_DETAIL_FIELDS:
        value = meta.get(key)
        if value:
            fields.append((label, str(value)))
    return fields


# ── Code taxonomy (standards/diagram-codes.yaml) ──────────────────────────────

# Compact fallback used only when the standard file cannot be read.
_FALLBACK_PROTOCOLS: list[tuple[str, str, str]] = [
    (r"https", "P-HTTPS", "HTTPS"),
    (r"\bhttp\b", "P-HTTP", "HTTP"),
    (r"kafka|sasl_ssl", "P-KAFKA", "Kafka"),
    (r"amqp|rabbitmq", "P-AMQP", "AMQP / RabbitMQ"),
    (r"jdbc", "P-JDBC", "JDBC"),
    (r"odbc", "P-ODBC", "ODBC"),
    (r"\bidoc\b", "P-IDOC", "SAP IDOC"),
    (r"\brfc\b", "P-RFC", "SAP RFC"),
    (r"grpc", "P-gRPC", "gRPC"),
    (r"sftp", "P-SFTP", "SFTP"),
    (r"\btcp\b", "P-TCP", "TCP"),
]
_FALLBACK_AUTH: list[tuple[str, str, str, str]] = [
    (r"oauth\s*2(?:\.0)?\s*client\s*credentials|oauth2[_\s]*client", "T1", "Token / federation", "OAuth2 client credentials"),
    (r"\bsaml\b", "T3", "Token / federation", "SAML 2.0 assertion"),
    (r"\bmtls\b|client[_\s]*certificate", "C1", "Certificate / key", "mTLS / client certificate"),
    (r"sasl\s*/?\s*scram|sasl[_\s]*scram", "S1", "SASL", "SASL/SCRAM"),
    (r"kerberos|logon\s*ticket", "K1", "Kerberos / OS", "Kerberos / logon ticket"),
    (r"service[_\s]*account|sap\s*technical\s*user", "P4", "Password / credential", "Service account / secret"),
    (r"user\s*/\s*password|userpassword", "P1", "Password / credential", "User ID / password"),
    (r"\bbasic\b", "P2", "Password / credential", "HTTP Basic auth"),
    (r"api[_\s]*key", "P3", "Password / credential", "API key"),
    (r"iam[_\s]*role", "I1", "Cloud identity", "IAM role"),
    (r"managed[_\s]*identity", "I2", "Cloud identity", "Managed identity"),
    (r"internal\s+access\s+authentication", "X1", "Other", "Internal access authentication"),
    (r"service\s+auth", "X2", "Other", "Service auth (unspecified)"),
    (r"topic\s*acl|least[-\s]*privilege|\bacl\b", "Z1", "Authorization", "Topic ACL / least privilege"),
]


def _load_code_table() -> dict:
    try:
        import yaml
        from ..paths import require_archharness_root
        path = require_archharness_root() / "standards" / "diagram-codes.yaml"
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}


def _build_protocols(table: dict) -> list[tuple[str, str, str]]:
    codes: list[tuple[str, str, str]] = []
    classes = (table.get("protocol") or {}).get("classes") or {}
    for entries in classes.values():
        for entry in entries or []:
            codes.append((entry["pattern"], entry["code"], entry.get("description", "")))
    return codes


def _build_auth(table: dict) -> list[tuple[str, str, str, str]]:
    codes: list[tuple[str, str, str, str]] = []
    for group in (table.get("auth") or {}).get("classes") or []:
        major = group.get("major", "Other")
        for entry in group.get("codes") or []:
            codes.append((entry["pattern"], entry["code"], major,
                          entry.get("description", "")))
    return codes


_CODE_TABLE = _load_code_table()
PROTOCOL_CODES = _build_protocols(_CODE_TABLE) or _FALLBACK_PROTOCOLS
AUTH_TAXONOMY = _build_auth(_CODE_TABLE) or _FALLBACK_AUTH
PROTOCOL_PREFIX = (_CODE_TABLE.get("protocol") or {}).get("prefix", "P-")
AUTH_PREFIX = (_CODE_TABLE.get("auth") or {}).get("prefix", "AU-")
AUTH_NONE_CODE = (_CODE_TABLE.get("auth") or {}).get("none_code", "N0")

PROTOCOL_DESCRIPTIONS = {code: desc for _, code, desc in PROTOCOL_CODES}
AUTH_CODE_DESCRIPTIONS = {code: desc for _, code, _, desc in AUTH_TAXONOMY}
AUTH_CODE_MAJORS = {code: major for _, code, major, _ in AUTH_TAXONOMY}
AUTH_CODE_DESCRIPTIONS[AUTH_NONE_CODE] = "No service authentication"
AUTH_CODE_MAJORS[AUTH_NONE_CODE] = "None"

_VIA_RE = re.compile(r"\bvia\s+([A-Za-z]{2,5}-\d{1,4})", re.IGNORECASE)


# ── Protocol codes ────────────────────────────────────────────────────────────

def protocol_codes(text) -> list[str]:
    """Return the ordered protocol codes found in a protocol string."""
    raw = str(text or "").strip()
    if not raw:
        return []
    codes: list[str] = []
    for pattern, code, _desc in PROTOCOL_CODES:
        if re.search(pattern, raw, re.IGNORECASE) and code not in codes:
            codes.append(code)
    if not codes:
        token = re.split(r"[\s/+,;()]+", raw)[0]
        if token:
            codes.append(f"{PROTOCOL_PREFIX}{token.upper()}")
    return codes


def protocol_code(text) -> str:
    """Protocol string → code string, e.g. ``HTTPS/TLS 1.3`` → ``P-HTTPS``."""
    return "+".join(protocol_codes(text))


def protocol_legend(interactions: list[dict]) -> list[str]:
    """Legend lines for the protocol codes actually used, first-seen order."""
    order: list[str] = []
    for interaction in interactions or []:
        for code in protocol_codes(interaction.get("protocol", "")):
            if code not in order:
                order.append(code)
    return [f"{code} {PROTOCOL_DESCRIPTIONS.get(code, '')}".rstrip() for code in order]


# ── Authentication codes ──────────────────────────────────────────────────────

def auth_codes(text) -> list[str]:
    """Return the ordered auth codes (minor) for an auth string."""
    raw = str(text or "").strip()
    if not raw or raw in {"—", "-"}:
        return [AUTH_NONE_CODE]
    codes: list[str] = []
    for pattern, code, _major, _desc in AUTH_TAXONOMY:
        if re.search(pattern, raw, re.IGNORECASE) and code not in codes:
            codes.append(code)
    return codes or [AUTH_NONE_CODE]


def auth_code(text) -> str:
    """Auth string → AU-prefixed code, e.g. ``UserPassword`` → ``AU-P1``.

    A combination is written with a single prefix: ``mTLS + SASL/SCRAM`` →
    ``AU-C1+S1``.
    """
    return f"{AUTH_PREFIX}{'+'.join(auth_codes(text))}"


def auth_via(text) -> str | None:
    """Return the ``via <id>`` reference if the auth string carries one."""
    match = _VIA_RE.search(str(text or ""))
    return match.group(1).upper() if match else None


def auth_legend(interactions: list[dict]) -> list[str]:
    """Legend lines for the auth codes actually used, in first-seen order."""
    order: list[str] = []
    vias: dict[str, list[str]] = {}
    for interaction in interactions or []:
        text = interaction.get("auth", "")
        codes = auth_codes(text)
        for code in codes:
            if code not in order:
                order.append(code)
        via = auth_via(text)
        if via:
            for code in codes:
                vias.setdefault(code, [])
                if via not in vias[code]:
                    vias[code].append(via)
    lines = []
    for code in order:
        major = AUTH_CODE_MAJORS.get(code, "Other")
        desc = AUTH_CODE_DESCRIPTIONS.get(code, code)
        suffix = f" via {', '.join(vias[code])}" if vias.get(code) else ""
        lines.append(f"{code} [{major}] {desc}{suffix}")
    return lines


# ── Edge label text ───────────────────────────────────────────────────────────

def clean_protocol(text: str) -> str:
    """Drop ``[STATUS: …]`` markers and tidy separators."""
    if not text:
        return ""

    def _sub(match: re.Match) -> str:
        return ""   # status is carried by the edge colour, not the label text

    text = _STATUS_RE.sub(_sub, str(text))
    text = re.sub(r"\s*/\s*$", "", text.strip())
    return _WS_RE.sub(" ", text).strip()


def edge_label(interaction: dict) -> str:
    """Visible edge label: protocol code on line 1, AU auth code on line 2."""
    protocol = protocol_code(interaction.get("protocol", ""))
    codes = auth_codes(interaction.get("auth", ""))
    auth = auth_code(interaction.get("auth", "")) if codes != [AUTH_NONE_CODE] else ""
    if protocol and auth:
        return f"{protocol}\n({auth})"
    if auth:
        return f"({auth})"
    return protocol


# ── Component technology stack ────────────────────────────────────────────────

_PAREN_RE = re.compile(r"\(([^)]*)\)")
_TRAILING_VERSION_RE = re.compile(r"\s+(\d+(?:\.\d+)*[\w.\-]*)$")
_PLACEHOLDER = {"tbd", "unknown", "n/a", "na", "-", "", "none"}

_RUNTIME_RULES: list[tuple[str, str]] = [
    (r"k8s|kubernetes|aks|eks|gke|openshift", "K8s"),
    (r"container|docker|\bpod\b", "CTR"),
    (r"serverless|lambda|function|faas", "Svrls"),
    (r"physical|bare\s*metal|appliance|hardware", "PM"),
    (r"\bvm\b|virtual\s*machine|instance|ec2", "VM"),
    (r"infrastructure|network", "HW"),
]


def clean_tech(raw) -> str:
    """Lower-case a technology token; keep ``name: version``, drop TBD versions."""
    if not raw:
        return ""
    text = str(raw)
    version = None

    def _grab(match: re.Match) -> str:
        nonlocal version
        inner = match.group(1).strip()
        if re.search(r"version", inner, re.IGNORECASE):
            candidate = re.sub(r"\b(version|mechanism)\b", "", inner,
                               flags=re.IGNORECASE).strip(" :/,-")
            if candidate.lower() not in _PLACEHOLDER:
                version = candidate
            return ""
        return match.group(0)

    text = _PAREN_RE.sub(_grab, text)
    text = re.sub(r"\bTBD\b", "", text, flags=re.IGNORECASE)

    if version is None:
        trailing = _TRAILING_VERSION_RE.search(text)
        if trailing:
            version = trailing.group(1)
            text = text[:trailing.start()]

    text = " ".join(text.split()).strip(" ,-/").lower()
    if text and version:
        return f"{text}: {version}"
    return text


def runtime_short(raw) -> str:
    """Abbreviate a runtime string (``Internal K8s Platform`` → ``K8s``)."""
    if not raw:
        return ""
    text = str(raw)
    lowered = text.lower()
    for pattern, short in _RUNTIME_RULES:
        if re.search(pattern, lowered):
            return short
    return " ".join(text.split())


def tech_line(comp: dict) -> str:
    """One-line technology summary: ``java, spring · K8s`` (may be empty)."""
    parts: list[str] = []
    for key in ("language", "framework"):
        token = clean_tech(comp.get(key))
        if token and token not in parts:
            parts.append(token)
    line = ", ".join(parts)
    runtime = runtime_short(comp.get("runtime"))
    if runtime:
        return f"{line} · {runtime}" if line else runtime
    return line
