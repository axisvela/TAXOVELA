"""A recorded validation binds to exact image bytes; catch silent drift.

``validation/v1`` carries ``source.path`` + ``source.sha256``. Re-rendering an
image without re-validating rots that binding silently, because no other check
reads it. This guard fails when a binding dangles or mismatches, so the only
acknowledged exception is listed here and explained in docs/revalidation-guide.md.
"""

import hashlib
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

# Known-broken bindings, with the reason in docs/revalidation-guide.md:
# 06 was validated against an image whose bytes are no longer in the repository.
KNOWN_UNRESOLVED = {"06-factory-mes-industrial"}


class ValidationBindingTests(unittest.TestCase):
    def _results(self):
        examples = sorted(p for p in (ROOT / "examples").glob("*") if p.is_dir())
        return [(ex, ex / "output" / "validation" / "validate_result.json")
                for ex in examples]

    def test_bindings_resolve_and_match(self):
        problems = []
        checked = 0
        for example, path in self._results():
            if not path.is_file():
                continue
            source = json.loads(path.read_text(encoding="utf-8")).get("source") or {}
            relative = str(source.get("path", "")).replace("\\", "/")
            if not relative:
                problems.append(f"{example.name}: source.path is empty")
                continue
            target = example / relative
            checked += 1
            if not target.is_file():
                if example.name not in KNOWN_UNRESOLVED:
                    problems.append(f"{example.name}: binding dangles ({relative})")
                continue
            actual = hashlib.sha256(target.read_bytes()).hexdigest()
            if actual != source.get("sha256"):
                problems.append(
                    f"{example.name}: image changed since validation ({relative})")

        self.assertEqual(
            problems, [],
            "validation bindings drifted; see docs/revalidation-guide.md: "
            + "; ".join(problems),
        )
        self.assertGreater(checked, 0, "no example validation was checked")

    def test_acknowledged_exceptions_still_exist(self):
        """When 06 is re-validated, drop it from KNOWN_UNRESOLVED here."""
        present = {example.name for example, _ in self._results()}
        stale = KNOWN_UNRESOLVED - present
        self.assertEqual(stale, set(), f"unknown example in KNOWN_UNRESOLVED: {stale}")


if __name__ == "__main__":
    unittest.main()
