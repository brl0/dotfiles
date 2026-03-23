"""Vulnerability scanning module using the OSV.dev API."""

import json
import urllib.request
import urllib.error
from typing import Dict, List, Any

from gen import PKG_GRAPH

OSV_API_URL = "https://api.osv.dev/v1/query"

# Map package managers to OSV ecosystems where possible
ECOSYSTEM_MAP = {
    "pip": "PyPI",
    "npm": "npm",
    "cargo": "crates.io",
    "apt": "Debian", # May be rejected if specific version needed, but best effort
}

def query_osv(package_name: str, ecosystem: str = "", version: str = "") -> Dict[str, Any]:
    """Query OSV.dev API for vulnerabilities for a specific package."""
    query: Dict[str, Any] = {"package": {"name": package_name}}
    if ecosystem:
        if ecosystem == "Debian":
            # OSV doesn't generally accept just "Debian", it wants "Debian:11" etc.
            # We omit ecosystem for apt to do a broader text search if possible, or leave it.
            # Actually, OSV will reject if ecosystem is incomplete and no exact version/commit is given.
            # We will supply it as generic, if it errors, it errors.
            query["package"]["ecosystem"] = "Debian"
        else:
            query["package"]["ecosystem"] = ecosystem
        
    if version:
        # OSV expects an exact version. Strip any pip-style constraints.
        clean_version = version.replace("==", "").replace("=", "").strip()
        if clean_version and not any(op in clean_version for op in ["<", ">", "~", "^"]):
             query["version"] = clean_version

    data = json.dumps(query).encode("utf-8")
    req = urllib.request.Request(
        OSV_API_URL,
        data=data,
        headers={"Content-Type": "application/json"}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 400:
            return {"error": f"OSV Bad Request: Check ecosystem/version format for {package_name}"}
        return {"error": str(e)}
    except urllib.error.URLError as e:
        return {"error": str(e)}

def scan_graph(graph: PKG_GRAPH) -> Dict[str, List[Dict[str, Any]]]:
    """Scan all packages in a PKG_GRAPH for vulnerabilities.
    
    Returns a dictionary mapping 'package_name (manager)' to a list of vulnerabilities.
    """
    results: Dict[str, List[Dict[str, Any]]] = {}
    for section_name, section in graph.sections.items():
        manager = section.manager
        ecosystem = ECOSYSTEM_MAP.get(manager, "")
        
        # Skip managers that have no clear OSV ecosystem mapping
        if not ecosystem:
            continue
            
        for pkg in section.packages:
            resp = query_osv(pkg.name, ecosystem, pkg.version)
            vulns = resp.get("vulns")
            if vulns:
                results[f"{pkg.name} ({manager})"] = vulns
            elif "error" in resp:
                 results[f"{pkg.name} ({manager})"] = [{"id": "SCAN_ERROR", "details": resp["error"]}]
            
    return results
