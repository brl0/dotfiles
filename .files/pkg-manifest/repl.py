#!/usr/bin/env python3
"""Interactive CLI Mode (REPL) for pkg-manifest."""

import cmd
import os
import sys
from pathlib import Path

# Add project root to sys.path so we can import gen
sys.path.insert(0, str(Path(__file__).parent))
from gen import PKG_GRAPH, Section, Package, parse_pkgm, emit_manifest

class PkgmREPL(cmd.Cmd):
    intro = "Welcome to the pkg-manifest REPL. Type 'help' or '?' to list commands.\n"
    prompt = "(pkgm) "
    
    def __init__(self):
        super().__init__()
        self.graph = PKG_GRAPH()
        from access import AccessManager
        self.access = AccessManager()

    def do_load(self, arg):
        """load [file_path]\nLoad an established .pkgm manifest into the active session."""
        if not arg:
            print("Please provide a file path.")
            return
        
        path = Path(arg)
        if not path.exists():
            print(f"Error: File '{path}' not found.")
            return
            
        try:
            with open(path, "r") as f:
                content = f.read()
            self.graph = parse_pkgm(content)
            print(f"Successfully loaded '{path}'.")
        except Exception as e:
            print(f"Failed to parse manifest: {e}")

    def do_list(self, arg):
        """list\nDisplay all packages categorized by their manager sections."""
        if not self.graph.sections:
            print("Manifest is currently empty. Use 'add' or 'load' to populate it.")
            return
        
        for section_name, section in self.graph.sections.items():
            print(f"\n[{section_name}]")
            for pkg in section.packages:
                print(f"  - {pkg.name}{pkg.version}")
        print()

    def do_add(self, arg):
        """add [manager_section] [pkg]\nAdd a package to the specified manager section (e.g., 'add apt/base curl')."""
        if not self.access.check_permission("developer", "add package"):
            print("Access Denied: You need at least 'developer' role to add packages.")
            return
            
        parts = arg.split()
        if len(parts) < 2:
            print("Usage: add <manager_section> <pkg> [version]")
            return
            
        section_name = parts[0]
        pkg_name = parts[1]
        version = parts[2] if len(parts) > 2 else ""
        
        if section_name not in self.graph.sections:
            manager = section_name.split('/')[0]
            cache_group = section_name.split('/')[1] if '/' in section_name else 'default'
            self.graph.sections[section_name] = Section(manager=manager, cache_group=cache_group)
            
        # Check if already exists to avoid duplicates
        exists = any(p.name == pkg_name for p in self.graph.sections[section_name].packages)
        if exists:
            print(f"Package '{pkg_name}' already exists in [{section_name}].")
        else:
            self.graph.sections[section_name].packages.append(Package(name=pkg_name, version=version))
            print(f"Added '{pkg_name}' to [{section_name}].")

    def do_remove(self, arg):
        """remove [manager_section] [pkg]\nRemove a package from the specified manager section."""
        if not self.access.check_permission("developer", "remove package"):
            print("Access Denied: You need at least 'developer' role to remove packages.")
            return

        parts = arg.split()
        if len(parts) < 2:
            print("Usage: remove <manager_section> <pkg>")
            return
            
        section_name = parts[0]
        pkg_name = parts[1]
        
        if section_name not in self.graph.sections:
            print(f"Error: Section [{section_name}] does not exist.")
            return
            
        section = self.graph.sections[section_name]
        initial_count = len(section.packages)
        section.packages = [p for p in section.packages if p.name != pkg_name]
        
        if len(section.packages) < initial_count:
            print(f"Removed '{pkg_name}' from [{section_name}].")
        else:
            print(f"Package '{pkg_name}' not found in [{section_name}].")

    def do_save(self, arg):
        """save [file_path]\nSave the active session's manifest to a .pkgm file."""
        if not self.access.check_permission("developer", "save manifest"):
            print("Access Denied: You need at least 'developer' role to save manifests.")
            return
            
        if not arg:
            print("Please provide a file name to save to.")
            return
            
        try:
            content = emit_manifest(self.graph)
            with open(arg, "w") as f:
                f.write(content)
            print(f"Successfully saved manifest to '{arg}'.")
            self.access.log_audit("SAVE_MANIFEST", f"Saved to '{arg}'")
        except Exception as e:
            print(f"Failed to save manifest: {e}")

    def do_install(self, arg):
        """install\nInstall the current manifest state to the local system by compiling an installation shell script."""
        if not self.access.check_permission("admin", "install system packages"):
            print("Access Denied: You need 'admin' role to install packages to the system.")
            return
            
        from gen import emit_install_sh
        import subprocess
        import tempfile
        try:
            print("Compiling manifest to installation script...")
            script = emit_install_sh(self.graph)
            
            with tempfile.NamedTemporaryFile("w", delete=False, suffix=".sh") as tmp:
                tmp.write(script)
                tmp_path = tmp.name
                
            print("Executing installation script...")
            subprocess.run(["/bin/bash", tmp_path], check=False)
            os.remove(tmp_path)
            print("Installation complete.")
            self.access.log_audit("INSTALL", "(via REPL compiled script)")
        except Exception as e:
            print(f"Installation failed: {e}")

    def do_sign(self, arg):
        """sign [file_path]\nGenerate a GPG detachment signature (.asc) for the specified manifest file."""
        if not arg:
            print("Please provide the file path of the manifest to sign.")
            return
            
        import subprocess
        try:
            print(f"Signing '{arg}' with GPG...")
            subprocess.run(["gpg", "--detach-sign", "--armor", arg], check=True)
            print(f"Signature created at '{arg}.asc'.")
        except subprocess.CalledProcessError as e:
            print(f"GPG signing failed: {e}")
        except FileNotFoundError:
            print("Error: gpg command not found on system.")

    def do_verify(self, arg):
        """verify [file_path]\nVerify a GPG detachment signature for the specified manifest file."""
        if not arg:
            print("Please provide the file path of the manifest to verify.")
            return
            
        import subprocess
        try:
            print(f"Verifying '{arg}'...")
            result = subprocess.run(["gpg", "--verify", f"{arg}.asc", arg], check=False)
            if result.returncode == 0:
                print("Signature verified successfully.")
            else:
                print("Signature verification failed.")
        except FileNotFoundError:
            print("Error: gpg command not found on system.")

    def do_scan(self, arg):
        """scan\nScan the loaded manifest for vulnerabilities using the OSV database."""
        if not self.graph.sections:
            print("Manifest is currently empty. Use 'add' or 'load' to populate it before scanning.")
            return

        from scanner import scan_graph
        print("Scanning packages for known vulnerabilities (this may take a moment)...")
        vulns = scan_graph(self.graph)
        
        if not vulns:
            print("✅ No vulnerabilities found!")
            return
            
        print("\n⚠️  Vulnerabilities Detected:")
        for pkg, issues in vulns.items():
            print(f"\n📦 {pkg}")
            for issue in issues:
                issue_id = issue.get("id", "Unknown ID")
                # Fallbacks for details: summary -> details -> simple description
                details = issue.get("summary", issue.get("details", "No detailed description available."))
                print(f"  - {issue_id}: {details}")
        print()

    def do_quit(self, arg):
        """quit\nExit the REPL session."""
        print("Exiting pkg-manifest REPL. Goodbye.")
        return True

    def do_exit(self, arg):
        """exit\nExit the REPL session."""
        return self.do_quit(arg)


if __name__ == '__main__':
    try:
        PkgmREPL().cmdloop()
    except KeyboardInterrupt:
        print("\nExiting pkg-manifest REPL. Goodbye.")
        sys.exit(0)
