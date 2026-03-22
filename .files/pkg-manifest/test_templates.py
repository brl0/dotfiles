#!/usr/bin/env python3
"""Test template rendering functionality"""

import sys

sys.path.insert(0, "/home/brl0/dotfiles/.files/pkg-manifest")

from gen import parse_pkgm, render_template

# Test manifest
manifest = """[apt/base]
mode=multi
inventory=apt list --installed
packages=
  curl
  build-essential
  vim

[pip/dev]
manager=pip
packages=
  pytest[~=7.0]
  black
"""

graph = parse_pkgm(manifest)

# Test each format
formats = [
    "install.sh",
    "dockerfile",
    "ansible-playbook",
    "noxfile",
    "manifest.pkgm",
    "github-actions",
]

for fmt in formats:
    print(f"\n{'=' * 60}")
    print(f"Format: {fmt}")
    print("=" * 60)
    try:
        output = render_template(fmt, graph, project_name="test-project")
        # Show first 50 lines or full output if shorter
        lines = output.split("\n")
        show_lines = min(50, len(lines))
        print("\n".join(lines[:show_lines]))
        if len(lines) > show_lines:
            print(f"\n... ({len(lines) - show_lines} more lines) ...")
        print(
            f"\n✓ Successfully rendered {fmt} ({len(output)} bytes, {len(lines)} lines)"
        )
    except Exception as e:
        print(f"✗ Error rendering {fmt}: {e}")

print(f"\n{'=' * 60}")
print("Template rendering tests complete!")
print("=" * 60)
