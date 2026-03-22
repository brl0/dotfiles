#!/usr/bin/env python3
"""
Install packages from a pkg-manifest file using gen.py parse_pkgm and emit_install_sh.

Usage:
    python3 install_from_manifest.py <manifest_name> [manifest_dir]

Arguments:
    manifest_name: Name of manifest file (relative to manifest_dir)
    manifest_dir:  Directory containing manifest files (default: /tmp/dotfiles/.files/config)
"""

import sys
import subprocess
import traceback
from pathlib import Path
from gen import parse_pkgm, emit_install_sh


def install_from_manifest(
    manifest_name: str, manifest_dir: str = "/tmp/dotfiles/.files/config"
) -> int:
    """
    Parse a manifest file and execute the generated install script.

    Args:
        manifest_name: Name of the manifest file (with or without .pkgm extension)
        manifest_dir: Directory where manifest files are located

    Returns:
        Exit code from the installation script
    """
    manifest_dir = Path(manifest_dir)

    # Ensure manifest name has .pkgm extension
    if not manifest_name.endswith(".pkgm"):
        manifest_name = f"{manifest_name}.pkgm"

    manifest_path = manifest_dir / manifest_name

    if not manifest_path.exists():
        print(f"❌ Error: Manifest file not found: {manifest_path}", file=sys.stderr)
        return 1

    try:
        # Read manifest
        with open(manifest_path) as f:
            manifest_content = f.read()

        print(f"📦 Parsing {manifest_name}...", file=sys.stderr)
        # Parse manifest to PKG_GRAPH
        graph = parse_pkgm(manifest_content)

        print(f"📦 Generating install script from {manifest_name}...", file=sys.stderr)
        # Generate install script
        script = emit_install_sh(graph, manifest_name.replace(".pkgm", ""))

        print(f"📦 Installing from {manifest_name}...", file=sys.stderr)
        # Execute the generated script
        result = subprocess.run(["/bin/bash", "-c", script], check=False)

        if result.returncode == 0:
            print(f"✅ Successfully installed from {manifest_name}", file=sys.stderr)
        else:
            print(
                f"⚠️  Installation from {manifest_name} completed with exit code {result.returncode}",
                file=sys.stderr,
            )

        return result.returncode

    except RecursionError as e:
        print(f"❌ RecursionError in {manifest_name}: {e}", file=sys.stderr)
        print(
            "This may indicate a circular reference in the template or manifest.",
            file=sys.stderr,
        )
        traceback.print_exc(file=sys.stderr)
        return 1
    except Exception as e:
        print(
            f"❌ Error installing from {manifest_name}: {type(e).__name__}: {e}",
            file=sys.stderr,
        )
        traceback.print_exc(file=sys.stderr)
        return 1


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        sys.exit(1)

    manifest_name = sys.argv[1]
    manifest_dir = sys.argv[2] if len(sys.argv) > 2 else "/tmp/dotfiles/.files/config"

    exit_code = install_from_manifest(manifest_name, manifest_dir)
    sys.exit(exit_code)
