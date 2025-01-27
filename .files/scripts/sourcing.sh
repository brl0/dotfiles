#!/bin/bash

function _source_if_exists() {
    if [ -f "$1" ]; then
        echo "sourcing $1"
        # shellcheck disable=SC1090
        . "$1"
    else
        echo "file $1 does not exist"
    fi
}
alias source_if_exists='_source_if_exists'

function _import_env() {
    set -o allexport
    source_if_exists "$1"
    set +o allexport
}
alias import_env='_import_env'
