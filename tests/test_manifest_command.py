"""archharness manifest: artifact/v1 provenance for an arbitrary file.

This is the CLI the re-validation runbook uses to re-record a re-rendered
diagram, so it must store a portable project-relative path and an exact hash.
"""

import contextlib
import hashlib
import io
import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from archharness import cli  # noqa: E402
from archharness.schemas import validate_manifest  # noqa: E402


class ManifestCommandTests(unittest.TestCase):
    def _run(self, argv):
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(io.StringIO()):
            code = cli.main(argv)
        return code, buffer.getvalue()

    def test_builds_a_valid_manifest(self):
        # Created inside the repo so the stored path is project-relative.
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            target = pathlib.Path(tmp) / "diagram.png"
            target.write_bytes(b"\x89PNG-bytes")
            code, out = self._run([
                "manifest", "--file", str(target), "--id", "diagram.png",
                "--type", "technical-deployment-view", "--schema", "diagram/png",
                "--input", "blueprint.yaml",
            ])

        self.assertEqual(code, 0)
        doc = json.loads(out)
        validate_manifest(doc)
        self.assertEqual(doc["schema_version"], "artifact/v1")
        self.assertEqual(doc["id"], "diagram.png")
        self.assertEqual(doc["type"], "technical-deployment-view")
        self.assertEqual(doc["schema"], "diagram/png")
        self.assertEqual(doc["input_artifacts"], ["blueprint.yaml"])
        self.assertEqual(doc["sha256"], hashlib.sha256(b"\x89PNG-bytes").hexdigest())
        self.assertFalse(pathlib.Path(doc["path"]).is_absolute())
        self.assertNotIn("\\", doc["path"])

    def test_id_defaults_to_the_file_stem(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            target = pathlib.Path(tmp) / "req.yaml"
            target.write_text("schema_version: req/v2\n", encoding="utf-8")
            code, out = self._run(["manifest", "--file", str(target)])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["id"], "req")

    def test_missing_file_fails_closed(self):
        code, _ = self._run(["manifest", "--file", str(ROOT / "nope.png")])
        self.assertEqual(code, 2)

    def test_output_flag_writes_the_manifest(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            target = pathlib.Path(tmp) / "d.png"
            target.write_bytes(b"x")
            out_file = pathlib.Path(tmp) / "d.manifest.json"
            code, _ = self._run(["manifest", "--file", str(target),
                                 "-o", str(out_file)])
            self.assertEqual(code, 0)
            self.assertTrue(out_file.is_file())
            validate_manifest(json.loads(out_file.read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()
