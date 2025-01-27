#!/bin/bash

source_files() {
    script_dir=$(dirname "$0")
    pushd "$script_dir/../.." > /dev/null || exit
    while IFS= read -r script; do
        if [[ -f "$script" ]]; then
            echo "Running: $script"
            # shellcheck disable=SC1090
            source "$script"
        else
            echo "File $script not found."
        fi
    done
    popd > /dev/null || exit
}

# If a file is provided as an argument
if [[ -n "$1" ]]; then
    if [[ -f "$1" ]]; then
        source_files < "$1"
    else
        echo "File $1 not found."
    fi
# If piped input is provided
elif [[ ! -t 0 ]]; then
    source_files
else
    echo "No input provided. Please provide a file as a parameter or pipe a list of scripts."
fi
