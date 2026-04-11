#!/bin/bash
#
# Demo: Generate and run an installer script from pkg-manifest
#
# This script demonstrates the pkg-manifest system workflow:
# 1. Parse a .pkgm manifest file
# 2. Generate an idempotent install.sh script
# 3. Execute the generated installer
#
# USAGE:
#   ./demo-pkg-manifest-installer.sh [manifest_name] [dry-run]
#
# EXAMPLES:
#   # Install system packages from sys-packages.pkgm
#   ./demo-pkg-manifest-installer.sh sys-packages
#
#   # Dry-run: just show what would be installed (preview script)
#   ./demo-pkg-manifest-installer.sh sys-packages --preview
#
#   # Install Python packages
#   ./demo-pkg-manifest-installer.sh python-packages
#

set -euo pipefail

# ============================================================================
# Configuration
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PKG_MANIFEST_DIR="${SCRIPT_DIR}/.files/pkg-manifest"
CONFIG_DIR="${SCRIPT_DIR}/.files/config"
MANIFEST_NAME="${1:-sys-packages}"
PREVIEW_MODE="${2:-}"

# Ensure manifest has .pkgm extension
if [[ ! "$MANIFEST_NAME" =~ \.pkgm$ ]]; then
    MANIFEST_FILE="${MANIFEST_NAME}.pkgm"
else
    MANIFEST_FILE="$MANIFEST_NAME"
fi

MANIFEST_PATH="${CONFIG_DIR}/${MANIFEST_FILE}"

# ============================================================================
# Helper Functions
# ============================================================================

log_info() {
    echo "ℹ️  $*"
}

log_success() {
    echo "✅ $*"
}

log_error() {
    echo "❌ ERROR: $*" >&2
}

log_section() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  $*"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

check_dependencies() {
    local missing=()
    
    if ! command -v python3 &> /dev/null; then
        missing+=("python3")
    fi
    
    if [[ ! -f "${PKG_MANIFEST_DIR}/gen.py" ]]; then
        missing+=("${PKG_MANIFEST_DIR}/gen.py")
    fi
    
    if (( ${#missing[@]} > 0 )); then
        log_error "Missing dependencies:"
        printf '  - %s\n' "${missing[@]}"
        return 1
    fi
    
    log_success "All dependencies found"
}

show_manifest_info() {
    log_section "Manifest Information"
    
    if [[ ! -f "$MANIFEST_PATH" ]]; then
        log_error "Manifest file not found: $MANIFEST_PATH"
        return 1
    fi
    
    log_info "Manifest: $MANIFEST_FILE"
    log_info "Full path: $MANIFEST_PATH"
    log_info "Size: $(wc -c < "$MANIFEST_PATH" | numfmt --to=iec-i --suffix=B 2>/dev/null || echo "$(wc -c < "$MANIFEST_PATH") bytes")"
    log_info ""
    log_info "Content preview:"
    echo "---"
    head -20 "$MANIFEST_PATH"
    if [[ $(wc -l < "$MANIFEST_PATH") -gt 20 ]]; then
        echo "... ($(wc -l < "$MANIFEST_PATH") total lines)"
    fi
    echo "---"
}

generate_installer() {
    log_section "Generating Installer Script"
    
    # Use Python to parse manifest and generate install.sh
    python3 << 'PYTHON_END'
import sys
sys.path.insert(0, '$PKG_MANIFEST_DIR')

from pathlib import Path
from gen import parse_pkgm, emit_install_sh

manifest_path = "$MANIFEST_PATH"
manifest_name = "$MANIFEST_FILE".replace('.pkgm', '')

try:
    # Read and parse manifest
    with open(manifest_path) as f:
        manifest_content = f.read()
    
    print("📦 Parsing manifest...", file=sys.stderr)
    graph = parse_pkgm(manifest_content)
    
    # Generate install script
    print("📦 Generating install.sh...", file=sys.stderr)
    script = emit_install_sh(graph, manifest_name)
    
    # Output the script to stdout
    print(script)
    
except Exception as e:
    print(f"❌ Error: {type(e).__name__}: {e}", file=sys.stderr)
    sys.exit(1)
PYTHON_END
}

preview_installer() {
    log_section "Preview: Generated Installer Script"
    
    local install_script
    install_script=$(generate_installer 2>&1 | grep -v "^📦") || {
        log_error "Failed to generate installer script"
        return 1
    }
    
    log_info "First 50 lines of generated installer:"
    echo "---"
    echo "$install_script" | head -50
    echo "..."
    echo "--- ($(echo "$install_script" | wc -l) total lines)"
    
    log_info ""
    log_info "Script includes:"
    if echo "$install_script" | grep -q "install_apt"; then
        log_info "  · apt package manager installation"
    fi
    if echo "$install_script" | grep -q "install_brew"; then
        log_info "  · brew package manager installation"
    fi
    if echo "$install_script" | grep -q "install_pip"; then
        log_info "  · pip package manager installation"
    fi
}

run_installer() {
    log_section "Running Installer Script"
    
    local install_script
    install_script=$(generate_installer 2>&1 | grep -v "^📦") || {
        log_error "Failed to generate installer script"
        return 1
    }
    
    log_info "Executing generated installer..."
    log_info ""
    
    # Execute the generated script
    if bash -c "$install_script"; then
        log_success "Installation completed successfully"
        return 0
    else
        local exit_code=$?
        log_error "Installation completed with exit code $exit_code"
        return $exit_code
    fi
}

show_help() {
    cat << 'EOF'
Usage: ./demo-pkg-manifest-installer.sh [OPTIONS] [manifest_name]

Description:
  Demonstrates the pkg-manifest system by parsing a manifest file,
  generating an installer script, and running it.

Options:
  manifest_name    Name of the manifest to use (default: sys-packages)
                   Examples: sys-packages, python-packages, brew-packages

  --preview       Show a preview of the generated installer without running it
  --help          Show this help message

Environment Variables:
  PKG_MANIFEST_DIR Directory containing gen.py (auto-detected from script location)
  CONFIG_DIR       Directory containing .pkgm manifests (auto-detected)

Examples:
  # Preview system packages installer
  ./demo-pkg-manifest-installer.sh sys-packages --preview

  # Install system packages
  ./demo-pkg-manifest-installer.sh sys-packages

  # Install python packages (with custom directory)
  ./demo-pkg-manifest-installer.sh python-packages

  # Get help
  ./demo-pkg-manifest-installer.sh --help

How pkg-manifest works:
  1. Define packages in .pkgm format (INI-style with [manager/cache-group])
  2. Parse manifest with gen.parse_pkgm()
  3. Generate shell script with gen.emit_install_sh()
  4. Execute the generated script for idempotent installation

EOF
}

# ============================================================================
# Main
# ============================================================================

main() {
    case "${1:-}" in
        --help)
            show_help
            return 0
            ;;
        --preview)
            MANIFEST_NAME="${PREVIEW_MODE:-sys-packages}"
            PREVIEW_MODE="--preview"
            ;;
    esac
    
    if [[ "$PREVIEW_MODE" == "--preview" ]]; then
        log_section "pkg-manifest Installer Demo (PREVIEW MODE)"
    else
        log_section "pkg-manifest Installer Demo"
    fi
    
    check_dependencies || return 1
    show_manifest_info || return 1
    
    if [[ "$PREVIEW_MODE" == "--preview" ]]; then
        preview_installer
    else
        run_installer
    fi
}

main "$@"
