"""AGENTS.md and CLAUDE.md share one body; CI fails when the two drift.

Both rules files describe the same tool to different hosts. The shared body is
delimited by ``archharness-shared`` markers so the host-specific headers can
differ while the substance stays identical.
"""

import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

START = "<!-- archharness-shared:start -->"
END = "<!-- archharness-shared:end -->"

EXPECTED_HEADINGS = (
    "## What this is",
    "## Available agents and skills",
    "## Configuration",
    "## Multi-project workspace",
    "## Standards in scope",
    "## Validation rules",
    "## Scoring",
    "## Pipeline discipline (mandatory order)",
)

EXPECTED_STANDARDS = (
    "private-cloud-standard.yaml",
    "aws-standard.yaml",
    "azure-standard.yaml",
    "gcp-standard.yaml",
    "aliyun-standard.yaml",
    "microsoft-saas-standard.yaml",
)


def shared_body(path: pathlib.Path) -> str:
    text = path.read_text(encoding="utf-8")
    if START not in text or END not in text:
        raise AssertionError(f"{path.name}: missing archharness-shared markers")
    return text.split(START, 1)[1].split(END, 1)[0].strip()


class RulesFilesInSyncTests(unittest.TestCase):
    def test_shared_bodies_match(self):
        agents = shared_body(ROOT / "AGENTS.md")
        claude = shared_body(ROOT / "CLAUDE.md")
        self.assertEqual(
            agents, claude,
            "AGENTS.md and CLAUDE.md shared body drifted — mirror the edit in both",
        )

    def test_shared_body_covers_the_expected_sections(self):
        body = shared_body(ROOT / "AGENTS.md")
        for heading in EXPECTED_HEADINGS:
            self.assertIn(heading, body)

    def test_standards_section_lists_every_standard(self):
        body = shared_body(ROOT / "AGENTS.md")
        for standard in EXPECTED_STANDARDS:
            self.assertIn(standard, body)


if __name__ == "__main__":
    unittest.main()
