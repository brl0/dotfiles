#!/bin/bash
# State Tracking Module
# Functions: load_state(), save_state(), state_file_path(), check_state()

state_file_path() {
    local project_name="${1:-pkgm}"
    echo "$HOME/.${project_name}.pkgm.state"
}

load_state() {
    local state_file="$1"

    if [[ ! -f "$state_file" ]]; then
        echo "{}"
        return 0
    fi

    cat "$state_file"
}

save_state() {
    local state_file="$1"
    local state_json="$2"

    # Ensure directory exists
    mkdir -p "$(dirname "$state_file")"

    # Write state file atomically
    echo "$state_json" > "$state_file.tmp"
    mv "$state_file.tmp" "$state_file"
}

check_manifest_hash() {
    local state_json="$1"
    local current_hash="$2"

    # Extract manifest_hash from state JSON
    # Simple extraction for "manifest_hash":"<hash>"
    local stored_hash
    stored_hash=$(echo "$state_json" | grep -o '"manifest_hash":"[^"]*"' | cut -d'"' -f4 || echo "")

    if [[ -z "$stored_hash" ]]; then
        return 1  # No stored hash, work needed
    fi

    if [[ "$stored_hash" == "$current_hash" ]]; then
        return 0  # Hashes match, no work needed
    fi

    return 1  # Hashes differ, work needed
}

get_finished_managers() {
    local state_json="$1"

    # Extract finished_managers array from state JSON
    # Returns space-separated list of manager names
    echo "$state_json" | grep -o '"finished_managers":\s*\[[^]]*\]' | \
        sed 's/.*:\s*\[//; s/\].*//' | \
        tr ',' '\n' | \
        sed 's/"//g; s/[[:space:]]*//g' | \
        paste -sd' ' - || echo ""
}

add_finished_manager() {
    local state_json="$1"
    local manager="$2"

    # Add manager to finished_managers list in JSON
    # Simple approach: remove old finished_managers and add new one
    local old_managers
    old_managers=$(get_finished_managers "$state_json")

    local new_managers="$manager"
    for m in $old_managers; do
        if [[ "$m" != "$manager" ]]; then
            new_managers="$new_managers,$m"
        fi
    done

    # Remove old finished_managers
    state_json=$(echo "$state_json" | sed 's/"finished_managers":\s*\[[^]]*\]//')

    # Remove trailing comma if present
    state_json=$(echo "$state_json" | sed 's/,$//')

    # Add new finished_managers before closing brace
    state_json=$(echo "$state_json" | sed "s/}$/,\"finished_managers\":[$(echo "$new_managers" | sed 's/,/\",\"/g; s/^/\"/; s/$/\"/')}/")

    echo "$state_json"
}

update_manifest_hash() {
    local state_json="$1"
    local manifest_hash="$2"
    local timestamp="$3"

    # Remove old manifest_hash and timestamp if present
    state_json=$(echo "$state_json" | sed 's/"manifest_hash":"[^"]*",*//')
    state_json=$(echo "$state_json" | sed 's/"timestamp":"[^"]*",*//')

    # Remove trailing comma and brace
    state_json=$(echo "$state_json" | sed 's/,\s*}/}/')

    # Add new manifest_hash and timestamp before closing brace
    state_json=$(echo "$state_json" | sed "s/}$/,\"manifest_hash\":\"$manifest_hash\",\"timestamp\":$timestamp}/")

    echo "$state_json"
}

initialize_state() {
    local manifest_hash="$1"
    local timestamp="$2"

    echo "{\"manifest_hash\":\"$manifest_hash\",\"timestamp\":$timestamp,\"finished_managers\":[]}"
}
