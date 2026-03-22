#!/usr/bin/env python3
"""pkg-manifest Installer Demo.

A simple Python wrapper to demonstrate pkg-manifest usage.
Generates installer scripts from .pkgm manifest files.

Usage:
    python3 demo-pkg-manifest-installer.py [OPTIONS] [manifest_name]

Examples:
    # Generate and execute installer for system packages
    python3 demo-pkg-manifest-installer.py sys-packages

    # Preview the installer without executing
    python3 demo-pkg-manifest-installer.py sys-packages --preview

    # Show available manifests
    python3 demo-pkg-manifest-installer.py --list

    # Get help
    python3 demo-pkg-manifest-installer.py --help

"""

import sys
import subprocess
import argparse
from pathlib import Path

# Import from local pkg-manifest generator
sys.path.insert(0, str(Path(__file__).parent / ".files" / "pkg-manifest"))
from gen import parse_pkgm, emit_install_sh


class ManifestInstaller:
    """Wrapper for pkg-manifest installer generation and execution."""

    def __init__(self, config_dir: Path | None = None) -> None:
        """Initialize installer with configuration directory."""
        if config_dir is None:
            config_dir = Path(__file__).parent / ".files" / "config"

        self.config_dir = Path(config_dir)
        self.verbose = False

    def find_manifests(self) -> list[str]:
        """Find all available .pkgm manifest files."""
        return sorted(p.stem for p in self.config_dir.glob("*.pkgm"))

    def get_manifest_path(self, manifest_name: str) -> Path:
        """Get full path to manifest file, adding .pkgm extension if needed."""
        if not manifest_name.endswith(".pkgm"):
            manifest_name = f"{manifest_name}.pkgm"
        return self.config_dir / manifest_name

    def parse_manifest(self, manifest_path: Path) -> tuple:
        """Parse manifest file and return PKG_GRAPH."""
        if not manifest_path.exists():
            msg = f"Manifest not found: {manifest_path}"
            raise FileNotFoundError(msg)

        with manifest_path.open() as f:
            content = f.read()

        return parse_pkgm(content)

    def generate_installer(self, manifest_name: str) -> str:
        """Generate installer script for manifest."""
        manifest_path = self.get_manifest_path(manifest_name)
        base_name = manifest_name.replace(".pkgm", "")

        self._log(f"Parsing: {manifest_path}")
        graph = self.parse_manifest(manifest_path)

        self._log("Generating installer script")
        script = emit_install_sh(graph, base_name)

        return script

    def preview_installer(self, manifest_name: str, lines: int = 50) -> None:
        """Show preview of generated installer."""
        self._section(f"Preview: {manifest_name} Installer")

        try:
            script = self.generate_installer(manifest_name)

            self._log(f"Showing first {lines} lines of generated script:")
            print("−" * 70)
            for line in script.split("\n")[:lines]:
                print(line)

            total_lines = len(script.split("\n"))
            if total_lines > lines:
                print(f"... ({total_lines - lines} more lines)")
            print("−" * 70)

            self._analyze_script(script)

        except (FileNotFoundError, ValueError) as e:
            self._error(f"Failed to generate installer: {e}")
            raise

    def run_installer(self, manifest_name: str, dry_run: bool = False) -> int:
        """Generate and execute installer script."""
        self._section(f"Installing from: {manifest_name}")

        try:
            script = self.generate_installer(manifest_name)

            if dry_run:
                self._log("DRY-RUN MODE: Script would be executed")
                self._analyze_script(script)
                return 0

            self._log("Executing installer script")
            self._log("")

            result = subprocess.run(["/bin/bash", "-c", script], check=False)

            if result.returncode == 0:
                self._success("Installation completed successfully")
            else:
                msg = f"Installation completed with exit code {result.returncode}"
                self._warn(msg)

            return result.returncode

        except Exception as e:
            self._error(f"Installation failed: {e}")
            return 1

    def list_manifests(self) -> None:
        """List all available manifest files."""
        self._section("Available Manifests")

        manifests = self.find_manifests()

        if not manifests:
            msg = f"No manifest files found in: {self.config_dir}"
            self._warn(msg)
            return

        for manifest in manifests:
            path = self.get_manifest_path(manifest)
            size = path.stat().st_size
            size_str = self._format_size(size)

            # Count packages (rough estimate)
            with path.open() as f:
                content = f.read()
            pkg_count = content.count("\n") - content.count("[")

            print(f"  • {manifest:<25} ({size_str:>8}, ~{pkg_count} packages)")

    def show_manifest_info(self, manifest_name: str) -> None:
        """Show information about a specific manifest."""
        manifest_path = self.get_manifest_path(manifest_name)

        self._section(f"Manifest: {manifest_name}")

        if not manifest_path.exists():
            self._error(f"Manifest not found: {manifest_path}")
            return

        # File info
        size = manifest_path.stat().st_size
        print(f"Path: {manifest_path}")
        print(f"Size: {self._format_size(size)}")

        # Content preview
        with manifest_path.open() as f:
            lines = f.readlines()

        print(f"Lines: {len(lines)}")
        print("")
        print("Content preview:")
        print("−" * 70)
        for line in lines[:20]:
            print(line.rstrip())
        if len(lines) > 20:
            print(f"... ({len(lines) - 20} more lines)")
        print("−" * 70)

    def _analyze_script(self, script: str) -> None:
        """Analyze and display script statistics."""
        lines = script.split("\n")
        managers = set()

        if "install_apt" in script:
            managers.add("apt")
        if "install_brew" in script:
            managers.add("brew")
        if "install_pip" in script:
            managers.add("pip")
        if "install_conda" in script:
            managers.add("conda")

        print("")
        print("Script statistics:")
        print(f"  • Total lines: {len(lines)}")
        if managers:
            mgr_str = ", ".join(sorted(managers))
            print(f"  • Package managers: {mgr_str}")

    def _format_size(self, size: int) -> str:
        """Format byte size as human-readable string."""
        size_float = float(size)
        for unit in ("B", "KB", "MB", "GB"):
            if size_float < 1000:
                return f"{size_float:.1f}{unit}"
            size_float /= 1000
        return f"{size_float:.1f}TB"

    def _section(self, title: str) -> None:
        """Print a section header."""
        print("")
        print("━" * 70)
        print(f"  {title}")
        print("━" * 70)

    def _log(self, msg: str) -> None:
        """Print info message."""
        if self.verbose:
            print(f"ℹ️  {msg}")

    def _success(self, msg: str) -> None:
        """Print success message."""
        print(f"✅ {msg}")

    def _warn(self, msg: str) -> None:
        """Print warning message."""
        print(f"⚠️  {msg}")

    def _error(self, msg: str) -> None:
        """Print error message."""
        print(f"❌ {msg}", file=sys.stderr)


def main() -> int:
    """Parse arguments and run installer."""
    parser = argparse.ArgumentParser(
        description=(
            "pkg-manifest Installer Demo - Generate installers from manifest files"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List available manifests
  %(prog)s --list

  # Show info about a manifest
  %(prog)s --info sys-packages

  # Preview installer without running
  %(prog)s --preview sys-packages

  # Generate and run installer
  %(prog)s sys-packages

  # Run with verbose output
  %(prog)s -v sys-packages
        """,
    )

    parser.add_argument(
        "manifest",
        nargs="?",
        default="sys-packages",
        help="Manifest file name (with or without .pkgm extension)",
    )
    parser.add_argument(
        "-l",
        "--list",
        action="store_true",
        help="List all available manifest files",
    )
    parser.add_argument(
        "-i",
        "--info",
        action="store_true",
        help="Show information about the manifest",
    )
    parser.add_argument(
        "-p",
        "--preview",
        action="store_true",
        help="Preview the installer without executing",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Execute in dry-run mode (show what would happen)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show verbose output",
    )
    parser.add_argument(
        "--config-dir",
        type=Path,
        help="Override config directory path",
    )

    args = parser.parse_args()

    installer = ManifestInstaller(config_dir=args.config_dir)
    installer.verbose = args.verbose

    try:
        if args.list:
            installer.list_manifests()
            return 0

        # Ensure manifest name is valid
        manifests = installer.find_manifests()
        if not args.manifest.endswith(".pkgm") and args.manifest not in manifests:
            # Check if it's a valid manifest
            manifest_path = installer.get_manifest_path(args.manifest)
            if not manifest_path.exists():
                msg = f"Error: Unknown manifest '{args.manifest}'"
                print(f"❌ {msg}", file=sys.stderr)
                print("Available manifests:", file=sys.stderr)
                for m in manifests:
                    print(f"  • {m}", file=sys.stderr)
                return 1

        if args.info:
            installer.show_manifest_info(args.manifest)
            return 0

        if args.preview:
            installer.preview_installer(args.manifest)
            return 0

        # Run installer
        return installer.run_installer(args.manifest, dry_run=args.dry_run)

    except KeyboardInterrupt:
        print("\n⚠️  Installation cancelled by user")
        return 130
    except (FileNotFoundError, ValueError, OSError) as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
