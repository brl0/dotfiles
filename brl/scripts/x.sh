#!/usr/bin/env bash
## #!/bin/bash
echo 'script begin'
# Check to see if a pipe exists on stdin.
if [ -p /dev/stdin ]; then
        echo "Data was piped to this script!"
        # If we want to read the input line by line
        while IFS=" " read -r -a line; do
                echo "Line: ${line}"
                echo
                for val in "${line[@]}"; do
                    echo "Value: ${val}"
                done
        done
        # Or if we want to simply grab all the data, we can simply use cat instead
        # cat
else
        echo "No input was found on stdin, skipping!"
        # Checking to ensure a filename was specified and that it exists
        if [ -f "$@" ]; then
                echo "Filenames specified: ${$@}"
                echo "Doing things now.."
        else
                echo "No input given!"
        fi
fi
echo 'script complete'
# END
