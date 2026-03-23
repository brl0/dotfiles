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
        if not arg:
            print("Please provide a file name to save to.")
            return
            
        try:
            content = emit_manifest(self.graph)
            with open(arg, "w") as f:
                f.write(content)
            print(f"Successfully saved manifest to '{arg}'.")
        except Exception as e:
            print(f"Failed to save manifest: {e}")

    def do_install(self, arg):
        """install\nInstall the current manifest state to the local system by compiling an installation shell script."""
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
        except Exception as e:
            print(f"Installation failed: {e}")

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
