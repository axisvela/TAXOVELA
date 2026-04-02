"""
from_api.py — Fetch application metadata from CMDB / Enterprise Architecture systems.

Supports:
  - Generic REST API (configurable field mapping)
  - ServiceNow CMDB (built-in field mapping)
  - CSV export from any system

The CMDB typically provides: application name, DC/region, owner, infra owner.
It does NOT provide: tech stack details, auth mechanisms, protocols.
Those gaps must be filled by other readers or interview.

Usage:
    python from_api.py --profile servicenow --app-id APP001 -o partial-req.yaml
    python from_api.py --profile custom --config cmdb_config.json --app-id OMS -o partial-req.yaml
    python from_api.py --csv apps_export.csv -o partial-req.yaml
"""

import argparse
import csv
import json
import os
import sys
import urllib.request
import urllib.parse
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
from normalizer import (
    PartialReq, PartialApplication, PartialComponent, Confidence, fv,
    partial_req_to_yaml
)


# ── Built-in CMDB profiles ────────────────────────────────────────────────────

PROFILES = {
    "servicenow": {
        "description": "ServiceNow CMDB (cmdb_ci_appl table)",
        "base_url_env": "SERVICENOW_URL",          # e.g. https://company.service-now.com
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
    "neimeng": "Neimeng DC (Hohhot) [CN]",
    "hohhot": "Neimeng DC (Hohhot) [CN]",
    "shenyang": "Shenyang DC [CN]",
    "sy": "Shenyang DC [CN]",
    "reston": "Reston DC [US]",
    "frankfurt": "Frankfurt DC [DE]",
    "aws-us-east": "AWS US East (N. Virginia) [US]",
    "aws-us-east-1": "AWS US East (N. Virginia) [US]",
    "azure-east-asia": "Azure East Asia [SG/HK]",
    "azure-china-north": "Azure China North 2 [CN]",
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
    if "aws" in s: return "aws"
    if "azure" in s: return "azure"
    if "gcp" in s or "google" in s: return "gcp"
    return "private_dc"


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


# ── Fetch from CMDB ───────────────────────────────────────────────────────────

def fetch_from_api(profile_name: str, app_ids: list[str],
                   custom_config: dict = None) -> PartialReq:
    """Fetch application data from a CMDB or EA system."""
    req = PartialReq(source_tool="arch-req-from-api",
                     source_file=f"api:{profile_name}")
    SRC = f"api:{profile_name}"

    profile = custom_config or PROFILES.get(profile_name, PROFILES["generic"])

    # Resolve credentials
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

    # Build query for specific app IDs if provided
    results = []
    if app_ids:
        for app_id in app_ids:
            try:
                # Attempt ServiceNow-style query
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

    # Map results to PartialApplication
    for i, item in enumerate(results):
        app = PartialApplication(id=f"cmdb_{i+1}")

        name = _get_nested(item, field_map.get("app_name", "name"))
        if name:
            app.name = fv(str(name), Confidence.HIGH, SRC)

        app_id_val = _get_nested(item, field_map.get("app_id", "id"))
        if app_id_val:
            app.id = str(app_id_val)

        owner_val = _get_nested(item, field_map.get("owner", "owner"))
        if owner_val:
            app.owner = fv(str(owner_val), Confidence.HIGH, SRC)

        dept = _get_nested(item, field_map.get("department", "department"))
        if dept:
            req.department = fv(str(dept), Confidence.HIGH, SRC)

        location = _get_nested(item, field_map.get("location", "datacenter"))
        if location:
            normalized, country = _normalize_dc(str(location))
            app.dc_or_region = fv(normalized, Confidence.HIGH, SRC,
                                  f"Raw value: {location}")
            if country:
                app.country = fv(country, Confidence.HIGH, SRC)
            app.platform = fv(_infer_platform(normalized), Confidence.MEDIUM, SRC)

        env = _get_nested(item, field_map.get("environment", "environment"))
        if env and env.lower() in ("production", "prod"):
            app.type = fv("existing", Confidence.HIGH, SRC)

        infra_owner = _get_nested(item, field_map.get("infra_owner", ""))
        if infra_owner:
            app.infra_owner = fv(str(infra_owner), Confidence.HIGH, SRC)

        req.applications.append(app)

    req.no_coverage.extend([
        "tech_stack", "language", "framework", "runtime",
        "interactions", "auth_methods", "protocols", "user_auth",
        "credentials", "data_encryption"
    ])
    req.gaps.append(
        f"CMDB provides physical location and ownership. "
        f"Tech stack, protocols, and auth mechanisms are NOT in CMDB — "
        f"collect from diagram files or interview."
    )
    return req


# ── CSV import ────────────────────────────────────────────────────────────────

def fetch_from_csv(csv_path: str) -> PartialReq:
    """
    Import applications from a CSV export.
    
    Expected columns (case-insensitive, flexible):
    name, app_id, dc_or_region, country, platform, zone, owner, infra_owner,
    language, framework, runtime, sensitivity
    """
    req = PartialReq(source_tool="arch-req-from-api", source_file=csv_path)
    SRC = f"csv:{Path(csv_path).name}"

    COLUMN_ALIASES = {
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

    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        headers_lower = {h.lower().strip(): h for h in (reader.fieldnames or [])}

        def col(row: dict, canonical: str) -> str:
            for alias in COLUMN_ALIASES.get(canonical, [canonical]):
                if alias in headers_lower:
                    return str(row.get(headers_lower[alias], "")).strip()
            return ""

        for i, row in enumerate(reader):
            app = PartialApplication(id=f"csv_{i+1}")
            name = col(row, "name")
            if name:
                app.name = fv(name, Confidence.HIGH, SRC)
            if col(row, "app_id"):
                app.id = col(row, "app_id")

            dc = col(row, "dc_or_region")
            if dc:
                normalized, country = _normalize_dc(dc)
                app.dc_or_region = fv(normalized, Confidence.HIGH, SRC)
                explicit_country = col(row, "country")
                app.country = fv(
                    explicit_country if explicit_country else country,
                    Confidence.HIGH, SRC
                )

            platform = col(row, "platform")
            app.platform = fv(
                platform if platform else _infer_platform(dc),
                Confidence.MEDIUM if platform else Confidence.LOW, SRC
            )

            zone = col(row, "zone")
            if zone:
                app.zone_subnet = fv(zone, Confidence.HIGH, SRC)

            if col(row, "owner"):
                app.owner = fv(col(row, "owner"), Confidence.HIGH, SRC)
            if col(row, "infra_owner"):
                app.infra_owner = fv(col(row, "infra_owner"), Confidence.HIGH, SRC)

            # Some CSVs include tech stack
            lang = col(row, "language")
            fw = col(row, "framework")
            rt = col(row, "runtime")
            sens = col(row, "sensitivity")

            if lang or fw or rt:
                comp = PartialComponent(id=f"csv_comp_{i+1}", app_id=app.id)
                comp.name = fv(name, Confidence.HIGH, SRC)
                comp.comp_type = fv("BE", Confidence.LOW, SRC, "Type assumed from CSV")
                if lang:  comp.language  = fv(lang, Confidence.HIGH, SRC)
                if fw:    comp.framework = fv(fw, Confidence.HIGH, SRC)
                if rt:    comp.runtime   = fv(rt, Confidence.HIGH, SRC)
                if sens:  comp.sensitivity = fv(sens, Confidence.HIGH, SRC)
                req.components.append(comp)

            req.applications.append(app)

    req.no_coverage.extend(["interactions", "auth_methods", "user_auth",
                             "credentials", "data_encryption"])
    return req


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
        print(f"  Applications fetched: {len(req.applications)}")
        if req.gaps:
            print("  Notes:")
            for g in req.gaps[:3]:
                print(f"    • {g}")
    else:
        print(out)


if __name__ == "__main__":
    main()
