# pkg-manifest Installer Demo Scripts

Two simple scripts to demonstrate how to use the pkg-manifest system to generate installer scripts for packages specified in `.files/config` manifest files.

## Files

- **`demo-pkg-manifest-installer.sh`** - Shell script demonstrator (bash)
- **`demo-pkg-manifest-installer.py`** - Python wrapper for better UX

## Quick Start

### Using the Shell Script

```bash
# Preview the generated installer without running it
./demo-pkg-manifest-installer.sh sys-packages --preview

# Generate and run the installer
./demo-pkg-manifest-installer.sh sys-packages

# Install python packages
./demo-pkg-manifest-installer.sh python-packages

# Get help
./demo-pkg-manifest-installer.sh --help
```

### Using the Python Script

```bash
# List all available manifests
python3 demo-pkg-manifest-installer.py --list

# Show information about a manifest
python3 demo-pkg-manifest-installer.py --info sys-packages

# Preview the installer without running it
python3 demo-pkg-manifest-installer.py --preview sys-packages

# Generate and run the installer
python3 demo-pkg-manifest-installer.py sys-packages

# Dry-run mode (show what would happen)
python3 demo-pkg-manifest-installer.py --dry-run sys-packages

# Get help
python3 demo-pkg-manifest-installer.py --help
```

## How It Works

The pkg-manifest system is a convention-driven package management framework:

### 1. **Manifest Format** (`.pkgm` files)

Manifest files define packages in INI-style format:

```ini
[apt/base]
mode=multi
pre=apt-get update
post=apt-get clean && rm -rf /var/lib/apt/lists/*
packages = \
  build-essential, \
  curl, \
  git, \
  ...
```

### 2. **Generator** (`gen.py`)

The generator tool parses manifest files and generates:

- **Install scripts** (idempotent shell scripts)
- **Dockerfiles** (optimized for layer caching)
- **Ansible playbooks** (infrastructure automation)

### 3. **Execution**

The generated installer script is atomic and idempotent:

- Can be run multiple times safely
- Embeds manifest hash for verification
- Supports per-manager inventory queries

## Available Manifests

Check what's available in `.files/config/`:

```bash
python3 demo-pkg-manifest-installer.py --list
```

Common manifests:

- `sys-packages.pkgm` - System utilities, build tools, CLI apps
- `python-packages.pkgm` - Python packages via pip
- `brew-packages.pkgm` - Homebrew packages (macOS)
- `utility-packages.pkgm` - Utility packages

## Workflow Example

```bash
# 1. Preview what will be installed
python3 demo-pkg-manifest-installer.py --preview sys-packages

# 2. Check manifest details
python3 demo-pkg-manifest-installer.py --info sys-packages

# 3. Dry-run (simulate without actually running)
python3 demo-pkg-manifest-installer.py --dry-run sys-packages

# 4. Execute the installer
python3 demo-pkg-manifest-installer.py sys-packages
```

## Key Features

### Shell Script Features

- ✅ Dependency checking (python3, gen.py)
- ✅ Manifest validation
- ✅ Automatic script generation
- ✅ Human-readable output
- ✅ Helper functions for logging (`_log`, `_success`, `_error`)

### Python Script Features

- ✅ List all available manifests
- ✅ Show manifest information and previews
- ✅ Dry-run mode
- ✅ Verbose output option
- ✅ Better error handling
- ✅ Script analysis (managers, line count, etc.)
- ✅ Human-readable file sizes
- ✅ Graceful keyboard interrupt handling

## Configuration

Both scripts auto-detect the configuration directory (`.files/config`), but you can override it:

### Shell Script

```bash
# Would require editing the script to change CONFIG_DIR
```

### Python Script

```bash
python3 demo-pkg-manifest-installer.py --config-dir /custom/path sys-packages
```

## Troubleshooting

### "Manifest file not found"

- Check that the manifest exists: `ls -la .files/config/*.pkgm`
- Ensure you're running from the dotfiles directory

### "python3: command not found"

- Install Python 3: `apt-get install python3` (Ubuntu/Debian)
- Or check your PATH: `which python3`

### "gen.py not found"

- Verify the path: `.files/pkg-manifest/gen.py`
- Run from the dotfiles root directory

### Permission denied

- Make scripts executable: `chmod +x demo-pkg-manifest-installer.*`

## Understanding the Generated Script

The generated install script includes:

- Manifest hash for idempotency
- Per-manager installation functions
- Optional inventory queries (for drift detection)
- Pre/post hooks per manager
- Error handling and logging

Example generated script structure:

```bash
#!/bin/bash
# Generated from: sys-packages.pkgm
# Manifest hash: abc123...

# Manager modules
install_apt() { ... }
install_brew() { ... }
install_pip() { ... }

# Main execution
"$@"
```

## Integration with CI/CD

The generated scripts can be integrated into:

- **Docker builds** - Copy manifest, generate, and run in Dockerfile
- **GitHub Actions** - Run in matrix jobs for different package managers
- **Ansible** - Use generated playbooks for configuration management
- **Shell scripts** - Embed or source generated scripts

Example Docker integration:

```dockerfile
COPY .files/config/sys-packages.pkgm /tmp/
RUN cd /tmp && \
    python3 gen.py --input sys-packages.pkgm --output install.sh && \
    bash install.sh
```

## Resources

- **Manifest design**: See `plan-artifactDrivenPackageSystem.prompt.md`
- **Generator source**: `.files/pkg-manifest/gen.py`
- **Existing manifests**: `.files/config/*.pkgm`
- **Manager registry**: `.files/pkg-manifest/managers.json`
