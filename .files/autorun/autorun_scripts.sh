#!/bin/bash
#
# autorun_scripts.sh
# Helper to source supplementary startup scripts.
# Input sources:
#   1) Explicit file argument (list of scripts to source)
#   2) Piped stdin
#   3) Default autorun list file
#
# Path handling:
#   - Absolute paths are used as-is.
#   - Relative paths are interpreted relative to the grandparent
#     of the directory containing this script.
#

# --- Banner: script start ---
script_path=$(realpath "${BASH_SOURCE[0]}")
script_name=$(basename "$script_path")
script_dir=$(dirname "$script_path")
grandparent_dir=$(dirname "$(dirname "$script_dir")")

start_time=$(date +%s)
start_human=$(date +"%Y-%m-%d %H:%M:%S")

echo "============================================================"
echo " Script: $script_path"
echo " Base  : $grandparent_dir"
echo " Start : $start_human"
echo "============================================================"
echo

# Function: source each script listed in a file or stdin
source_files() {
    local input_file="$1"

    # Choose input source: file or stdin
    if [[ -n "$input_file" ]]; then
        if [[ ! -r "$input_file" ]]; then
            echo "!!! Cannot read input file: $input_file"
            return 1
        fi
        exec 3<"$input_file"
        echo ">>> Reading script list from file: $input_file"
    else
        exec 3<&0
        echo ">>> Reading script list from stdin"
    fi

    # Read each line (script path) from input
    while IFS= read -r script <&3; do
        # Skip empty lines and comments
        [[ -z "$script" || "$script" =~ ^[[:space:]]*$ || "$script" =~ ^[[:space:]]*# ]] && continue

        # Trim leading/trailing whitespace
        script="${script#"${script%%[![:space:]]*}"}"
        script="${script%"${script##*[![:space:]]}"}"

        # Determine full path:
        # - Absolute: use as-is
        # - Relative: resolve against grandparent_dir
        local full_path="$script"
        if [[ "$script" != /* ]]; then
            full_path="$grandparent_dir/$script"
        fi

        echo "Script: $script"
        echo "Full  : $full_path"

        if [[ -f "$full_path" ]]; then
            echo ">>> Running: $full_path"
            # shellcheck disable=SC1090
            source "$full_path"
            echo ">>> Finished: $full_path"
        else
            echo "!!! File not found: $full_path"
        fi
    done
    exec 3<&-
    echo
}

# --- Input handling ---
if [[ -n "$1" ]]; then
    # Case 1: explicit file argument
    if [[ -f "$1" ]]; then
        echo ">>> Argument provided. Using script list: $1"
        source_files "$1"
    else
        echo "!!! File not found: $1"
    fi
elif [[ ! -t 0 ]]; then
    # Case 2: piped input
    source_files
else
    # Case 3: default autorun file
    default_file="$HOME/dotfiles/.files/config/autorun.txt"
    echo ">>> No args or stdin provided. Using default: $default_file"
    source_files "$default_file"
fi

# --- Banner: script end ---
end_time=$(date +%s)
end_human=$(date +"%Y-%m-%d %H:%M:%S")
duration=$((end_time - start_time))

echo "============================================================"
echo " Script: $script_name"
echo " End   : $end_human"
echo " Duration: ${duration}s"
echo "============================================================"
