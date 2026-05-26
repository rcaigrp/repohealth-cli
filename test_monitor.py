import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import main


class TestRepoHealth(unittest.TestCase):
    def test_generate_script_close(self):
        items = [{"repo_name": "test/repo", "number": 1}]
        script = main.generate_script(items, "close")
        self.assertIn("closed", script)
        self.assertIn("curl", script)
        self.assertIn("#!/bin/bash", script)

    def test_generate_script_label(self):
        items = [{"repo_name": "test/repo", "number": 1}]
        script = main.generate_script(items, "label")
        self.assertIn("stale", script)
        self.assertIn("curl", script)
        self.assertIn("#!/bin/bash", script)

    def test_generate_report_markdown(self):
        items = [{"repo_name": "test/repo", "title": "Test Issue"}]
        report = main.generate_report(items, "markdown")
        self.assertIn("# Stale Issues and PRs", report)
        self.assertIn("Test Issue", report)

    def test_generate_report_ascii(self):
        items = [{"repo_name": "test/repo", "title": "Test Issue"}]
        report = main.generate_report(items, "ascii")
        self.assertIn("Test Issue", report)
        self.assertIn("+------------------------+------------------+", report)


if __name__ == "__main__":
    unittest.main()
