"""CMDB / EA adapters: ServiceNow, generic REST, CSV, and secret externalization.

These cover the paths that the CLI exposes via ``--api servicenow|generic`` and
``--csv`` but that ``test_application_api.py`` only exercised through the CSV
happy path. The HTTP layer is faked; nothing here touches the network.
"""

import base64
import json
import os
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from archharness.requirements import from_api  # noqa: E402
from archharness.requirements.from_api import (  # noqa: E402
    fetch_from_api, fetch_from_csv, csv_to_partial,
    _normalize_dc, _infer_platform, _infra_shape, _runtime_token,
)
from archharness.requirements.merger import merge_partial_reqs  # noqa: E402


SERVICENOW_ROW = {
    "name": "Order Management System",
    "correlation_id": "OMS-001",
    "owned_by": {"display_value": "org_it"},
    "assignment_group": {"display_value": "SSG Team"},
    "location": {"display_value": "Hohhot DC"},
    "environment": "production",
}


class _FakeResponse:
    """Minimal stand-in for the object urlopen yields as a context manager."""

    def __init__(self, payload: bytes):
        self._payload = payload

    def read(self) -> bytes:
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _header(request, name: str):
    for key, value in request.headers.items():
        if key.lower() == name.lower():
            return value
    return None


class ServiceNowProfileTests(unittest.TestCase):
    """Built-in ServiceNow field mapping, no HTTP."""

    def _fetch(self, response, app_ids=("OMS-001",)):
        captured = {}

        def fake_request(url, params, auth_type, auth_creds):
            captured["url"] = url
            captured["params"] = dict(params)
            captured["auth_type"] = auth_type
            captured["auth_creds"] = auth_creds
            return response

        env = {
            "SERVICENOW_URL": "https://acme.service-now.com",
            "SERVICENOW_USER": "svc_reader",
            "SERVICENOW_PASSWORD": "s3cr3t",
        }
        with mock.patch.dict(os.environ, env, clear=True), \
                mock.patch.object(from_api, "_make_request", fake_request):
            req = fetch_from_api("servicenow", list(app_ids))
        return req, captured

    def test_field_mapping_to_partial_entities(self):
        req, _ = self._fetch({"result": [SERVICENOW_ROW]})

        self.assertEqual(len(req.systems), 1)
        system = req.systems[0]
        self.assertEqual(system.name.value, "Order Management System")
        self.assertEqual(system.owner.value, "org_it")
        self.assertEqual(system.type.value, "existing")
        self.assertEqual(req.department.value, "SSG Team")

        # Location is normalized and country inferred from the DC table.
        self.assertEqual(len(req.infra), 1)
        infra = req.infra[0]
        self.assertEqual(infra.name.value, "Neimeng DC (Hohhot)")
        self.assertEqual(infra.country.value, "CN")
        self.assertEqual(infra.node_kind.value, "data_center")
        self.assertEqual(infra.infra_type.value, "private_cloud")

    def test_app_id_becomes_servicenow_query(self):
        _, captured = self._fetch({"result": [SERVICENOW_ROW]})
        self.assertEqual(captured["params"]["sysparm_query"],
                         "correlation_id=OMS-001^ORname=OMS-001")
        self.assertTrue(captured["url"].endswith("/api/now/table/cmdb_ci_appl"))
        self.assertEqual(captured["auth_type"], "basic")

    def test_adapter_declares_its_coverage_honestly(self):
        req, _ = self._fetch({"result": [SERVICENOW_ROW]})
        self.assertIn("protocols", req.no_coverage)
        self.assertIn("auth_methods", req.no_coverage)
        self.assertTrue(any("NOT in CMDB" in gap for gap in req.gaps))


class GenericProfileTests(unittest.TestCase):
    """Custom field mapping via --config."""

    CONFIG = {
        "description": "Internal EA system",
        "base_url_env": "EA_SYSTEM_URL",
        "auth_type": "bearer",
        "auth_env": ["EA_SYSTEM_TOKEN"],
        "endpoints": {"applications": "/api/v1/applications"},
        "field_map": {
            "app_name": "displayName",
            "app_id": "applicationId",
            "owner": "businessOwner.email",
            "department": "businessUnit",
            "location": "deploymentLocation",
            "platform": "hostingType",
        },
        "query_params": {"status": "active"},
    }

    def test_custom_field_map_and_nested_paths(self):
        response = {"data": [{
            "displayName": "Payments App",
            "applicationId": "PAY-1",
            "businessOwner": {"email": "biz@example.com"},
            "businessUnit": "Finance",
            "deploymentLocation": "AWS US East",
            "hostingType": "aws",
        }]}

        def fake_request(*_args, **_kwargs):
            return response

        env = {"EA_SYSTEM_URL": "https://ea.example.com",
               "EA_SYSTEM_TOKEN": "tok"}
        with mock.patch.dict(os.environ, env, clear=True), \
                mock.patch.object(from_api, "_make_request", fake_request):
            req = fetch_from_api("generic", [], self.CONFIG)

        self.assertEqual(req.systems[0].name.value, "Payments App")
        self.assertEqual(req.systems[0].owner.value, "biz@example.com")
        self.assertEqual(req.department.value, "Finance")
        infra = req.infra[0]
        self.assertEqual(infra.name.value, "AWS US East (N. Virginia)")
        self.assertEqual(infra.country.value, "US")
        self.assertEqual(infra.node_kind.value, "iaas_vpc_vnet")
        self.assertEqual(infra.infra_type.value, "public_cloud")


class FetchFailureTests(unittest.TestCase):
    """Fail-closed behavior: unset configuration is a gap, never a crash."""

    def test_missing_base_url_records_gap(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            req = fetch_from_api("servicenow", ["OMS-001"])
        self.assertEqual(req.systems, [])
        self.assertTrue(any("SERVICENOW_URL" in gap for gap in req.gaps))

    def test_missing_auth_records_gap(self):
        env = {"SERVICENOW_URL": "https://acme.service-now.com"}
        with mock.patch.dict(os.environ, env, clear=True):
            req = fetch_from_api("servicenow", ["OMS-001"])
        self.assertEqual(req.systems, [])
        self.assertTrue(any("Auth env vars not set" in gap for gap in req.gaps))

    def test_api_error_records_gap_and_continues(self):
        def boom(*_args, **_kwargs):
            raise OSError("connection refused")

        env = {
            "SERVICENOW_URL": "https://acme.service-now.com",
            "SERVICENOW_USER": "u",
            "SERVICENOW_PASSWORD": "p",
        }
        with mock.patch.dict(os.environ, env, clear=True), \
                mock.patch.object(from_api, "_make_request", boom):
            req = fetch_from_api("servicenow", ["OMS-001"])
        self.assertEqual(req.systems, [])
        self.assertTrue(any("API error for app OMS-001" in gap for gap in req.gaps))


class HttpAuthTests(unittest.TestCase):
    """Authorization headers are built from the injected credential tuple."""

    def _capture(self, auth_type, creds):
        captured = {}

        def fake_urlopen(request, timeout=30):
            captured["request"] = request
            return _FakeResponse(json.dumps({"result": []}).encode("utf-8"))

        with mock.patch.object(from_api.urllib.request, "urlopen", fake_urlopen):
            from_api._make_request("https://x/api", {"a": "b"}, auth_type, creds)
        return captured["request"]

    def test_basic_auth(self):
        request = self._capture("basic", ("user", "pass"))
        expected = base64.b64encode(b"user:pass").decode()
        self.assertEqual(_header(request, "Authorization"), f"Basic {expected}")

    def test_bearer_auth(self):
        request = self._capture("bearer", ("tok",))
        self.assertEqual(_header(request, "Authorization"), "Bearer tok")

    def test_api_key_auth(self):
        request = self._capture("api_key", ("key-123",))
        self.assertEqual(_header(request, "X-API-Key"), "key-123")

    def test_params_are_url_encoded(self):
        request = self._capture("bearer", ("tok",))
        self.assertIn("a=b", request.full_url)


class HelperTests(unittest.TestCase):
    """The pure mapping tables that decide placement and runtime."""

    def test_dc_normalization(self):
        self.assertEqual(_normalize_dc("Hohhot DC")[0], "Neimeng DC (Hohhot)")
        self.assertEqual(_normalize_dc("hohhot")[1], "CN")
        self.assertEqual(_normalize_dc("AWS US East")[0], "AWS US East (N. Virginia)")
        self.assertEqual(_normalize_dc("some unknown place")[0], "some unknown place")
        self.assertEqual(_normalize_dc("some unknown place")[1], "")

    def test_platform_inference(self):
        self.assertEqual(_infer_platform("AWS US East"), "aws")
        self.assertEqual(_infer_platform("Azure East Asia"), "azure")
        self.assertEqual(_infer_platform("Google europe-west1"), "gcp")
        self.assertEqual(_infer_platform("Neimeng DC"), "private_dc")

    def test_infra_shape(self):
        self.assertEqual(_infra_shape("aws"), ("iaas_vpc_vnet", "public_cloud"))
        self.assertEqual(_infra_shape("private_dc"), ("data_center", "private_cloud"))

    def test_runtime_token(self):
        self.assertEqual(_runtime_token("Internal K8s"), "container")
        self.assertEqual(_runtime_token("VM"), "vm")
        self.assertEqual(_runtime_token("physical appliance"), "physical")
        self.assertEqual(_runtime_token("Lambda"), "serverless")
        self.assertIsNone(_runtime_token(""))


class CsvAdapterTests(unittest.TestCase):
    """CSV import: aliases, tech-stack expansion, and reference resolution."""

    CSV = (
        "name,app_id,dc_or_region,country,platform,zone,owner,infra_owner,"
        "language,framework,runtime,sensitivity\n"
        "OrderMgmt,OMS-001,Hohhot DC,CN,private_dc,App Zone,SSG Team,InfraSec,"
        "Java,Spring Boot,Internal K8s,confidential\n"
    )

    def _write(self, tmp: pathlib.Path) -> pathlib.Path:
        path = tmp / "cmdb.csv"
        path.write_text(self.CSV, encoding="utf-8")
        return path

    def test_rows_expand_to_entities(self):
        with tempfile.TemporaryDirectory() as tmp:
            req = fetch_from_csv(str(self._write(pathlib.Path(tmp))))

        self.assertEqual(len(req.systems), 1)
        self.assertEqual(req.systems[0].name.value, "OrderMgmt")
        self.assertEqual(req.systems[0].data_classification.value, "confidential")

        self.assertEqual(len(req.infra), 1)
        self.assertEqual(req.infra[0].name.value, "Neimeng DC (Hohhot) / App Zone")
        self.assertEqual(req.infra[0].country.value, "CN")

        self.assertEqual(len(req.components), 1)
        self.assertEqual(req.components[0].sensitivity.value, "confidential")

        stack_names = {s.component_name.value for s in req.stacks}
        self.assertEqual(stack_names, {"Java", "Spring Boot"})

        self.assertEqual(len(req.deployments), 1)
        self.assertEqual(req.deployments[0].runtime_type.value, "container")
        self.assertEqual(req.deployments[0].infra.value,
                         "Neimeng DC (Hohhot) / App Zone")

    def test_column_aliases_are_honoured(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "aliases.csv"
            path.write_text(
                "application_name,application_id,datacenter,zone,app_owner\n"
                "Legacy,L-1,Shenyang DC,App Zone,org_it\n",
                encoding="utf-8",
            )
            req = fetch_from_csv(str(path))
        self.assertEqual(req.systems[0].name.value, "Legacy")
        self.assertEqual(req.systems[0].owner.value, "org_it")
        self.assertEqual(req.infra[0].name.value, "Shenyang DC / App Zone")

    def test_csv_to_partial_reads_canonical_keys(self):
        """csv_to_partial is the post-alias layer: it takes canonical keys."""
        req = csv_to_partial(
            [{"name": "Legacy", "dc_or_region": "Reston DC", "platform": "private_dc"}],
            "canonical.csv",
        )
        self.assertEqual(req.systems[0].name.value, "Legacy")
        self.assertEqual(req.infra[0].name.value, "Reston DC")

    def test_deployment_infra_reference_resolves_on_merge(self):
        """Regression: the deployment must reference the *normalized* infra name.

        The infra node is created with the normalized DC name; if the deployment
        points at the raw name the merger cannot resolve it and drops a critical
        gap.
        """
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = pathlib.Path(tmp)
            csv_path = self._write(tmpdir)
            partial = tmpdir / "partial-csv.yaml"
            partial.write_text(
                from_api.partial_req_to_yaml(fetch_from_csv(str(csv_path))),
                encoding="utf-8",
            )
            _, _, gaps = merge_partial_reqs([str(partial)])

        unresolved_infra = [g for g in gaps["critical"] if "infra" in g and "unresolved" in g]
        self.assertEqual(unresolved_infra, [])


class SecretExternalizationTests(unittest.TestCase):
    """Credentials live in the environment, never in the adapter source."""

    def test_profiles_reference_env_names_only(self):
        for name, profile in from_api.PROFILES.items():
            self.assertIn("base_url_env", profile, name)
            self.assertIsInstance(profile["base_url_env"], str)
            for env_name in profile["auth_env"]:
                self.assertRegex(env_name, r"^[A-Z][A-Z0-9_]*$")
            self.assertNotIn("base_url", profile, name)
            self.assertNotIn("password", profile, name)


if __name__ == "__main__":
    unittest.main()
