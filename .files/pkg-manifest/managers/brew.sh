#!/bin/bash
# Homebrew Package Manager Module
# install_packages(packages_array) - Install Homebrew packages with idempotency support

install_packages() {
    local -a pkgs=("$@")
    local work_done=0
    local exit_code=0

    [[ ${#pkgs[@]} -eq 0 ]] && return 0

    # Detect macOS
    if [[ "$OSTYPE" != "darwin"* ]]; then
        echo "Error: Homebrew module requires macOS" >&2
        return 1
    fi

    # Check for delta using inventory_cmd if provided
    if [[ -n "${BREW_INVENTORY_CMD:-}" ]]; then
        local -A installed

        # Execute inventory command to get installed packages
        while IFS= read -r line; do
            # Parse package name (first field or package@version)
            local pkg_name="${line%% *}"
            pkg_name="${pkg_name%@*}"
            [[ -z "$pkg_name" ]] && continue
            installed["$pkg_name"]=1
        done < <(eval "$BREW_INVENTORY_CMD" 2>/dev/null || true)

        # Filter to only packages not installed
        local -a to_install
        for pkg in "${pkgs[@]}"; do
            local pkg_name="${pkg%%[*}"  # Strip version constraint
            if [[ -z "${installed[$pkg_name]:-}" ]]; then
                to_install+=("$pkg")
            fi
        done

        [[ ${#to_install[@]} -eq 0 ]] && return 0
        pkgs=("${to_install[@]}")
        work_done=1
    else
        work_done=1
    fi

    # Pre-install commands
    if [[ -n "${BREW_PRE_CMD:-}" ]]; then
        eval "$BREW_PRE_CMD" || exit_code=1
    fi

    # Install packages
    if [[ $exit_code -eq 0 ]]; then
        local pkg_str=""
        for pkg in "${pkgs[@]}"; do
            # Handle version constraints: package[~=1.0] → package@1.0
            pkg="${pkg//[/=}"
            pkg="${pkg//]/}"
            pkg="${pkg//[=/@}"  # [=1.0 → @1.0
            pkg_str="$pkg_str $pkg"
        done

        brew install $pkg_str >/dev/null 2>&1 || exit_code=1
    fi

    # Post-install commands
    if [[ -n "${BREW_POST_CMD:-}" && $exit_code -eq 0 ]]; then
        eval "$BREW_POST_CMD" || exit_code=1
    fi

    [[ $exit_code -ne 0 ]] && return 1
    [[ $work_done -eq 1 ]] && return 2 || return 0
}
