#!/bin/bash

set_shopt_options() {
    local shopt_file=$1

    if [ -f "$shopt_file" ]; then
        script_dir=$(dirname "$0")
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
