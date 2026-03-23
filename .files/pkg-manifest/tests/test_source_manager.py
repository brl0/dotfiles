"""Tests for the source package manager plugin."""

import unittest
from gen import parse_pkgm, get_manager_registry

class TestSourceManager(unittest.TestCase):
    
    def test_source_manager_registered(self):
        """Test that source manager is present in the global registry."""
        registry = get_manager_registry()
        self.assertTrue(registry.is_available("source"))
        
        source_meta = registry.get("source")
        self.assertIsNotNone(source_meta)
        self.assertIn("ls -1 ~/.pkgm/source_installs", source_meta["inventory_cmd"])
        
    def test_parse_source_manifest(self):
        """Test parsing a manifest with the source manager section."""
        manifest = "[source]\npackages:\n  htop[https://github.com/htop-dev/htop/archive/refs/tags/3.2.2.tar.gz]\n"
        graph = parse_pkgm(manifest)
        self.assertIn("source", graph.sections)
        
        section = graph.sections["source"]
        self.assertEqual(len(section.packages), 1)
        
        self.assertEqual(section.packages[0].name, "htop")
        self.assertEqual(section.packages[0].version, "[https://github.com/htop-dev/htop/archive/refs/tags/3.2.2.tar.gz]")

if __name__ == '__main__':
    unittest.main()
