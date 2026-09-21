"""Application API: stable keyword contract, exit codes, no global leaks."""

import pathlib
import sys
import tempfile
import unittest

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from archharness import api  # noqa: E402
from archharness.schemas import validate_final_req_v2  # noqa: E402


class ApplicationApiTests(unittest.TestCase):
    def test_run_requirements_offline(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = pathlib.Path(tmp)
            csv_path = tmpdir / "cmdb.csv"
            csv_path.write_text(
                "name,datacenter,country,platform,zone,owner\n"
                "Payments App,Hohhot DC,CN,private_dc,App Zone,org_it\n",
                encoding="utf-8",
            )
            out = tmpdir / "req.yaml"
            code = api.run_requirements(
                csv=str(csv_path),
                output=str(out),
                report=str(tmpdir / "gaps.md"),
                manifest=str(tmpdir / "manifest.json"),
            )
            self.assertEqual(code, 0)
            doc = yaml.safe_load(out.read_text(encoding="utf-8"))
            validate_final_req_v2(doc)
            self.assertEqual(doc["requirements"]["systems"][0]["name"], "Payments App")

    def test_run_requirements_missing_input_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            code = api.run_requirements(
                csv=str(pathlib.Path(tmp) / "nope.csv"),
                output=str(pathlib.Path(tmp) / "req.yaml"),
            )
            self.assertNotEqual(code, 0)

    def test_run_diagram_and_invalid_refs(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = pathlib.Path(tmp)
            arch = {
                "id": "demo",
                "name": "Demo",
                "deployment": [{
                    "id": "dc-a",
                    "type": "private_dc",
                    "network_zones": [{
                        "id": "z1",
                        "components": [{"id": "api", "name": "API"}],
                    }],
                }],
                "interactions": [{"from": "api", "to": "ghost", "protocol": "HTTPS"}],
            }
            src = tmpdir / "arch.yaml"
            src.write_text(yaml.safe_dump(arch), encoding="utf-8")
            code = api.run_diagram(input=str(src), output=str(tmpdir / "out.drawio"))
            self.assertNotEqual(code, 0)

            arch["interactions"] = []
            src.write_text(yaml.safe_dump(arch), encoding="utf-8")
            code = api.run_diagram(input=str(src), output=str(tmpdir / "out.drawio"))
            self.assertEqual(code, 0)
            self.assertTrue((tmpdir / "out.drawio").is_file())

    def test_validate_yaml_files(self):
        config = str(ROOT / "config.yaml")
        self.assertEqual(api.validate_yaml_files([config]), 0)
        with tempfile.TemporaryDirectory() as tmp:
            missing = str(pathlib.Path(tmp) / "nope.yaml")
            self.assertNotEqual(api.validate_yaml_files([missing]), 0)

    def test_no_global_leaks(self):
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = pathlib.Path(tmp) / "c.csv"
            csv_path.write_text("name\nDemo\n", encoding="utf-8")
            out = str(pathlib.Path(tmp) / "r.yaml")
            report = str(pathlib.Path(tmp) / "gaps.md")
            drawio = str(pathlib.Path(tmp) / "d.drawio")
            arch = str(ROOT / "tools" / "arch-diagram-gen" / "example_arch.yaml")
            # Warm up every tool once (transitional path inserts happen here).
            api.validate_yaml_files([str(ROOT / "config.yaml")])
            api.run_requirements(csv=str(csv_path), output=out, report=report)
            api.run_diagram(input=arch, output=drawio)
            path_before = list(sys.path)
            modules_before = set(sys.modules)
            # Repeated calls must not grow sys.path or sys.modules.
            api.validate_yaml_files([str(ROOT / "config.yaml")])
            api.run_requirements(csv=str(csv_path), output=out, report=report)
            api.run_diagram(input=arch, output=drawio)
            self.assertEqual(list(sys.path), path_before)
            self.assertEqual(set(sys.modules), modules_before)
            # Plain imports only: no file-location loader modules remain.
            for name in list(sys.modules):
                self.assertFalse(name.startswith("archharness_tool_"), name)


if __name__ == "__main__":
    unittest.main()
