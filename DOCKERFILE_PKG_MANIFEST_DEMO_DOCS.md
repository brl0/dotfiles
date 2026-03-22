# pkg-manifest Demo Dockerfile

## Overview

This document describes **Dockerfile.pkg-manifest-demo**, which demonstrates how to use the **pkg-manifest** system to:

1. **Parse** a package manifest file (INI format)
2. **Generate** an idempotent installation shell script
3. **Execute** the script to install packages across multiple package managers

## What Is pkg-manifest?

**pkg-manifest** is an enterprise-grade package management generator (~2,000 lines) that converts unified manifest files into deployment artifacts:

- **Input**: `.pkgm` manifest file (INI format defining sections, packages, metadata)
- **Output**: Installation scripts, Dockerfiles, Ansible playbooks, noxfiles, GitHub Actions workflows
- **Features**:
    - ✅ Two-tier idempotency (manifest hash + per-manager inventory checks)
    - ✅ Multi-manager support (apt, brew, pip, conda, webi)
    - ✅ State tracking (JSON state file prevents re-running unchanged installs)
    - ✅ Fail-fast vs continue modes (single/multi)
    - ✅ Pre/post/init lifecycle commands
    - ✅ Tag-based filtering and package diffing

---

## Dockerfile Workflow

### Step 1: Copy pkg-manifest System Files

```dockerfile
COPY .files/pkg-manifest/gen.py ./gen.py
COPY .files/pkg-manifest/managers.json ./managers.json
COPY .files/pkg-manifest/managers/ ./managers/
COPY .files/pkg-manifest/templates/ ./templates/
```

These files provide:

- **gen.py**: Core generator with `parse_pkgm()` and `emit_install_sh()` functions
- **managers.json**: Registry of available package managers (apt, brew, pip, conda, webi)
- **managers/**: Shell modules implementing idempotent `install_packages()` for each manager
- **templates/**: Jinja2 templates for generating various output formats

### Step 2: Copy Manifest File

```dockerfile
COPY .files/config/pkgs_sys.conf ./pkgs_sys.conf
```

The manifest file (`pkgs_sys.conf`) defines:

- **Section**: `[apt]` - Package manager and cache group
- **Metadata**: `mode=multi`, `pre`, `install`, `post` commands
- **Packages**: 28 packages (apt-utils, build-essential, curl, git, etc.)

### Step 3: Generate and Execute Install Script

```python
# Parse manifest → PKG_GRAPH data structure
graph = parse_pkgm(manifest_content)

# Generate idempotent installation script
install_script = emit_install_sh(graph, project_name='pkgm-demo')

# Execute the generated script
subprocess.run(['bash', '-c', install_script])
```

---

## Technical Details

### Manifest Format (INI)

```ini
[apt/base]
mode=multi
pre=apt-get update
post=apt-get clean && rm -rf /var/lib/apt/lists/*
packages=
  apt-utils
  build-essential
  curl
  git
```

**Key Concepts**:

- **Section**: `[manager/cache-group]` format
- **Commands**: `pre`, `init`, `install`, `post` lifecycle hooks
- **Packages**: Multiline list with optional version constraints

### Generated Script Features

The generated `install.sh` script:

1. **Tier 1 Idempotency**: Computes SHA256 hash of manifest
    - Skips if unchanged (unless `--force`)
    - Stores hash in `~/.pkgm-demo.pkgm.state`

2. **Tier 2 Idempotency**: Per-manager inventory checks
    - Runs `apt list --installed` to detect already-installed packages
    - Only installs deltas (new packages)

3. **Return Codes**:
    - `0`: No work needed (manifest unchanged)
    - `1`: Error during installation
    - `2`: Work completed successfully

4. **Execution**: Runs pre/init/install/post commands in order

---

## Key Fixes Applied

### Issue 1: Recursive Template Fallback

**Problem**: `emit_install_sh()` → `render_template()` → `_render_format_fallback()` → `emit_install_sh()` = infinite recursion

**Solution**: Added `_emit_install_sh_direct()` function

- Checks if Jinja2 available and templates exist
- Falls back to direct script generation (no templates needed)
- Breaks the recursion cycle

### Issue 2: Package Name Parsing

**Problem**: Package names with trailing commas and backslashes weren't cleaned

- Example: `git, \` → stored as `git, \` instead of `git`

**Solution**: Enhanced `_parse_package_line()` to strip:

- Trailing backslashes (line continuations)
- Trailing commas (from comma-separated lists)

---

## Usage

### Build the Docker Image

```bash
docker build -f Dockerfile.pkg-manifest-demo -t demo-pkgm:latest .
```

**Expected Output**:

```
[pkg-manifest] Reading manifest: /opt/pkg-manifest/pkgs_sys.conf
[pkg-manifest] Parsing manifest into PKG_GRAPH...
[pkg-manifest] ✓ Parsed 1 package manager section(s)
[pkg-manifest] Generating installation script via emit_install_sh()...
[pkg-manifest] ✓ Generated 33 lines of bash script
[pkg-manifest] Executing generated installation script...
[pkg-manifest] ✓ Installation completed successfully (exit code: 0)
[pkg-manifest] Verifying installation...
```

### Run the Container

```bash
docker run --rm demo-pkgm:latest
```

The container will:

1. Parse `pkgs_sys.conf`
2. Generate an idempotent install script
3. Execute the script
4. Verify installation by listing packages

---

## Implementation Architecture

```
Dockerfile.pkg-manifest-demo
├── Copy gen.py (core generator)
├── Copy managers.json (registry)
├── Copy managers/*.sh (shell modules)
├── Copy templates/*.j2 (Jinja2 templates)
├── Copy pkgs_sys.conf (manifest)
└── Python Script:
    ├── parse_pkgm() → PKG_GRAPH
    ├── emit_install_sh() → bash script
    └── subprocess.run() → execute
        ├── apt-get update (pre)
        ├── apt-get install -y [28 packages] (install)
        └── apt-get clean (post)
```

---

## Files and Functions

### core Functions

| Function                    | Purpose                                 | Input      | Output                 |
| --------------------------- | --------------------------------------- | ---------- | ---------------------- |
| `parse_pkgm()`              | Parse manifest into graph               | INI string | PKG_GRAPH              |
| `emit_install_sh()`         | Generate install script                 | PKG_GRAPH  | Bash script (string)   |
| `_emit_install_sh_direct()` | Direct script generation (no templates) | PKG_GRAPH  | Bash script (string)   |
| `emit_dockerfile()`         | Generate Dockerfile                     | PKG_GRAPH  | Dockerfile (string)    |
| `emit_ansible_playbook()`   | Generate Ansible playbook               | PKG_GRAPH  | YAML playbook (string) |

### Data Structures

```python
@dataclass
class Package:
    name: str
    version: str = ""  # e.g., "[~=1.0]", "==2.3.4"

@dataclass
class Section:
    manager: str  # "apt", "pip", "brew", etc.
    cache_group: str
    packages: list[Package]
    commands: dict[str, str]  # {"pre": "...", "install": "..."}

@dataclass
class PKG_GRAPH:
    sections: dict[str, Section]
    metadata: dict[str, str]
    manager_deps: dict[str, list[str]]
```

---

## Testing and Validation

### Build Test

✅ Dockerfile successfully builds without errors
✅ All file paths resolve correctly
✅ parse_pkgm() successfully parses manifest
✅ emit_install_sh() generates valid bash script
✅ Generated script executes without errors

### Runtime Test

✅ Packages successfully installed
✅ State file created at `~/.pkgm-demo.pkgm.state`
✅ Subsequent runs skip installation (idempotent)
✅ Installation verification shows packages installed

---

## Troubleshooting

### Recursion Error

If you see `RecursionError: maximum recursion depth exceeded`:

- Ensure `_emit_install_sh_direct()` is called when templates unavailable
- Check that `emit_install_sh()` doesn't loop back to `render_template()`

### Missing Files

If build fails with "file not found":

- Verify `.files/pkg-manifest/` directory exists
- Check `.files/config/pkgs_sys.conf` is present
- Confirm `managers/` and `templates/` subdirectories exist

### Package Install Failures

If installation fails:

- Check that `apt-get update` is in the `pre` command
- Verify package names are valid (check `apt-cache search <pkg>`)
- Review the generated script saved at `/tmp/generated-install.sh`

---

## Advanced Usage

### Custom Manifest

Create a new manifest file and pass it to the Dockerfile:

```ini
[pip/base]
mode=multi
install=pip install --upgrade --user
packages=
  requests>=2.28.0
  pytest[extra]>=7.0
  black
```

### Filter by Tags

Manifest supports tag-based filtering:

```ini
# @tags: curl=base,networking build-essential=base,build
```

### Apply Lock File

Use lock files for reproducible installs:

```ini
[pip/frozen]
lock=requirements.lock
```

---

## References

- **pkg-manifest README**: `.files/pkg-manifest/README.md`
- **Test Suite**: `.files/pkg-manifest/tests/` (48 test cases)
- **Templates**: `.files/pkg-manifest/templates/` (6 Jinja2 templates)
- **Manager Scripts**: `.files/pkg-manifest/managers/*.sh` (shell modules)

---

## Summary

This Dockerfile demonstrates a production-ready workflow for:

1. Converting unified manifest files to installation scripts
2. Implementing two-tier idempotency (manifest + inventory)
3. Supporting multiple package managers in a single workflow
4. Generating deterministic, reproducible container images

The solution is **self-documenting** (manifest format is declarative), **extensible** (pluggable managers), and **fail-safe** (state tracking prevents duplicate work).
