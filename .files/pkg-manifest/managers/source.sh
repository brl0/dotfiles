#!/bin/bash
# Source Package Manager Module
# install_packages(packages_array) - Download, build, and record source tarballs

install_packages() {
    local -a pkgs=("$@")
    local work_done=0
    local exit_code=0
    local install_dir="$HOME/.pkgm/source_installs"
    local cache_dir="$HOME/.pkgm/cache/source"

    [[ ${#pkgs[@]} -eq 0 ]] && return 0

    mkdir -p "$install_dir" "$cache_dir"

    if ! command -v curl &>/dev/null || ! command -v tar &>/dev/null; then
        echo "[source] Error: curl and tar are required" >&2
        return 1
    fi

    local -a to_install
    
    # Delta detection
    if [[ -n "${SOURCE_INVENTORY_CMD:-}" ]]; then
        for pkg in "${pkgs[@]}"; do
            local pkg_name="${pkg%%[*}"
            if [[ ! -f "$install_dir/$pkg_name" ]]; then
                to_install+=("$pkg")
            fi
        done
        [[ ${#to_install[@]} -eq 0 ]] && return 0
        pkgs=("${to_install[@]}")
        work_done=1
    else
        work_done=1
    fi

    if [[ -n "${SOURCE_PRE_CMD:-}" ]]; then
        eval "$SOURCE_PRE_CMD" || exit_code=1
    fi

    if [[ $exit_code -eq 0 ]]; then
        for pkg in "${pkgs[@]}"; do
            local pkg_name="${pkg%%[*}"
            local url="${pkg#*[}"
            url="${url%]}"
            
            if [[ "$url" == "$pkg_name" || -z "$url" ]]; then
                echo "[source] Error: Package $pkg_name requires a URL variant like pkg[http...]" >&2
                exit_code=1
                continue
            fi
            
            echo "[source] Downloading & building $pkg_name..."
            
            local archive_path="$cache_dir/${pkg_name}.tar.gz"
            local extract_dir="$cache_dir/${pkg_name}_extract"
            
            rm -rf "$extract_dir"
            mkdir -p "$extract_dir"
            
            if ! curl -sL "$url" -o "$archive_path"; then
                echo "[source] Failed to download $url" >&2
                exit_code=1
                continue
            fi
            
            if ! tar -xzf "$archive_path" -C "$extract_dir" --strip-components=1 2>/dev/null; then
                 if ! tar -xzf "$archive_path" -C "$extract_dir"; then
                     echo "[source] Failed to extract $archive_path. Ensure it is a valid gzip tarball." >&2
                     exit_code=1
                     continue
                 fi
            fi
            
            (
                cd "$extract_dir" || exit 1
                if [[ -x "./configure" ]]; then
                    ./configure --prefix="$HOME/.local" >/dev/null
                fi
                if [[ -f "Makefile" || -f "makefile" ]]; then
                    make >/dev/null && make install >/dev/null
                else
                    if [[ -x "./$pkg_name" ]]; then
                        mkdir -p "$HOME/.local/bin"
                        cp "./$pkg_name" "$HOME/.local/bin/"
                    fi
                fi
            )
            local build_code=$?
            
            if [[ $build_code -eq 0 ]]; then
                touch "$install_dir/$pkg_name"
                echo "[source] $pkg_name installed successfully."
            else
                echo "[source] Build/Install failed for $pkg_name" >&2
                exit_code=1
            fi
        done
    fi

    if [[ -n "${SOURCE_POST_CMD:-}" && $exit_code -eq 0 ]]; then
        eval "$SOURCE_POST_CMD" || exit_code=1
    fi

    [[ $exit_code -ne 0 ]] && return 1
    [[ $work_done -eq 1 ]] && return 2 || return 0
}
