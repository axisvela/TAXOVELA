"""
from_api.py — Fetch application metadata from CMDB / Enterprise Architecture systems.

Supports:
  - Generic REST API (configurable field mapping)
  - ServiceNow CMDB (built-in field mapping)
  - CSV export from any system

A CMDB app row maps to the req/v2 entity model as:
  - one `systems` row (the application)
  - one `infra` row (its physical location), de-duplicated by name
  - CSV exports that also carry a tech stack additionally yield `components`,
    `stacks` and `deployments`.

The CMDB does NOT provide protocols or auth mechanisms — those gaps must be
filled by other readers or the interview.

Usage:
    python from_api.py --profile servicenow --app-id APP001 -o partial-req.yaml
    python from_api.py --profile custom --config cmdb_config.json --app-id OMS -o partial-req.yaml
    python from_api.py --csv apps_export.csv -o partial-req.yaml
"""

import argparse
import csv
import json
import os
import urllib.request
import urllib.parse
from pathlib import Path

from .normalizer import (
    PartialReq, PartialSystem, PartialInfra, PartialComponent, PartialStack,
    PartialDeployment, Confidence, fv, partial_req_to_yaml,
)


# ── Built-in CMDB profiles ────────────────────────────────────────────────────

PROFILES = {
    "servicenow": {
        "description": "ServiceNow CMDB (cmdb_ci_appl table)",
        "base_url_env": "SERVICENOW_URL",
        "auth_type": "basic",
        "auth_env": ("SERVICENOW_USER", "SERVICENOW_PASSWORD"),
        "endpoints": {
            "applications": "/api/now/table/cmdb_ci_appl",
            "servers": "/api/now/table/cmdb_ci_server",
        },
        "field_map": {
            "app_name":     "name",
            "app_id":       "correlation_id",
            "owner":        "owned_by.display_value",
            "department":   "assignment_group.display_value",
            "location":     "location.display_value",
            "environment":  "environment",
            "tech_stack":   "sys_class_name",
        },
        "query_params": {
            "sysparm_fields": "name,correlation_id,owned_by,assignment_group,location,environment",
            "sysparm_display_value": "true",
            "sysparm_limit": "50",
        }
    },
    "generic": {
        "description": "Generic REST API (configure with --config)",
        "base_url_env": "CMDB_URL",
        "auth_type": "bearer",
        "auth_env": ("CMDB_TOKEN",),
        "endpoints": {
            "applications": "/api/applications",
        },
        "field_map": {
            "app_name":   "name",
            "app_id":     "id",
            "owner":      "owner",
            "department": "department",
            "location":   "datacenter",
            "platform":   "platform",
            "country":    "country",
        },
        "query_params": {}
    }
}

# Known DC name normalizations
DC_NORMALIZATIONS = {
    "neimeng": "Neimeng DC (Hohhot)",
    "hohhot": "Neimeng DC (Hohhot)",
    "shenyang": "Shenyang DC",
    "sy": "Shenyang DC",
    "reston": "Reston DC",
    "frankfurt": "Frankfurt DC",
    "aws-us-east": "AWS US East (N. Virginia)",
    "aws-us-east-1": "AWS US East (N. Virginia)",
    "azure-east-asia": "Azure East Asia",
    "azure-china-north": "Azure China North 2",
}

COUNTRY_FROM_DC = {
    "Neimeng DC": "CN",
    "Shenyang DC": "CN",
    "Reston DC": "US",
    "Frankfurt DC": "DE",
    "AWS US East": "US",
    "Azure East Asia": "SG",
    "Azure China North": "CN",
}


def _normalize_dc(raw: str) -> tuple[str, str]:
    """Return (normalized_dc_name, country_code)."""
    raw_lower = raw.lower().replace(" ", "-").replace("_", "-")
    for key, normalized in DC_NORMALIZATIONS.items():
        if key in raw_lower:
            country = next((v for k, v in COUNTRY_FROM_DC.items()
                            if k.lower() in normalized.lower()), "")
            return normalized, country
    return raw, ""


def _infer_platform(dc_or_region: str) -> str:
    s = dc_or_region.lower()
    if "aws" in s:
        return "aws"
    if "azure" in s:
        return "azure"
    if "gcp" in s or "google" in s:
        return "gcp"
    return "private_dc"


def _infra_shape(platform: str) -> tuple[str, str]:
    """Map a platform token to (node_kind, infra_type)."""
    if platform in ("aws", "azure", "gcp"):
        return "iaas_vpc_vnet", "public_cloud"
    return "data_center", "private_cloud"


def _runtime_token(runtime: str) -> str | None:
    s = (runtime or "").lower()
    if any(t in s for t in ("k8s", "kubernetes", "container", "docker", "aks", "eks", "ecs")):
        return "container"
    if any(t in s for t in ("vm", "instance", "ec2", "server", "virtual")):
        return "vm"
    if any(t in s for t in ("physical", "bare", "hardware", "appliance")):
        return "physical"
    if any(t in s for t in ("lambda", "function", "serverless", "faas")):
        return "serverless"
    return None


# ── HTTP client ───────────────────────────────────────────────────────────────

def _make_request(url: str, params: dict, auth_type: str,
                  auth_credentials: tuple) -> dict:
    """Make a REST API call and return parsed JSON."""
    if params:
        url = url + "?" + urllib.parse.urlencode(params)

    req = urllib.request.Request(url)

    if auth_type == "basic":
        import base64
        creds = base64.b64encode(f"{auth_credentials[0]}:{auth_credentials[1]}".encode()).decode()
        req.add_header("Authorization", f"Basic {creds}")
    elif auth_type == "bearer":
        req.add_header("Authorization", f"Bearer {auth_credentials[0]}")
    elif auth_type == "api_key":
        req.add_header("X-API-Key", auth_credentials[0])

    req.add_header("Accept", "application/json")

    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _get_nested(data: dict, dotted_path: str):
    """Get a nested value using dot notation."""
    parts = dotted_path.split(".")
    val = data
    for p in parts:
        if isinstance(val, dict):
            val = val.get(p, "")
        else:
            return ""
    return val


def _add_infra(req: PartialReq, name: str, country: str, platform: str, src: str) -> None:
    """Add a de-duplicated infra node for a physical location."""
    if not name:
        return
    if any(iv.value == name for iv in (e.name for e in req.infra if e.name)):
        return
    node_kind, infra_type = _infra_shape(platform)
    infra = PartialInfra(id=f"loc_{len(req.infra) + 1}")
    infra.name = fv(name, Confidence.HIGH, src)
    infra.node_kind = fv(node_kind, Confidence.MEDIUM, src, "Inferred from platform")
    infra.infra_type = fv(infra_type, Confidence.MEDIUM, src, "Inferred from platform")
    if country:
        infra.country = fv(country, Confidence.HIGH, src)
    req.infra.append(infra)


# ── Fetch from CMDB ───────────────────────────────────────────────────────────

def fetch_from_api(profile_name: str, app_ids: list[str],
                   custom_config: dict = None) -> PartialReq:
    """Fetch application data from a CMDB or EA system."""
    req = PartialReq(source_tool="arch-req-from-api",
                     source_file=f"api:{profile_name}")
    SRC = f"api:{profile_name}"

    profile = custom_config or PROFILES.get(profile_name, PROFILES["generic"])

    base_url = os.environ.get(profile.get("base_url_env", "CMDB_URL"), "")
    if not base_url:
        req.gaps.append(f"Environment variable {profile.get('base_url_env')} not set")
        return req

    auth_type = profile.get("auth_type", "bearer")
    auth_envs = profile.get("auth_env", ("CMDB_TOKEN",))
    auth_creds = tuple(os.environ.get(e, "") for e in auth_envs)
    if not all(auth_creds):
        req.gaps.append(f"Auth env vars not set: {auth_envs}")
        return req

    field_map = profile.get("field_map", {})
    endpoint = base_url + profile["endpoints"]["applications"]
    qparams = dict(profile.get("query_params", {}))

    results = []
    if app_ids:
        for app_id in app_ids:
            try:
                if profile_name == "servicenow":
                    qparams["sysparm_query"] = f"correlation_id={app_id}^ORname={app_id}"
                response = _make_request(endpoint, qparams, auth_type, auth_creds)
                items = response.get("result", response.get("data",
                        response if isinstance(response, list) else []))
                results.extend(items)
            except Exception as e:
                req.gaps.append(f"API error for app {app_id}: {e}")
    else:
        try:
            response = _make_request(endpoint, qparams, auth_type, auth_creds)
            items = response.get("result", response.get("data",
                    response if isinstance(response, list) else []))
            results.extend(items)
        except Exception as e:
            req.gaps.append(f"API error: {e}")
            return req

    for i, item in enumerate(results):
        system = PartialSystem(id=f"cmdb_{i+1}")

        name = _get_nested(item, field_map.get("app_name", "name"))
        if name:
            system.name = fv(str(name), Confidence.HIGH, SRC)

        owner_val = _get_nested(item, field_map.get("owner", "owner"))
        if owner_val:
            system.owner = fv(str(owner_val), Confidence.HIGH, SRC)

        dept = _get_nested(item, field_map.get("department", "department"))
        if dept:
            req.department = fv(str(dept), Confidence.HIGH, SRC)

        platform = str(_get_nested(item, field_map.get("platform", "platform")) or "")
        location = _get_nested(item, field_map.get("location", "datacenter"))
        if location:
            normalized, country = _normalize_dc(str(location))
            if not platform:
                platform = _infer_platform(normalized)
            _add_infra(req, normalized, country, platform, SRC)

        env = _get_nested(item, field_map.get("environment", "environment"))
        if env and str(env).lower() in ("production", "prod"):
            system.type = fv("existing", Confidence.HIGH, SRC)
        else:
            system.type = fv("existing", Confidence.LOW, SRC, "Defaulted — verify")

        if name:
            req.systems.append(system)

    req.no_coverage.extend([
        "tech_stack", "language", "framework", "runtime",
        "flows", "auth_methods", "protocols", "user_auth",
        "credentials", "encryption",
    ])
    req.gaps.append(
        "CMDB provides physical location and ownership. Tech stack, protocols and "
        "auth mechanisms are NOT in CMDB — collect from diagram files or interview."
    )
    return req


# ── CSV import ────────────────────────────────────────────────────────────────

CSV_COLUMN_ALIASES = {
    "name": ["name", "app_name", "application", "application_name"],
    "app_id": ["app_id", "id", "application_id", "appid"],
    "dc_or_region": ["dc_or_region", "datacenter", "dc", "region", "location"],
    "country": ["country", "country_code", "geo"],
    "platform": ["platform", "cloud", "environment_type"],
    "zone": ["zone", "zone_subnet", "network_zone", "subnet"],
    "owner": ["owner", "app_owner", "owner_team"],
    "infra_owner": ["infra_owner", "infrastructure_owner", "dc_owner"],
    "language": ["language", "tech_language", "prog_language"],
    "framework": ["framework", "tech_framework"],
    "runtime": ["runtime", "runtime_env", "deployment"],
    "sensitivity": ["sensitivity", "classification", "data_classification"],
}


def csv_to_partial(rows: list[dict], source_file: str) -> PartialReq:
    """Map CSV rows (already header-resolved) onto the req/v2 entity model."""
    req = PartialReq(source_tool="arch-req-from-api", source_file=source_file)
    SRC = f"csv:{Path(source_file).name}"

    for i, row in enumerate(rows):
        name = row.get("name", "")
        if not name:
            continue

        system = PartialSystem(id=f"csv_{i+1}")
        system.name = fv(name, Confidence.HIGH, SRC)
        system.type = fv("existing", Confidence.LOW, SRC, "CSV import — verify")
        if row.get("owner"):
            system.owner = fv(row["owner"], Confidence.HIGH, SRC)
        if row.get("sensitivity"):
            system.data_classification = fv(row["sensitivity"], Confidence.HIGH, SRC)
        req.systems.append(system)

        platform = row.get("platform") or ""
        dc = row.get("dc_or_region", "")
        zone = row.get("zone", "")
        normalized, country = _normalize_dc(dc)
        if not platform:
            platform = _infer_platform(normalized)
        # One canonical infra name, used both for the node and for the
        # deployment reference — otherwise the merger cannot resolve the
        # deployment's infra ref (it resolves references by normalized name).
        infra_name = f"{normalized} / {zone}" if zone else normalized
        if infra_name:
            _add_infra(req, infra_name, row.get("country") or country, platform, SRC)

        # Tech stack columns -> component + stacks + deployment
        lang = row.get("language", "")
        framework = row.get("framework", "")
        runtime = row.get("runtime", "")
        if lang or framework or runtime:
            component = PartialComponent(id=f"csv_comp_{i+1}")
            component.system = fv(name, Confidence.HIGH, SRC)
            component.name = fv(name, Confidence.MEDIUM, SRC,
                                "Component assumed from CSV row")
            component.kind = fv("component", Confidence.LOW, SRC, "Assumed")
            if row.get("sensitivity"):
                component.sensitivity = fv(row["sensitivity"], Confidence.HIGH, SRC)
            req.components.append(component)

            for order, tech in enumerate((lang, framework), start=1):
                if not tech:
                    continue
                stack = PartialStack(id=f"csv_stack_{i+1}_{order}")
                stack.component = fv(name, Confidence.HIGH, SRC)
                stack.component_name = fv(tech, Confidence.HIGH, SRC)
                stack.version = fv("TBD", Confidence.LOW, SRC)
                req.stacks.append(stack)

            if runtime:
                runtime_type = _runtime_token(runtime)
                if runtime_type:
                    deployment = PartialDeployment(id=f"csv_dep_{i+1}")
                    deployment.component = fv(name, Confidence.HIGH, SRC)
                    deployment.environment = fv("prod", Confidence.LOW, SRC)
                    deployment.deployment_type = fv(
                        "public_cloud" if platform in ("aws", "azure", "gcp") else "private_cloud",
                        Confidence.MEDIUM, SRC)
                    deployment.location_type = fv(
                        "public_cloud_region" if platform in ("aws", "azure", "gcp") else "data_center",
                        Confidence.MEDIUM, SRC)
                    if infra_name:
                        deployment.infra = fv(infra_name, Confidence.MEDIUM, SRC)
                    deployment.runtime_type = fv(runtime_type, Confidence.MEDIUM, SRC,
                                                 f"From runtime column: {runtime}")
                    deployment.runtime_detail = fv(runtime, Confidence.HIGH, SRC)
                    req.deployments.append(deployment)

    req.no_coverage.extend(["flows", "auth_methods", "user_auth",
                            "credentials", "encryption"])
    return req


def fetch_from_csv(csv_path: str) -> PartialReq:
    """Import applications from a CSV export."""
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        headers_lower = {h.lower().strip(): h for h in (reader.fieldnames or [])}

        def col(row: dict, canonical: str) -> str:
            for alias in CSV_COLUMN_ALIASES.get(canonical, [canonical]):
                if alias in headers_lower:
                    return str(row.get(headers_lower[alias], "")).strip()
            return ""

        rows = []
        for row in reader:
            rows.append({key: col(row, key) for key in CSV_COLUMN_ALIASES})

    return csv_to_partial(rows, csv_path)


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Fetch requirements from CMDB/EA API")
    parser.add_argument("--profile", default="servicenow",
                        choices=list(PROFILES.keys()),
                        help="CMDB profile (default: servicenow)")
    parser.add_argument("--config", default=None,
                        help="Custom config JSON file for field mapping")
    parser.add_argument("--app-id", nargs="*", default=[],
                        help="Application IDs to fetch (empty = fetch all)")
    parser.add_argument("--csv", default=None,
                        help="Import from CSV file instead of API")
    parser.add_argument("-o", "--output", default=None,
                        help="Output partial-req YAML file")
    args = parser.parse_args()

    if args.csv:
        req = fetch_from_csv(args.csv)
    else:
        custom_config = None
        if args.config:
            with open(args.config) as f:
                custom_config = json.load(f)
        req = fetch_from_api(args.profile, args.app_id, custom_config)

    out = partial_req_to_yaml(req)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out)
        print(f"✓ Partial requirements written: {args.output}")
        print(f"  Systems: {len(req.systems)}  |  Infra nodes: {len(req.infra)}"
              f"  |  Components: {len(req.components)}")
        if req.gaps:
            print("  Notes:")
            for g in req.gaps[:3]:
                print(f"    • {g}")
    else:
        print(out)


if __name__ == "__main__":
    main()
