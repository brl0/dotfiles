"""Unit tests for the vulnerability scanner."""

import unittest
from unittest.mock import patch, MagicMock
import json

from gen import PKG_GRAPH, Section, Package
from scanner import query_osv, scan_graph

class TestScanner(unittest.TestCase):
    
    @patch('urllib.request.urlopen')
    def test_query_osv_success(self, mock_urlopen):
        """Test successful OSV API query."""
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({"vulns": [{"id": "CVE-2023-1234"}]}).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp
        
        result = query_osv("requests", "PyPI")
        self.assertIn("vulns", result)
        self.assertEqual(result["vulns"][0]["id"], "CVE-2023-1234")

    @patch('urllib.request.urlopen')
    def test_query_osv_error(self, mock_urlopen):
        """Test OSV API error handling."""
        import urllib.error
        mock_urlopen.side_effect = urllib.error.URLError("Network unreachable")
        
        result = query_osv("requests", "PyPI")
        self.assertIn("error", result)
        self.assertIn("Network unreachable", result["error"])

    @patch('urllib.request.urlopen')
    def test_scan_graph(self, mock_urlopen):
        """Test scanning a PKG_GRAPH for vulnerabilities."""
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({"vulns": [{"id": "OSV-2024-5678", "details": "Fake issue"}]}).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        graph = PKG_GRAPH()
        section = Section(manager="pip", cache_group="default")
        section.packages.append(Package(name="pillow", version="==9.0.0"))
        graph.sections["pip"] = section
        
        results = scan_graph(graph)
        key = "pillow (pip)"
        self.assertIn(key, results)
        self.assertEqual(results[key][0]["id"], "OSV-2024-5678")

    def test_scan_graph_unsupported_manager(self):
        """Test scanning ignores unmapped ecosystems like brew."""
        graph = PKG_GRAPH()
        section = Section(manager="brew", cache_group="default")
        section.packages.append(Package(name="wget"))
        graph.sections["brew"] = section
        
        results = scan_graph(graph)
        self.assertEqual(len(results), 0)

if __name__ == '__main__':
    unittest.main()
