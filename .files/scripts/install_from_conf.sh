#!/bin/bash

sect="----------------------------------------"

alias pf=printf

sect_cmd="printf \"\\n%s\\n\" \"$sect\""

alias print_section='mkalias_section'
function mkalias_section() { eval "$sect_cmd"; }
alias p_sect='mkalias_section'

default_shell="/bin/bash -c"

install_from_conf() {
    local conf_file="$1"
    local current_section=""
    local install_command=""
    local install_mode=""
    local shell="$default_shell"
    local packages=()
    local in_packages=0

    if [[ ! -f "$conf_file" ]]; then
        echo "Configuration file not found: $conf_file"
        exit 1
    fi

    process_section() {
        if [[ -n "$current_section" ]]; then
            echo $sect
            echo "Processing section [$current_section]..."
            echo $sect
        fi

        if [[ -n "$install_command" ]]; then
            if [[ ${#packages[@]} -gt 0 ]]; then
                echo $sect
                echo "Installing packages for [$current_section]..."
                echo $sect

                if [[ "$install_mode" == "multi" ]]; then
                    echo $sect
                    echo $shell "$install_command ${packages[*]}"
                    echo $sect
                    $shell "$install_command ${packages[*]}"
                else
                    for pkg_line in "${packages[@]}"; do
                        echo $sect
                        echo $shell "$install_command $pkg_line"
                        echo $sect
                        $shell "$install_command $pkg_line"
                    done
                fi
            else
                echo $sect
                echo "Running command for [$current_section]..."
                echo $shell "$install_command"
                echo $sect
                $shell "$install_command"
            fi
        fi
    }

    while IFS= read -r line || [[ -n $line ]]; do
        line=$(echo "$line" | sed 's/[[:space:]]*#.*//; s/^ *//; s/ *$//')
        [ -z "$line" ] && continue

        if [[ "$line" =~ ^\[.*\]$ ]]; then
            process_section
            current_section="${BASH_REMATCH[0]}"
            install_command=""
            install_mode=""
            shell="$default_shell"
            packages=()
            in_packages=0
        elif [[ "$line" =~ ^shell=(.*)$ ]]; then
            shell="${BASH_REMATCH[1]}"
            in_packages=0
        elif [[ "$line" == "packages:" ]]; then
            in_packages=1
        elif [[ "$line" =~ ^command=(.*)$ ]]; then
            install_command="${BASH_REMATCH[1]}"
            in_packages=0
        elif [[ "$line" =~ ^mode=(.*)$ ]]; then
            install_mode="${BASH_REMATCH[1]}"
            in_packages=0
        elif [[ "$in_packages" -eq 1 ]]; then
            packages+=("$line")
        fi
    done < "$conf_file"

    process_section
}

if [[ -n "$1" ]]; then
    install_from_conf "$1"
fi

exit 0
