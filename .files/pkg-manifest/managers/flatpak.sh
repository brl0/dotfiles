#!/bin/bash
# Flatpak Package Manager Module

install_packages() {
    local -a pkgs=("$@")
    local work_done=0
    local exit_code=0

    [[ ${#pkgs[@]} -eq 0 ]] && return 0

    if ! command -v flatpak &>/dev/null; then
        echo "[flatpak] Error: flatpak command not found" >&2
        return 1
    fi

    if [[ -n "${FLATPAK_INVENTORY_CMD:-}" ]]; then
        local -A installed
        while IFS= read -r line; do
            [[ -z "$line" ]] && continue
            installed["$line"]=1
        done < <(eval "$FLATPAK_INVENTORY_CMD" 2>/dev/null || true)

        local -a to_install
        for pkg in "${pkgs[@]}"; do
            local pkg_name="${pkg%%[*}"
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

    if [[ -n "${FLATPAK_PRE_CMD:-}" ]]; then
        eval "$FLATPAK_PRE_CMD" || exit_code=1
    fi

    if [[ $exit_code -eq 0 ]]; then
        local pkg_str=""
        for pkg in "${pkgs[@]}"; do
             local pkg_name="${pkg%%[*}"
             pkg_str="$pkg_str $pkg_name"
        done

        ${FLATPAK_INSTALL_CMD:-flatpak install -y} $pkg_str >/dev/null 2>&1 || exit_code=1
    fi

    if [[ -n "${FLATPAK_POST_CMD:-}" && $exit_code -eq 0 ]]; then
        eval "$FLATPAK_POST_CMD" || exit_code=1
    fi

    [[ $exit_code -ne 0 ]] && return 1
    [[ $work_done -eq 1 ]] && return 2 || return 0
}
