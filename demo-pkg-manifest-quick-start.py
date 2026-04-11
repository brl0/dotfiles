#!/usr/bin/env python3
"""Quick demo of pkg-manifest installer scripts.

This script shows you how to use the two new demonstrator scripts.
Run this to see all available options.
"""

import subprocess
import sys
from pathlib import Path

DOTFILES = Path(__file__).parent


def run_cmd(cmd, title):
    """Run a command and show its output."""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}\n")
    print(f"$ {cmd}\n")
    try:
        subprocess.run(cmd, shell=True, cwd=DOTFILES, check=False)
    except Exception as e:
        print(f"Error: {e}")


def main():
    """Show quick start examples."""
    print("""
╔════════════════════════════════════════════════════════════════════╗
║                 pkg-manifest Installer Demo                       ║
║                    Quick Start Guide                              ║
╚════════════════════════════════════════════════════════════════════╝

TWO NEW SCRIPTS CREATED:

1. demo-pkg-manifest-installer.sh  (Bash)
2. demo-pkg-manifest-installer.py  (Python)

Both demonstrate how to use pkg-manifest to generate installer scripts
from .pkgm configuration files.

QUICK EXAMPLES:
""")

    examples = [
        (
            "python3 demo-pkg-manifest-installer.py --help",
            "Show Python script help",
        ),
        (
            "python3 demo-pkg-manifest-installer.py --list",
            "List available manifests",
        ),
        (
            "python3 demo-pkg-manifest-installer.py --info sys-packages",
            "Show manifest details",
        ),
        (
            "python3 demo-pkg-manifest-installer.py --preview sys-packages "
            "2>&1 | head -60",
            "Preview generated installer (first 60 lines)",
        ),
        (
            "./demo-pkg-manifest-installer.sh --help",
            "Show shell script help",
        ),
    ]

    for i, (cmd, desc) in enumerate(examples, 1):
        print(f"\n{i}. {desc}")
        print(f"   $ {cmd[48:] if len(cmd) > 48 else cmd}")

    print("""

FULL WORKFLOW EXAMPLE:

  Step 1: List available manifests
    $ python3 demo-pkg-manifest-installer.py --list

  Step 2: Check what a manifest contains
    $ python3 demo-pkg-manifest-installer.py --info sys-packages

  Step 3: Preview the generated installer script
    $ python3 demo-pkg-manifest-installer.py --preview sys-packages

  Step 4: Execute the installer (install packages)
    $ python3 demo-pkg-manifest-installer.py sys-packages

  Step 5: Try a dry-run (show what would happen)
    $ python3 demo-pkg-manifest-installer.py --dry-run python-packages

AVAILABLE MANIFESTS:

  sys-packages.pkgm      - System utilities, build tools, CLI apps
  python-packages.pkgm   - Python packages via pip
  brew-packages.pkgm     - Homebrew packages (macOS)
  utility-packages.pkgm  - Additional utility packages

FILES CREATED:

  ✓ demo-pkg-manifest-installer.sh
  ✓ demo-pkg-manifest-installer.py
  ✓ DEMO-PKG-MANIFEST-INSTALLER-README.md (Full documentation)
  ✓ DEMO-PKG-MANIFEST-SUMMARY.md (Summary of features)

WHAT IT DEMONSTRATES:

  1. pkg-manifest format (.pkgm files)
     - INI-style configuration
     - [manager/cache-group] sections
     - Multiple package managers

  2. Generator system (gen.py)
     - Parse manifests
     - Generate idempotent install scripts
     - Support multiple output formats

  3. Idempotent installation
     - Can run scripts multiple times safely
     - Embed manifest hashes for verification
     - Optional inventory queries for drift detection

LEARN MORE:

  See DEMO-PKG-MANIFEST-INSTALLER-README.md for:
    - Detailed usage examples
    - Integration patterns (Docker, CI/CD, etc.)
    - Troubleshooting tips
    - How to create custom manifests

TRY IT NOW:

""")

    # Ask if user wants to run examples
    response = (
        input("Would you like to see a live example? (y/n) [default: y]: ")
        .strip()
        .lower()
    )

    if response in ("y", "yes", ""):
        run_cmd(
            "python3 demo-pkg-manifest-installer.py --list",
            "Example 1: List Available Manifests",
        )
        run_cmd(
            "python3 demo-pkg-manifest-installer.py --info sys-packages",
            "Example 2: Show Manifest Information",
        )

    print("\n" + "=" * 70)
    print("✅ Ready to use! Try the commands above.")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nCancelled")
        sys.exit(0)
