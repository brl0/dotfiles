#!/bin/bash

# Check if a directory is provided as an argument
if [ -z "$1" ]; then
    echo "Usage: $0 <directory>"
    exit 1
fi

# Set all files in the given directory to be executable
for file in "$1"/*; do
    [ -f "$file" ] && chmod +x "$file"
done

echo "All files in $1 have been set to be executable."
