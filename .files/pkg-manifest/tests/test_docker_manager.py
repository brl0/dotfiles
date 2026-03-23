"""Tests for the docker package manager plugin."""

import unittest
from gen import parse_pkgm, get_manager_registry

class TestDockerManager(unittest.TestCase):
    
    def test_docker_manager_registered(self):
        """Test that docker is present in the global manager registry."""
        registry = get_manager_registry()
        self.assertTrue(registry.is_available("docker"))
        
        docker_meta = registry.get("docker")
        self.assertIsNotNone(docker_meta)
        self.assertEqual(docker_meta["install_cmd"], "docker pull")
        
    def test_parse_docker_manifest(self):
        """Test parsing a manifest with the docker manager section."""
        manifest = "[docker]\npackages:\n  ubuntu[22.04]\n  nginx\n"
        graph = parse_pkgm(manifest)
        self.assertIn("docker", graph.sections)
        
        section = graph.sections["docker"]
        self.assertEqual(len(section.packages), 2)
        
        self.assertEqual(section.packages[0].name, "ubuntu")
        self.assertEqual(section.packages[0].version, "[22.04]")
        
        self.assertEqual(section.packages[1].name, "nginx")
        self.assertEqual(section.packages[1].version, "")

if __name__ == '__main__':
    unittest.main()
