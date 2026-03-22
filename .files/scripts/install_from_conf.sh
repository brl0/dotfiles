#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(dirname "$(realpath "$0")")"
PARENT_DIR="$(dirname "$SCRIPT_DIR")"
DOTFILES_DIR="$(dirname "$PARENT_DIR")"

sect="========================================"

# Default shell binary and arguments
default_shell_bin="/bin/bash"
default_shell_args=(-lc)

# Global log file (set in install_from_conf)
log_file=""

# Print a section banner with optional text and timestamp
section_banner() {
    local text="${1:-}"
    local ts
    ts="$(date -Iseconds)"
    if [[ -n $text ]]; then
        printf "\n%s\n[%s] %s\n%s\n" "$sect" "$ts" "$text" "$sect"
    else
        printf "\n%s\n[%s]\n%s\n" "$sect" "$ts" "$sect"
    fi
}

# Print an end banner with completion time and duration
section_end_banner() {
    local text="${1:-Section completed}"
    local start_time="$2"
    local end_time
    end_time="$(date -Iseconds)"
    local duration
    duration=$(($(date -d "$end_time" +%s) - $(date -d "$start_time" +%s)))
    printf "\n%s\n[%s] %s\nDuration: %ss\n%s\n" "$sect" "$end_time" "$text" "$duration" "$sect"
}

# Normalize command string: strip outer quotes if both exist
normalize_command() {
    local cmd="$1"
    if [[ ($cmd == \"*\" && $cmd == *\") || ($cmd == \'*\' && $cmd == *\') ]]; then
        cmd="${cmd:1:-1}"
    fi
    printf "\n%s\n" "$cmd"
}

# Safely run a command string inside the chosen shell
run_command() {
    local shell_bin="$1"
    shift
    local -a shell_args=("$@")
    local cmd="${shell_args[-1]}"
    ncmd="$(normalize_command "$cmd")"
    unset 'shell_args[-1]' # remove the command from args
    printf "\nRunning command: %s\n" "$ncmd"
    fullcmd="\"$shell_bin\" ${shell_args[*]} \"$ncmd\""
    printf "Full command: $fullcmd"
    eval "$fullcmd"
}

# Process the current section: run commands in order
process_section() {
    local current_section="$1"
    local install_mode="$2"
    local shell_bin="$3"
    shift 3
    local -a shell_args=("$1")
    shift
    local packages=("$@")

    [[ -n $current_section ]] || return 0

    local start_time
    start_time="$(date -Iseconds)"
    section_banner "Processing section $current_section (start)"

    # Run commands in order
    for key in pre init install post command; do
        local cmd="${section_cmds[$key]:-}"
        [[ -z $cmd ]] && continue

        section_banner "${key^} command for $current_section: $cmd"

        if [[ $key == "install" || $key == "command" ]]; then
            if [[ ${#packages[@]} -gt 0 ]]; then
                if [[ $install_mode == "multi" ]]; then
                    local joined="${packages[*]}"
                    run_command "$shell_bin" "${shell_args[@]}" "$cmd $joined"
                else
                    for pkg in "${packages[@]}"; do
                        run_command "$shell_bin" "${shell_args[@]}" "$cmd $pkg"
                    done
                fi
            else
                run_command "$shell_bin" "${shell_args[@]}" "$cmd"
            fi
        else
            run_command "$shell_bin" "${shell_args[@]}" "$cmd"
        fi
    done

    section_end_banner "Section $current_section completed" "$start_time"
}

install_from_conf() {
    local conf_file="$1"
    local current_section=""
    declare -A section_cmds=()
    local install_mode=""
    local shell_bin="$default_shell_bin"
    local -a shell_args=("${default_shell_args[@]}")
    local packages=()
    local in_packages=0
    local in_command=0
    local current_key=""

    # Set up logging
    local ts
    ts="$(date +%Y%m%dT%H%M%S)"
    local base
    base="$(basename "$conf_file" .conf)"
    mkdir -p "$DOTFILES_DIR/logs"
    log_file="$DOTFILES_DIR/logs/${base}-${ts}.log"
    exec > >(tee -a "$log_file") 2>&1

    [[ -f $conf_file ]] || {
        echo "Configuration file not found: $conf_file"
        exit 1
    }

    while IFS= read -r line || [[ -n $line ]]; do
        # Strip comments and trim whitespace
        line="${line%%#*}"
        line="${line#"${line%%[![:space:]]*}"}"
        line="${line%"${line##*[![:space:]]}"}"
        [[ -z $line ]] && continue

        if [[ $line =~ ^\[.*\]$ ]]; then
            process_section "$current_section" "$install_mode" "$shell_bin" "${shell_args[@]}" "${packages[@]}"
            current_section="${BASH_REMATCH[0]}"
            section_cmds=() # reset commands
            install_mode=""
            shell_bin="$default_shell_bin"
            shell_args=("${default_shell_args[@]}")
            packages=()
            in_packages=0
            in_command=0
            current_key=""
        elif [[ $line =~ ^shell=(.*)$ ]]; then
            read -ra parts <<<"${BASH_REMATCH[1]}"
            shell_bin="${parts[0]}"
            shell_args=("${parts[@]:1}")
            in_packages=0
            in_command=0
        elif [[ $line == "packages:" ]]; then
            in_packages=1
            in_command=0
        elif [[ $line =~ ^(pre|init|install|post|command)=(.*)$ ]]; then
            local key="${BASH_REMATCH[1]}"
            local cmd_part
            cmd_part="$(normalize_command "${BASH_REMATCH[2]}")"
            if [[ -n ${section_cmds[$key]:-} ]]; then
                section_cmds[$key]+=$'\n'"$cmd_part"
            else
                section_cmds[$key]="$cmd_part"
            fi
            in_packages=0
            in_command=0
        elif [[ $line =~ ^(pre|init|install|post|command):$ ]]; then
            current_key="${BASH_REMATCH[1]}"
            in_command=1
            in_packages=0
        elif [[ $line =~ ^mode=(.*)$ ]]; then
            install_mode="${BASH_REMATCH[1]}"
            in_packages=0
            in_command=0
        elif [[ $in_packages -eq 1 ]]; then
            packages+=("$line")
        elif [[ $in_command -eq 1 ]]; then
            local cmd_part
            cmd_part="$(normalize_command "$line")"
            if [[ -n ${section_cmds[$current_key]:-} ]]; then
                section_cmds[$current_key]+=$'\n'"$cmd_part"
            else
                section_cmds[$current_key]="$cmd_part"
            fi
        fi
    done <"$conf_file"

    process_section "$current_section" "$install_mode" "$shell_bin" "${shell_args[@]}" "${packages[@]}"
}

[[ -n ${1-} ]] && install_from_conf "$1"
