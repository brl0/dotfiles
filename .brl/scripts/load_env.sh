#!/bin/bash
set -a

if [ $# -eq 0 ]; then
    file="$HOME/.env"
else
    file="$*"
fi

if [ -f "$file" ]; then
    # shellcheck disable=SC1090
    . "$file"
fi

set +a
