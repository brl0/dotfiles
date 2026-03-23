#!/bin/bash
# Docker Manager Module
# install_packages(packages_array) - Pull Docker images with idempotency support

install_packages() {
    local -a pkgs=("$@")
    local work_done=0
    local exit_code=0

    [[ ${#pkgs[@]} -eq 0 ]] && return 0

    if ! command -v docker &>/dev/null; then
        echo "[docker] Error: docker command not found" >&2
        return 1
    fi

    # Check for delta using inventory_cmd if provided
    if [[ -n "${DOCKER_INVENTORY_CMD:-}" ]]; then
        local -A installed
        
        while IFS= read -r line; do
            [[ -z "$line" ]] && continue
            installed["$line"]=1
            # Also register name without tag as ':latest'
            if [[ "$line" == *":latest" ]]; then
                local base_repo="${line%:latest}"
                installed["$base_repo"]=1
            fi
        done < <(eval "$DOCKER_INVENTORY_CMD" 2>/dev/null || true)

        local -a to_install
        for pkg in "${pkgs[@]}"; do
            local image_name
            if [[ "$pkg" == *"["* ]]; then
                local repo="${pkg%%[*}"
                local tag="${pkg#*[}"
                tag="${tag%]}"
                image_name="${repo}:${tag}"
            else
                image_name="$pkg"
            fi
            
            local check_name="$image_name"
            if [[ "$image_name" != *":"* ]]; then
               check_name="${image_name}:latest"
            fi
            
            if [[ -z "${installed[$check_name]:-}" && -z "${installed[$image_name]:-}" ]]; then
                to_install+=("$image_name")
            fi
        done

        [[ ${#to_install[@]} -eq 0 ]] && return 0
        pkgs=("${to_install[@]}")
        work_done=1
    else
        local -a formatted_pkgs
        for pkg in "${pkgs[@]}"; do
            if [[ "$pkg" == *"["* ]]; then
                local repo="${pkg%%[*}"
                local tag="${pkg#*[}"
                tag="${tag%]}"
                formatted_pkgs+=("${repo}:${tag}")
            else
                formatted_pkgs+=("$pkg")
            fi
        done
        pkgs=("${formatted_pkgs[@]}")
        work_done=1
    fi

    # Pre-install commands (not commonly used for docker pull but supported)
    if [[ -n "${DOCKER_PRE_CMD:-}" ]]; then
        eval "$DOCKER_PRE_CMD" || exit_code=1
    fi

    # Pull images
    if [[ $exit_code -eq 0 ]]; then
        for image in "${pkgs[@]}"; do
            ${DOCKER_INSTALL_CMD:-docker pull} "$image" >/dev/null || exit_code=1
        done
    fi

    # Post-install commands
    if [[ -n "${DOCKER_POST_CMD:-}" && $exit_code -eq 0 ]]; then
        eval "$DOCKER_POST_CMD" || exit_code=1
    fi

    [[ $exit_code -ne 0 ]] && return 1
    [[ $work_done -eq 1 ]] && return 2 || return 0
}
