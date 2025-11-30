#!/bin/bash
set -euo pipefail

sect="----------------------------------------"
print_section() { printf "\n%s\n" "$sect"; }

default_shell="/bin/bash -lc"

install_from_conf() {
    local conf_file="$1"
    local current_section=""
    local install_command=""
    local install_mode=""
    local shell="$default_shell"
    local packages=()
    local in_packages=0

    [[ -f $conf_file ]] || {
        echo "Configuration file not found: $conf_file"
        exit 1
    }

    process_section() {
        [[ -n $current_section ]] && {
            print_section
            echo "Processing section [$current_section]..."
            print_section
        }

        [[ -n $install_command ]] || return 0

        if [[ ${#packages[@]} -gt 0 ]]; then
            print_section
            echo "Installing packages for [$current_section]..."
            print_section
            if [[ $install_mode == "multi" ]]; then
                $shell "$install_command ${packages[*]}"
            else
                for pkg in "${packages[@]}"; do
                    $shell "$install_command $pkg"
                done
            fi
        else
            print_section
            echo "Running command for [$current_section]..."
            print_section
            $shell "$install_command"
        fi
    }

    while IFS= read -r line || [[ -n $line ]]; do
        # Strip comments outside quotes (simple heuristic)
        line=$(echo "$line" | sed 's/[[:space:]]*#.*//; s/^ *//; s/ *$//')
        [[ -z $line ]] && continue

        if [[ $line =~ ^\[.*\]$ ]]; then
            process_section
            current_section="${BASH_REMATCH[0]}"
            install_command=""
            install_mode=""
            shell="$default_shell"
            packages=()
            in_packages=0
        elif [[ $line =~ ^shell=(.*)$ ]]; then
            shell="${BASH_REMATCH[1]}"
            in_packages=0
        elif [[ $line == "packages:" ]]; then
            in_packages=1
        elif [[ $line =~ ^command=(.*)$ ]]; then
            install_command="${BASH_REMATCH[1]}"
            in_packages=0
        elif [[ $line =~ ^mode=(.*)$ ]]; then
            install_mode="${BASH_REMATCH[1]}"
            in_packages=0
        elif [[ $in_packages -eq 1 ]]; then
            packages+=("$line")
        fi
    done <"$conf_file"

    process_section
}

[[ -n ${1-} ]] && install_from_conf "$1"
