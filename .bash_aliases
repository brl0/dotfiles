#!/usr/bin/env bash

echo 'processing ~/.bash_aliases'

mkcd() {
        test -d "$1" || mkdir -p -- "$1" && cd -P -- "$1" || return
}

alias python=python3

alias repos='mkalias_repos'
function mkalias_repos() { cd ~/repos/ "$@" || return; }

alias docker_prune='mkalias_docker_prune'
function mkalias_docker_prune() { docker system prune -a -f --volumes "$@"; }
alias docker_purge='mkalias_docker_prune'

alias code='mkalias_code'
function mkalias_code() { code-insiders -n "$@"; }
alias edit='mkalias_code'

alias edit-dots='mkalias_rc'
function mkalias_rc() { code-insiders -n ~/dotfiles/ "$@"; }
alias rc='mkalias_rc'

alias upg='mkalias_upg'
function mkalias_upg() { bash ~/dotfiles/.brl/upgrades.sh; }

alias clone='mkalias_clone'
function mkalias_clone() {
        pushd ~/repos || return
        gh repo clone "$@"
        folder="$(echo "$@" | cut -d '/' -f 2)"
        code-insiders -n "$folder"
        popd || return
}

alias chrome='mkalias_chrome'
function mkalias_chrome() { "$BROWSER" "$@"; }
alias browse='mkalias_chrome'
alias browser='mkalias_chrome'

alias mambe='mkalias_mambe'
function mkalias_mambe() { mamba "$@"; }

alias mka='mkalias_mka'
function mkalias_mka() { mkalias new "$@"; }

alias cmd='mkalias_cmd'
function mkalias_cmd() { cmd.exe "$@"; }

alias explorer='mkalias_explorer'
function mkalias_explorer() { explorer.exe "$@"; }
alias explore='mkalias_explorer'

alias npp='mkalias_npp'
function mkalias_npp() { "/mnt/c/Program Files/Notepad++/notepad++.exe" "$@"; }
alias np='mkalias_npp'

alias notepad='mkalias_notepad'
function mkalias_notepad() { notepad.exe "$@"; }

alias winmerge='mkalias_winmerge'
function mkalias_winmerge() { "/mnt/c/Program Files/WinMerge/WinMergeU.exe" /e "$@"; }
alias merge='mkalias_winmerge'

alias powershell='mkalias_powershell'
function mkalias_powershell() { powershell.exe "$@"; }

alias pwsh='mkalias_pwsh'
function mkalias_pwsh() { pwsh.exe "$@"; }
alias posh='mkalias_pwsh'
alias psh='mkalias_pwsh'

alias uniqhist='mkalias_uniqhist'
function mkalias_uniqhist() { history "$@" | tr -s " " | cut -d " " -f 1-4 --complement | awk '!x[$0]++'; }
alias uniq-hist='mkalias_uniqhist'
alias uhist='mkalias_uniqhist'
alias hist='mkalias_uniqhist'

alias unsort='mkalias_unsort'
function mkalias_unsort() { awk '!x[$0]++' "$@"; }

alias ufirst='mkalias_ufirst'
function mkalias_ufirst() { awk '!x[$1]++ { print $1; }' "$@"; }

alias first='mkalias_first'
function mkalias_first() { awk '{ print $1; }' "$@" | sort -u; }

alias ulast='mkalias_ulast'
function mkalias_ulast() { tac "$@" | awk '!x[$1]++' | tac; }

alias xsh='mkalias_xsh'
alias x='mkalias_xsh'
function mkalias_xsh() {
        XPATH=$(echo "$PATH" | sed 's/:/\n/g' | awk '!x[$0]++' | xargs -i -n 1 echo "::{}::" | grep -v -e "/mnt/" | xargs echo | sed 's/:: ::/:/g' | sed 's/:://g')
        XPATH="$XPATH:/mnt/c/WINDOWS/system32:/mnt/c/Users/b_r_l/AppData/Local/Programs/Microsoft VS Code Insiders/bin:/mnt/c/Users/b_r_l/AppData/Local/Programs/Microsoft VS Code/bin"
        PATH="$XPATH" xonsh "$@"
}

section="----------------------------------------"

alias print_date='mkalias_date'
function mkalias_date() { printf "\n\n%s\n%s: %s\n%s\n\n" "$section" "$@" "$(date --rfc-3339=seconds)" "$section"; }
alias p_dt='mkalias_date'

alias pf=printf

sect_cmd="printf \"\\n%s\\n\" \"$section\""

alias print_section='mkalias_section'
function mkalias_section() { eval "$sect_cmd"; }
alias p_sect='mkalias_section'

function sect_date() { p_sect && p_dt "$@"; }
alias s_date='sect_date'

function cmd_date() {
        ("$@" && sect_date 'Completed') || sect_date 'FAILED!'
}

alias run='mkalias_run'
function mkalias_run() {
        clear
        p_sect
        _CMD="$(printf " %q" "${@}")"
        printf "Command:\n$section\n%s\n$section\n" "$_CMD"
        print_date "Starting"
        t="$(which time)"
        b="$(which bash)"
        # ($t -p "$b" -c "($_CMD && $sect_cmd) || $sect_cmd" &&
        #   sect_date "Completed") || (sect_date "FAILED!")
        # echo "$t" -p "$b" -c "($_CMD && $sect_cmd) || $sect_cmd"
        # "$t" -p "$b" -c "$*; $sect_cmd" && \
        "$t" -p "$b" -c "$_CMD; $sect_cmd" &&
                sect_date 'Completed' || (p_sect && sect_date 'FAILED!')
}

typeset -xf p_dt
typeset -xf p_sect
typeset -xf sect_date
typeset -xf cmd_date
typeset -xf run

alias repo='mkalias_repo'
function mkalias_repo() { pushd "$HOME/repos/$*" || return; }

alias coder='mkalias_coder'
function mkalias_coder() {
        repo "$@"
        code .
}

_repo() {
        local cur=${COMP_WORDS[COMP_CWORD]}
        _TARGET="$HOME/repos"
        IFS=$'\n' tmp=($(compgen -W "$(ls $_TARGET)" -- $cur))
        COMPREPLY=("${tmp[@]// /\ }")
        # check if completion array is not empty
        if [ ${#tmp[@]} -ne 0 ]; then
                COMPREPLY=($(printf "%q\n" "${tmp[@]}"))
        fi
}

complete -o nospace -F _repo repo
complete -o nospace -F _repo coder

echo 'finished ~/.bash_aliases'
# END BRL
