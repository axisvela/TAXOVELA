import tempfile
import unittest
from pathlib import Path

from archharness.workspace import (
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

    def test_rejects_unsafe_project_id(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            init_workspace(root)
            with self.assertRaises(ValueError):
                init_project(root, "../escape")


if __name__ == "__main__":
    unittest.main()
