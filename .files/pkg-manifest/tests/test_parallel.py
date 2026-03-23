"""Tests for ParallelRunner DAG execution."""

import json
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

from gen import PKG_GRAPH, Section
from runner import ParallelRunner, get_state_file


class TestParallelRunner(unittest.TestCase):
    def setUp(self):
        self.graph = PKG_GRAPH()
        self.graph.sections = {
            "apt/base": Section(manager="apt", cache_group="base"),
            "pip/tools": Section(manager="pip", cache_group="tools"),
            "pip/dev": Section(manager="pip", cache_group="dev"),
        }
        self.graph.manager_deps = {
            "pip": ["apt"],  # pip depends on apt
        }

    @patch("runner.subprocess.run")
    @patch("runner.emit_install_sh")
    def test_dag_resolution_and_execution(self, mock_emit, mock_run):
        # Mock emit to return empty string
        mock_emit.return_value = "echo 'mocked'"
        
        # Mock run to succeed
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Mocked output"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        runner = ParallelRunner(
            graph=self.graph,
            project_name="test_pkgm",
            manifest_str="[apt/base]\n[pip/tools]\n[pip/dev]",
            force=True
        )
        
        # Force fresh state
        runner.state = {"finished_managers": []}
        
        status = runner.run()
        self.assertEqual(status, 0)
        
        # Verify emit was called 3 times total
        self.assertEqual(mock_emit.call_count, 3)
        
        # Verify state file was updated
        state_file = get_state_file("test_pkgm")
        if state_file.exists():
            with open(state_file) as f:
                state = json.load(f)
                self.assertIn("timestamp", state)

if __name__ == "__main__":
    unittest.main()
