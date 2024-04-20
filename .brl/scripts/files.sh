#!/bin/bash

# Specify the directory to analyze (recursively)
directory="./"

# Initialize associative arrays to store file sizes and counts
declare -A file_sizes
declare -A file_counts

# Function to process files
process_file() {
    local file_path="$1"
    local extension="${file_path##*.}"
    local file_output
    file_output=$(file "$file_path")
    if echo "$file_output" | grep -q "text"; then
        # echo "The file contains plain text."
        extension="text-$extension"
    fi
    local file_size
    file_size=$(stat -c %s "$file_path")
    ((file_sizes["$extension"] += file_size))
    ((file_counts["$extension"]++))
}

typeset -xf process_file
export process_file

# Recursively find files
file_list=$(find "$directory" -type f)
# \( -name "*.yml" -o -name "*.yaml" \))

# Iterate through the list of files
for file_item in $file_list; do
    echo "Processing file: $file_item"
    # Add your custom logic here (e.g., perform some operation on the file)
    process_file "$file_item"
done

# Print summary
echo "File Type | File Count | Total Size (Bytes)"
echo "------------------------------------------"
for ext in "${!file_sizes[@]}"; do
    echo "$ext | ${file_counts[$ext]} | ${file_sizes[$ext]}"
done
