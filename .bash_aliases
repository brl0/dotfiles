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
function mkalias_code() { code-insiders "$@"; }
alias edit='mkalias_code'

alias edit-dots='mkalias_edit-dots'
function mkalias_edit-dots() {
  # TODO: add args to dotfiles
  # echo $@ | sed 's/ /\n/g' | xargs -i -n 1 echo "{}" >> ~/.brl.dotfiles.txt
  pushd ~ || return
  xargs -a ~/.brl.dotfiles.txt code-insiders -n "$@"
  popd || return
}
alias rc='mkalias_edit-dots'

# alias rc='mkalias_rc'
# function mkalias_rc(){ code ~/.bashrc "$@"; }

alias datum='mkalias_datum'
function mkalias_datum() { cd ~/repos/datum/ && conda activate datum && code-insiders ~/repos/datum/ "$@"; }

alias upg='mkalias_upg'
function mkalias_upg() { bash ~/.brl.upgrades.sh; }

alias clone='mkalias_clone'
function mkalias_clone() {
  pushd ~/repos || return
  gh repo clone "$@";
  popd || return
}

alias chrome='mkalias_chrome'
function mkalias_chrome() { "$BROWSER" "$@"; }
alias browse='mkalias_chrome'
alias browser='mkalias_chrome'

alias maxi='mkalias_maxi'
function mkalias_maxi() { conda activate /home/brl0/maxiconda/envs/maxiconda; }

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

alias first='mkalias_first'
function mkalias_first() { awk '{ print $1; }' "$@"; }

alias ufirst='mkalias_ufirst'
function mkalias_ufirst() { awk '{ print $1; }' "$@" | sort -u; }

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
  ("$@" && sect_date 'Completed') || sect_date 'FAILED!';
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
  "$t" -p "$b" -c "$_CMD; $sect_cmd" && \
  sect_date 'Completed' || (p_sect && sect_date 'FAILED!');
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
  code .;
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