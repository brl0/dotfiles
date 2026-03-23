"""Tests for snap and flatpak manager parsing."""

import unittest
from gen import parse_pkgm, get_manager_registry

class TestNewManagers(unittest.TestCase):
    def test_snap_manager_registered(self):
        self.assertTrue(get_manager_registry().is_available("snap"))
        self.assertIn("snap install", get_manager_registry().get("snap")["install_cmd"])

    def test_flatpak_manager_registered(self):
        self.assertTrue(get_manager_registry().is_available("flatpak"))
        self.assertIn("flatpak install", get_manager_registry().get("flatpak")["install_cmd"])

    def test_parse_new_managers(self):
        manifest = "[snap]\npackages:\n  spotify\n\n[flatpak]\npackages:\n  com.spotify.Client\n"
        graph = parse_pkgm(manifest)
        self.assertIn("snap", graph.sections)
        self.assertEqual(graph.sections["snap"].packages[0].name, "spotify")

        self.assertIn("flatpak", graph.sections)
        self.assertEqual(graph.sections["flatpak"].packages[0].name, "com.spotify.Client")

if __name__ == '__main__':
    unittest.main()
