#!/bin/bash
# PIP Package Manager Module
# install_packages(packages_array) - Install Python pip packages with idempotency support

install_packages() {
    local -a pkgs=("$@")
    local work_done=0
    local exit_code=0

    [[ ${#pkgs[@]} -eq 0 ]] && return 0

    # Determine pip command and environment
    local pip_cmd="pip"
    local use_venv=0

    if [[ -n "${PIP_VENV:-}" ]]; then
        if [[ ! -d "$PIP_VENV" ]]; then
            python3 -m venv "$PIP_VENV" >/dev/null 2>&1 || exit_code=1
        fi
        if [[ $exit_code -eq 0 ]]; then
            pip_cmd="${PIP_VENV}/bin/pip"
            use_venv=1
        fi
    fi

    # Check for delta using inventory_cmd if provided
    if [[ -n "${PIP_INVENTORY_CMD:-}" && $exit_code -eq 0 ]]; then
        local -A installed

        # Execute inventory command to get installed packages
        while IFS='== ' read -r pkg_name version; do
            pkg_name="${pkg_name%% *}"
            [[ -z "$pkg_name" ]] && continue
            installed["$pkg_name"]=1
        done < <(eval "$PIP_INVENTORY_CMD" 2>/dev/null || true)

        # Filter to only packages not installed
        local -a to_install
        for pkg in "${pkgs[@]}"; do
            # Strip extras and version constraints: package[extra1,extra2]>=1.0
            local pkg_name="${pkg%%[*}"
            pkg_name="${pkg_name%%>*}"
            pkg_name="${pkg_name%%<*}"
            pkg_name="${pkg_name%%=*}"
            pkg_name="${pkg_name%%~*}"

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
    if [[ -n "${PIP_PRE_CMD:-}" && $exit_code -eq 0 ]]; then
        eval "$PIP_PRE_CMD" || exit_code=1
    fi

    # Upgrade pip if in venv
    if [[ $use_venv -eq 1 && $exit_code -eq 0 ]]; then
        "$pip_cmd" install --upgrade pip setuptools wheel >/dev/null 2>&1 || exit_code=1
    fi

    # Install packages
    if [[ $exit_code -eq 0 ]]; then
        local pip_args=()

        # Add --index-url if specified
        if [[ -n "${PIP_INDEX_URL:-}" ]]; then
            pip_args+=("--index-url" "$PIP_INDEX_URL")
        fi

        # Build package list (extras and constraints preserved as-is)
        local pkg_str="${pkgs[*]}"

        "$pip_cmd" install "${pip_args[@]}" $pkg_str >/dev/null 2>&1 || exit_code=1
    fi

    # Post-install commands
    if [[ -n "${PIP_POST_CMD:-}" && $exit_code -eq 0 ]]; then
        eval "$PIP_POST_CMD" || exit_code=1
    fi

    [[ $exit_code -ne 0 ]] && return 1
    [[ $work_done -eq 1 ]] && return 2 || return 0
}
