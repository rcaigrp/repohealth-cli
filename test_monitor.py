import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class TestSmoke(unittest.TestCase):
    def test_import_main(self):
        try:
            import main
            self.assertTrue(True)
        except ImportError:
            self.fail("main.py not found or has syntax errors")

if __name__ == '__main__':
    unittest.main()