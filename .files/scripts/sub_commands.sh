# Normalize command string: strip outer quotes if both exist
normalize_command() {
    local cmd="$1"
    if [[ ($cmd == \"*\" && $cmd == *\") || ($cmd == \'*\' && $cmd == *\') ]]; then
        cmd="${cmd:1:-1}"
    fi
    printf "\n%s\n" "$cmd"
}

# Safely run a command string inside the chosen shell
run_command() {
    local shell_bin="$1"
    shift
    local -a shell_args=("$@")
    local cmd="${shell_args[-1]}"
    ncmd="$(normalize_command "$cmd")"
    unset 'shell_args[-1]' # remove the command from args
    printf "\nRunning command: %s\n" "$ncmd"
    eval "\"$shell_bin\" ${shell_args[*]} \"$ncmd\""
}
