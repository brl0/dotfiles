#!/bin/bash
# Snap Package Manager Module

install_packages() {
    local -a pkgs=("$@")
    local work_done=0
    local exit_code=0

    [[ ${#pkgs[@]} -eq 0 ]] && return 0

    if ! command -v snap &>/dev/null; then
        echo "[snap] Error: snap command not found" >&2
        return 1
    fi

    if [[ -n "${SNAP_INVENTORY_CMD:-}" ]]; then
        local -A installed
        while IFS= read -r line; do
            [[ -z "$line" ]] && continue
            installed["$line"]=1
        done < <(eval "$SNAP_INVENTORY_CMD" 2>/dev/null || true)

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

    if [[ -n "${SNAP_PRE_CMD:-}" ]]; then
        eval "$SNAP_PRE_CMD" || exit_code=1
    fi

    if [[ $exit_code -eq 0 ]]; then
        local pkg_str=""
        for pkg in "${pkgs[@]}"; do
             # Snap supports channels via flags e.g. --classic or --channel=edge
             local pkg_name="${pkg%%[*}"
             local channel="${pkg#*[}"
             channel="${channel%]}"
             if [[ "$channel" == "$pkg_name" || -z "$channel" ]]; then
                 pkg_str="$pkg_str $pkg_name"
             else
                 pkg_str="$pkg_str $pkg_name $channel"
             fi
        done

        ${SNAP_INSTALL_CMD:-sudo snap install} $pkg_str >/dev/null 2>&1 || exit_code=1
    fi

    if [[ -n "${SNAP_POST_CMD:-}" && $exit_code -eq 0 ]]; then
        eval "$SNAP_POST_CMD" || exit_code=1
    fi

    [[ $exit_code -ne 0 ]] && return 1
    [[ $work_done -eq 1 ]] && return 2 || return 0
}
