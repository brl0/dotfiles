#!/bin/bash

# --- Banner: script start ---
script_path=$(realpath "${BASH_SOURCE[0]}")
script_name=$(basename "$script_path")
script_dir=$(dirname "$script_path")
grandparent_dir=$(dirname "$(dirname "$script_dir")")

start_time=$(date +%s)
start_human=$(date +"%Y-%m-%d %H:%M:%S")

echo "============================================================"
echo " Script: $script_path"
echo " Dir   : $script_dir"
echo " Base  : $grandparent_dir"
echo " Args  : $*"
echo " Start : $start_human"
echo "============================================================"
echo

set_shopt_options() {
    local shopt_file=$1

    if [ -f "$shopt_file" ]; then
        echo "Script directory: $script_dir"
        local shopt_opts
        shopt_opts=$(
            . "$script_dir/fcat" "$shopt_file" | sort -u | xargs echo
        )
        echo "Setting shopt options: $shopt_opts"
        # shellcheck disable=SC2086
        shopt -s $shopt_opts
    fi
}

if [[ -n "$1" ]]; then
    set_shopt_options "$1"
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
