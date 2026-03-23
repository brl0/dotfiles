"""Package Manifest Generator (gen.py)."""

from dataclasses import dataclass, field
import hashlib
import configparser
import copy
import json
import os
from pathlib import Path

try:
    from jinja2 import Environment, FileSystemLoader, TemplateNotFound

    HAS_JINJA2 = True
except ImportError:
    HAS_JINJA2 = False


def _get_base_directory() -> Path:
    """Get the base directory containing managers.json and managers/ directory."""
    return Path(__file__).parent


def _load_managers_registry() -> dict[str, dict]:
    """Load manager registry from managers.json file."""
    managers_file = _get_base_directory() / "managers.json"
    if managers_file.exists():
        with open(managers_file) as f:
            return json.load(f)
    return {}


def _load_manager_script(manager_name: str) -> str | None:
    """Load manager shell script from managers/ directory."""
    script_file = _get_base_directory() / "managers" / f"{manager_name}.sh"
    if script_file.exists():
        with open(script_file) as f:
            return f.read()
    return None


@dataclass
class Package:
    """Represents a single package."""

    name: str
    version: str = ""
    features: list[str] = field(default_factory=list)
    tags: set[str] = field(default_factory=set)
    source: str = ""

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if not isinstance(other, Package):
            return False
        return self.name == other.name


@dataclass
class Section:
    """Represents a package manager section [manager/cache-group]."""

    manager: str
    cache_group: str
    packages: list[Package] = field(default_factory=list)
    commands: dict[str, str] = field(default_factory=dict)  # pre, init, install, post
    metadata: dict[str, str] = field(
        default_factory=dict,
    )  # system metadata from comments
    inventory_cmd: str = ""
    lock_file: str = ""
    mode: str = "multi"  # single or multi


@dataclass
class PKG_GRAPH:
    """Central in-memory representation of parsed manifest."""

    format_version: str = "1.0"
    metadata: dict[str, str] = field(default_factory=dict)
    sections: dict[str, Section] = field(default_factory=dict)
    manager_deps: dict[str, list[str]] = field(default_factory=dict)

    def filter_tags(
        self,
        include: list[str] | None = None,
        exclude: list[str] | None = None,
    ) -> "PKG_GRAPH":
        """Filter packages by tags."""
        filtered = copy.deepcopy(self)

        for section in filtered.sections.values():
            # Extract tags from metadata
            tags_meta = section.metadata.get("tags", "")
            package_tags = self._parse_tags(tags_meta)

            filtered_packages = []

            for pkg in section.packages:
                pkg_tags = package_tags.get(pkg.name, set())

                # Non-tagged always included (unless excluded)
                if not pkg_tags:
                    if exclude:
                        excluded = any(tag in exclude for tag in exclude)
                        if not excluded:
                            filtered_packages.append(pkg)
                    else:
                        filtered_packages.append(pkg)
                else:
                    # Tagged packages: check include/exclude
                    if include:
                        matches_include = any(tag in include for tag in pkg_tags)
                    else:
                        matches_include = True

                    if exclude:
                        matches_exclude = any(tag in exclude for tag in pkg_tags)
                    else:
                        matches_exclude = False

                    if matches_include and not matches_exclude:
                        filtered_packages.append(pkg)

            section.packages = filtered_packages

        return filtered

    def _parse_tags(self, tags_meta: str) -> dict[str, set[str]]:
        """Parse tags metadata into package->tags dict."""
        result = {}
        if not tags_meta:
            return result

        # Parse "pkg1=tag1,tag2 pkg2=tag3" format
        for item in tags_meta.split():
            if "=" in item:
                pkg_name, tags_str = item.split("=", 1)
                tags = {tag.strip() for tag in tags_str.split(",")}
                result[pkg_name.strip()] = tags

        return result

    def apply_lock_file(self, manager: str, lock_content: str) -> None:
        """Apply lock file versions to packages."""
        # Parse lock file format (one per line, pkg==version)
        locked = {}
        for line in lock_content.split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "==" in line:
                pkg_name, version = line.split("==", 1)
                locked[pkg_name.strip()] = "==" + version.strip()

        # Apply to packages in sections
        for section in self.sections.values():
            if section.manager == manager:
                for pkg in section.packages:
                    if pkg.name in locked:
                        pkg.version = locked[pkg.name]


# ===== MANAGER REGISTRY SYSTEM =====
class ManagerRegistry:
    """Registry for package managers with extensibility support."""

    def __init__(self):
        """Initialize with built-in managers loaded from managers.json."""
        self._managers: dict[str, dict] = _load_managers_registry()
        self._custom_managers: dict[str, dict] = {}

    def get(self, manager_name: str) -> dict | None:
        """Get manager metadata by name."""
        return self._managers.get(manager_name) or self._custom_managers.get(
            manager_name,
        )

    def register(self, manager_name: str, metadata: dict) -> None:
        """Register a custom manager."""
        if manager_name in self._managers:
            msg = f"Cannot override built-in manager: {manager_name}"
            raise ValueError(msg)
        self._custom_managers[manager_name] = metadata

    def list_managers(self) -> list[str]:
        """List all available manager names."""
        return list(self._managers.keys()) + list(self._custom_managers.keys())

    def is_available(self, manager_name: str) -> bool:
        """Check if manager exists in registry."""
        return manager_name in self._managers or manager_name in self._custom_managers


# Global registry instance
_manager_registry = ManagerRegistry()


def get_manager_registry() -> ManagerRegistry:
    """Get the global manager registry."""
    return _manager_registry


def parse_pkgm(manifest_str: str) -> PKG_GRAPH:
    """Parse .pkgm manifest into PKG_GRAPH."""
    # Expand environment variables mathematically (Phase 10)
    manifest_str = os.path.expandvars(manifest_str)

    graph = PKG_GRAPH()
    config = configparser.ConfigParser()
    config.read_string(manifest_str)

    for section_name in config.sections():
        # Parse section header [manager/cache-group]
        if "/" in section_name:
            manager, cache_group = section_name.split("/", 1)
        else:
            manager = section_name
            cache_group = "default"

        section = Section(manager=manager, cache_group=cache_group)

        # Parse declarative metadata (INI keys)
        if config.has_option(section_name, "mode"):
            section.mode = config.get(section_name, "mode")
        if config.has_option(section_name, "inventory"):
            section.inventory_cmd = config.get(section_name, "inventory")
        if config.has_option(section_name, "lock"):
            section.lock_file = config.get(section_name, "lock")

        for cmd in ["pre", "init", "install", "post"]:
            if config.has_option(section_name, cmd):
                section.commands[cmd] = config.get(section_name, cmd)

        # Parse packages (custom parsing after 'packages:' line)
        if config.has_option(section_name, "packages"):
            packages_text = config.get(section_name, "packages")
            for pkg_line in packages_text.split("\n"):
                pkg_line = pkg_line.strip()
                if pkg_line and not pkg_line.startswith("#"):
                    pkg_name, version = _parse_package_line(pkg_line)
                    section.packages.append(
                        Package(name=pkg_name, version=version),
                    )

        # Parse system metadata from original manifest comments
        _parse_system_metadata_from_manifest(
            section,
            manifest_str,
            section_name,
        )

        graph.sections[section_name] = section

    # Evaluate package conditions (Phase 10: Condition-Based Selection)
    import sys
    env_locals = {"sys": sys, "os": os}
    for section in graph.sections.values():
        filtered_packages = []
        for pkg in section.packages:
            cond_key = f"condition({pkg.name})"
            if cond_key in section.metadata:
                expr = section.metadata[cond_key]
                try:
                    if not eval(expr, {"__builtins__": {}}, env_locals):
                        continue
                except Exception as e:
                    raise ValueError(f"Failed to evaluate condition '{expr}' for package '{pkg.name}': {e}")
            filtered_packages.append(pkg)
        section.packages = filtered_packages

    return graph


def _parse_package_line(line: str) -> tuple[str, str]:
    """Parse a package line: 'name' or 'name[constraint]'.

    Handles:
    - Simple names: 'git'
    - With versions: 'python@3.12', 'git[extras]'
    - With trailing comma/continuation: 'git, \\' or 'git\\'
    """
    line = line.strip()

    # Remove trailing backslash (line continuation)
    if line.endswith("\\"):
        line = line[:-1].rstrip()

    # Remove trailing comma
    if line.endswith(","):
        line = line[:-1].rstrip()

    # Parse version constraints
    if "[" in line:
        name_part, constraint_part = line.split("[", 1)
        return name_part.strip(), "[" + constraint_part

    return line.strip(), ""


def _parse_system_metadata_from_manifest(
    section: Section,
    manifest_str: str,
    section_name: str,
) -> None:
    """Extract system metadata from manifest comments."""
    lines = manifest_str.split("\n")
    in_section = False

    for line in lines:
        stripped = line.strip()

        # Check if we're in the target section
        if stripped.startswith(f"[{section_name}]"):
            in_section = True
            continue

        # Stop if we hit another section
        if in_section and stripped.startswith("[") and stripped.endswith("]"):
            break

        # Extract system metadata from comments
        if in_section and stripped.startswith("#"):
            comment = stripped.lstrip("# ").strip()

            if comment.startswith("@"):
                # System metadata: @key: value
                if ":" in comment:
                    key, value = comment.split(":", 1)
                    key = key.strip()[1:]  # Remove '@'
                    value = value.strip()
                    section.metadata[key] = value
                elif "=" in comment:
                    # @tags: package=tag1,tag2
                    parts = comment.split("=", 1)
                    key = parts[0].strip()[1:]  # Remove '@'
                    value = parts[1].strip()
                    section.metadata[key] = value


def compute_manifest_hash(manifest_str: str) -> str:
    """Compute deterministic SHA256 hash of manifest."""
    return hashlib.sha256(manifest_str.encode()).hexdigest()


def diff_packages(
    old: list[Package],
    new: list[Package],
) -> tuple[list[Package], list[Package], list[Package]]:
    """Compare two package lists."""
    old_map = {p.name: p for p in old}
    new_map = {p.name: p for p in new}

    added = [p for name, p in new_map.items() if name not in old_map]
    removed = [p for name, p in old_map.items() if name not in new_map]
    modified = []

    for name in old_map:
        if name in new_map and (
            old_map[name].version != new_map[name].version
            or old_map[name].features != new_map[name].features
        ):
            modified.append(new_map[name])

    return added, removed, modified


def emit_manifest(graph: PKG_GRAPH) -> str:
    """Emit PKG_GRAPH back to .pkgm format."""
    lines = []

    for section_name, section in graph.sections.items():
        lines.append(f"[{section_name}]")
        if section.mode != "multi":
            lines.append(f"mode={section.mode}")
        if section.inventory_cmd:
            lines.append(f"inventory={section.inventory_cmd}")
        if section.lock_file:
            lines.append(f"lock={section.lock_file}")

        for cmd, value in section.commands.items():
            lines.append(f"{cmd}={value}")

        if section.packages:
            lines.append("packages:")
            for pkg in section.packages:
                lines.append(f"  {pkg.name}{pkg.version}")

        for key, value in section.metadata.items():
            lines.append(f"# @{key}: {value}")

        lines.append("")

    return "\n".join(lines)


def emit_dockerfile(graph: PKG_GRAPH) -> str:
    """Emit PKG_GRAPH as Dockerfile."""
    lines = ["FROM ubuntu:22.04", "# Generated Dockerfile", ""]

    # Add metadata
    for section_name, section in graph.sections.items():
        if section.manager == "apt":
            lines.append(f"# [{section_name}]")
            if section.inventory_cmd:
                lines.append(f"# inventory={section.inventory_cmd}")
            for key, val in section.metadata.items():
                lines.append(f"# @{key}: {val}")

            pkgs = " ".join(f"{p.name}{p.version}" for p in section.packages)
            if pkgs:
                if "pre" in section.commands:
                    lines.append(f"RUN {section.commands['pre']}")
                lines.append(f"RUN apt-get install -y {pkgs}")

    return "\n".join(lines)


def emit_ansible_playbook(graph: PKG_GRAPH) -> str:
    """Emit PKG_GRAPH as Ansible playbook."""
    lines = ["---", "# Generated Ansible playbook", "- hosts: all", "  tasks:", ""]

    for section_name, section in graph.sections.items():
        lines.append(f"    # [{section_name}]")
        for key, val in section.metadata.items():
            lines.append(f"    # @{key}: {val}")

        if section.manager == "apt":
            pkgs = [f"{p.name}{p.version}" for p in section.packages]
            if pkgs:
                lines.append(f"    - name: Install {section_name} packages")
                lines.append("      apt:")
                lines.append(f"        name: {pkgs}")

    return "\n".join(lines)


def emit_noxfile(graph: PKG_GRAPH) -> str:
    """Emit PKG_GRAPH as noxfile.py."""
    lines = [
        '"""Generated noxfile.py"""',
        "import nox",
        "",
    ]

    for section_name, section in graph.sections.items():
        if section.manager == "pip":
            lines.append("@nox.session")
            s_name = section_name.replace("/", "_")
            lines.append(f"def {s_name}(session):")
            lines.append(f'    """Install {section_name}."""')
            for key, val in section.metadata.items():
                lines.append(f"    # @{key}: {val}")
            pkgs = [f"{p.name}{p.version}" for p in section.packages]
            if pkgs:
                pkg_str = ", ".join(repr(p) for p in pkgs)
                lines.append(f"    session.install({pkg_str})")
            lines.append("")

    return "\n".join(lines)


def emit_manager_modules(graph: PKG_GRAPH) -> dict[str, str]:
    """Emit manager-specific shell modules from PKG_GRAPH.

    Returns dict of {manager: shell_code} with idempotent install_packages().
    """
    managers_dict = {}
    managers_seen = set()

    for section in graph.sections.values():
        manager = section.manager

        if manager in managers_seen:
            continue

        managers_seen.add(manager)

        # Load manager script from file
        shell_code = _load_manager_script(manager)
        if shell_code:
            managers_dict[manager] = shell_code

    return managers_dict


def emit_install_sh(
    graph: PKG_GRAPH,
    project_name: str = "pkgm",
    force: bool = False,
    manifest_str: str = "",
    skip_state: bool = False,
    section_filter: list[str] | None = None,
) -> str:
    """Emit PKG_GRAPH as idempotent install shell script using template.

    Features:
    - Tier 1: Check manifest hash against state file (skip if matched, unless --force)
    - Tier 2: For each manager, check inventory_cmd if provided, compute delta
    - Support mode=single (stop on first failure) vs mode=multi (continue)
    - Return codes: 0=no work, 1=error, 2=work done
    - Handle pre/post/init commands from metadata

    Falls back to direct generation if Jinja2 unavailable or templates missing.
    """
    # Check if we can use templates
    if not HAS_JINJA2:
        return _emit_install_sh_direct(
            graph,
            project_name=project_name,
            force=force,
            manifest_str=manifest_str,
            skip_state=skip_state,
            section_filter=section_filter,
        )

    # Check if templates exist
    templates_dir = get_template_directory()
    if not templates_dir:
        return _emit_install_sh_direct(
            graph,
            project_name=project_name,
            force=force,
            manifest_str=manifest_str,
            skip_state=skip_state,
            section_filter=section_filter,
        )

    # Use template-based rendering
    return render_template(
        "install.sh",
        graph,
        project_name=project_name,
        force=force,
        manifest_str=manifest_str,
        skip_state=skip_state,
        section_filter=section_filter,
    )


def _emit_install_sh_direct(
    graph: PKG_GRAPH,
    project_name: str = "pkgm",
    force: bool = False,
    manifest_str: str = "",
    skip_state: bool = False,
    section_filter: list[str] | None = None,
) -> str:
    """Generate basic install.sh script without templates (fallback).

    This is used when Jinja2 is unavailable or templates can't be found.
    Generates a simple but functional shell script.
    """
    lines = [
        "#!/bin/bash",
        "# Generated install script (template fallback mode)",
        "set -e",
        "",
        f"PROJECT_NAME='{project_name}'",
    ]

    # Compute manifest hash for tier-1 idempotency
    manifest_hash = compute_manifest_hash(manifest_str) if manifest_str else "unknown"
    lines.append(f"MANIFEST_HASH='{manifest_hash}'")

    lines.extend(
        [
            "",
            "# Tier 1: Check manifest hash to skip if unchanged",
            f'STATE_FILE="$HOME/.{project_name}.pkgm.state"',
            "if [ -f \"$STATE_FILE\" ] && ! [ '{0}' = '1' ]; then".format(
                "true" if force else "false"
            ),
            '    LAST_HASH=$(grep "manifest_hash" "$STATE_FILE" 2>/dev/null | '
            'cut -d= -f2 || echo "")',
            '    if [ "$LAST_HASH" = "$MANIFEST_HASH" ]; then',
            '        echo "[info] Manifest unchanged, skipping installation"',
            "        exit 0",
            "    fi",
            "fi",
            "",
        ]
    )

    # Install per manager section
    for section_name, section in graph.sections.items():
        if section_filter and section_name not in section_filter:
            continue
            
        manager = section.manager
        lines.append(f"# Section: [{section_name}] (manager={manager})")

        # Run pre command if present
        if "pre" in section.commands:
            lines.append(f"echo '[{manager}] Running pre-install...'")
            lines.append(section.commands["pre"])

        # Run install command if packages exist
        if section.packages:
            packages_str = " ".join([pkg.name for pkg in section.packages])
            install_cmd = section.commands.get(
                "install",
                f"{manager} install",
            )
            pkg_count = len(section.packages)
            lines.append(f"echo '[{manager}] Installing {pkg_count} packages...'")
            lines.append(f"{install_cmd} {packages_str}")

        # Run post command if present
        if "post" in section.commands:
            lines.append(f"echo '[{manager}] Running post-install...'")
            lines.append(section.commands["post"])

        lines.append("")

    # Update state file
    if not skip_state:
        lines.extend(
            [
                "# Save state for next run",
                'mkdir -p "$(dirname "$STATE_FILE")"',
                'cat > "$STATE_FILE" <<STATE',
                f"manifest_hash={manifest_hash}",
                "STATE",
            ]
        )
    
    lines.extend(
        [
            "",
            "echo '[info] Installation complete'",
            "exit 0",
        ]
    )

    return "\n".join(lines)


def get_template_directory() -> Path | None:
    """Get the templates directory path."""
    if not HAS_JINJA2:
        return None

    # Look for templates/ subdirectory relative to this file
    current_dir = Path(__file__).parent
    templates_dir = current_dir / "templates"

    if templates_dir.exists():
        return templates_dir

    return None


def render_template(
    format_name: str,
    graph: PKG_GRAPH,
    project_name: str = "pkgm",
    force: bool = False,
    manifest_str: str = "",
    skip_state: bool = False,
    section_filter: list[str] | None = None,
) -> str:
    """Render PKG_GRAPH as specified format using Jinja2 templates.

    Supported formats: install.sh, dockerfile, ansible-playbook, noxfile,
    manifest.pkgm, github-actions

    Falls back to hardcoded functions if Jinja2 is not available.
    """
    if not HAS_JINJA2:
        # Fallback to non-template versions
        return _render_format_fallback(
            format_name,
            graph,
            project_name,
            force,
            manifest_str,
            skip_state,
            section_filter,
        )

    templates_dir = get_template_directory()
    if not templates_dir:
        # Fallback if templates directory not found
        return _render_format_fallback(
            format_name,
            graph,
            project_name,
            force,
            manifest_str,
            skip_state,
            section_filter,
        )

    # Set up Jinja2 environment
    env = Environment(loader=FileSystemLoader(str(templates_dir)))

    # Add custom filters
    def shell_escape(value: str) -> str:
        """Escape a string for safe use in single-quoted shell strings.

        Converts a string to be safely usable within single quotes by
        replacing ' with '\"'\"' pattern.
        """
        if not value:
            return value
        return value.replace("'", "'\"'\"'")

    env.filters["shell_escape"] = shell_escape

    template_map = {
        "install.sh": "install.sh.j2",
        "dockerfile": "dockerfile.j2",
        "Dockerfile": "dockerfile.j2",
        "ansible": "ansible-playbook.j2",
        "ansible-playbook": "ansible-playbook.j2",
        "noxfile": "noxfile.j2",
        "noxfile.py": "noxfile.j2",
        "manifest": "manifest.pkgm.j2",
        "manifest.pkgm": "manifest.pkgm.j2",
        "github-actions": "github-actions.j2",
        "gha": "github-actions.j2",
    }

    template_name = template_map.get(format_name)
    if not template_name:
        raise ValueError(f"Unsupported format: {format_name}")

    try:
        template = env.get_template(template_name)
    except TemplateNotFound:
        # Fallback if template not found
        return _render_format_fallback(
            format_name,
            graph,
            project_name,
            force,
            manifest_str,
        )

    # Prepare context for template
    manager_modules = emit_manager_modules(graph)
    manifest_hash = compute_manifest_hash(manifest_str) if manifest_str else "unknown"

    context = {
        "graph": graph,
        "format_name": format_name,
        "project_name": project_name,
        "manifest_hash": manifest_hash,
        "force": str(force).lower(),
        "manager_modules": manager_modules,
        "skip_state": skip_state,
        "section_filter": section_filter,
    }

    return template.render(context)


def _render_format_fallback(
    format_name: str,
    graph: PKG_GRAPH,
    project_name: str = "pkgm",
    force: bool = False,
    manifest_str: str = "",
    skip_state: bool = False,
    section_filter: list[str] | None = None,
) -> str:
    """Fallback rendering using hardcoded functions."""
    format_lower = format_name.lower()

    if format_lower in ("install.sh", "shell", "bash"):
        return emit_install_sh(graph, project_name, force, manifest_str, skip_state, section_filter)
    if format_lower in ("dockerfile", "docker"):
        return emit_dockerfile(graph)
    if format_lower in ("ansible", "ansible-playbook"):
        return emit_ansible_playbook(graph)
    if format_lower in ("noxfile", "noxfile.py", "nox"):
        return emit_noxfile(graph)
    if format_lower in ("manifest", "manifest.pkgm", "pkgm"):
        return emit_manifest(graph)
    raise ValueError(f"Unsupported format: {format_name}")


if __name__ == "__main__":
    # Development and testing
    pass
