import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from archharness.registry import check_example  # noqa: E402
from archharness.workspace import (  # noqa: E402
    find_workspace,
    get_project,
    init_project,
    init_workspace,
    list_projects,
)


class WorkspaceTests(unittest.TestCase):
    def test_initialize_multiple_isolated_projects(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            init_workspace(root)
            alpha = init_project(root, "alpha", name="Alpha")
            beta = init_project(root, "beta", make_default=True)

            self.assertEqual(["alpha", "beta"], list_projects(root))
            self.assertEqual("beta", get_project(root).project_id)
            self.assertNotEqual(alpha.input_path, beta.input_path)
            self.assertTrue(alpha.input_path.is_dir())
            self.assertTrue((beta.output_path / "validation").is_dir())

    def test_discovers_workspace_from_project_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            init_workspace(root)
            context = init_project(root, "payments")
            self.assertEqual(root.resolve(), find_workspace(context.input_path))

    def test_new_project_scaffolds_inputs_that_pass_the_registry_check(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            init_workspace(root)
            context = init_project(root, "orders", name="Order Platform")

            registry = context.input_path / "systems-registry.md"
            prompt = context.input_path / "prompt.md"
            readme = context.project_root / "README.md"
            self.assertTrue(registry.is_file())
            self.assertTrue(prompt.is_file())
            self.assertIn("archharness doctor", readme.read_text(encoding="utf-8"))

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                errors = check_example(context.project_root)

            self.assertEqual(errors, 0, output.getvalue())
            self.assertIn("OK", output.getvalue())

    def test_scaffold_is_not_written_over_an_existing_project(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            init_workspace(root)
            context = init_project(root, "orders")
            registry = context.input_path / "systems-registry.md"
            registry.write_text("# my own registry\n", encoding="utf-8")

            init_project(root, "orders-next")
            self.assertEqual(registry.read_text(encoding="utf-8"), "# my own registry\n")

    def test_rejects_unsafe_project_id(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            init_workspace(root)
            with self.assertRaises(ValueError):
                init_project(root, "../escape")


if __name__ == "__main__":
    unittest.main()
