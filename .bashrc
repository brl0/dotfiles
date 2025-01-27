#!/usr/bin/env bash

# ~/.bashrc: executed by bash(1) for non-login shells.
# see /usr/share/doc/bash/examples/startup-files (in the package bash-doc)
# for examples

# If not running interactively, don't do anything
case $- in
    *i*) ;;
      *) return;;
esac

echo "script begin: $0"
echo 'processing ~/.bashrc'

# run all autorun scripts
for x in "$HOME"/.files/autorun/*.{env,bash,sh}; do
    [ -e "$x" ] || continue  # Skip if no files match the pattern
    echo "sourcing: $x"
    # shellcheck disable=SC1090
    source "$x"
done

import_env "$HOME/.bash.env"
import_env "$HOME/.env"

# Call the function to set shopt options from a file
set_shopt_options "$HOME/dotfiles/.files/config/shopts.txt"

export PROMPT_COMMAND="history -a; history -c; history -r; $PROMPT_COMMAND"

# make less more friendly for non-text input files, see lesspipe(1)
[ -x /usr/bin/lesspipe ] && eval "$(SHELL=/bin/sh lesspipe)"

# set variable identifying the chroot you work in (used in the prompt below)
if [ -z "${debian_chroot:-}" ] && [ -r /etc/debian_chroot ]; then
    debian_chroot=$(cat /etc/debian_chroot)
fi

# set a fancy prompt (non-color, unless we know we "want" color)
case "$TERM" in
    xterm-color | *-256color) color_prompt=yes ;;
esac

# uncomment for a colored prompt, if the terminal has the capability; turned
# off by default to not distract the user: the focus in a terminal window
# should be on the output of commands, not on the prompt
force_color_prompt=yes

if [ -n "$force_color_prompt" ]; then
    if [ -x /usr/bin/tput ] && tput setaf 1 >&/dev/null; then
        # We have color support; assume it's compliant with Ecma-48
        # (ISO/IEC-6429). (Lack of such support is extremely rare, and such
        # a case would tend to support setf rather than setaf.)
        color_prompt=yes
    else
        color_prompt=
    fi
fi

if [ "$color_prompt" = yes ]; then
    PS1='${debian_chroot:+($debian_chroot)}\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '
else
    PS1='${debian_chroot:+($debian_chroot)}\u@\h:\w\$ '
fi
unset color_prompt force_color_prompt

# If this is an xterm set the title to user@host:dir
case "$TERM" in
xterm* | rxvt*)
    PS1="\[\e]0;${debian_chroot:+($debian_chroot)}\u@\h: \w\a\]$PS1"
    ;;
*) ;;

esac

# enable color support of ls and also add handy aliases
if [ -x /usr/bin/dircolors ]; then
    test -r "$HOME/.dircolors" && eval "$(dircolors -b "$HOME/.dircolors")" || eval "$(dircolors -b)"
    alias ls='ls --color=auto'
    alias dir='dir --color=auto'
    alias vdir='vdir --color=auto'

    alias grep='grep --color=auto'
    alias fgrep='fgrep --color=auto'
    alias egrep='egrep --color=auto'
fi

# Alias definitions.
# You may want to put all your additions into a separate file like
# $HOME/.bash_aliases, instead of adding them here directly.
# See /usr/share/doc/bash-doc/examples in the bash-doc package.

source_if_exists "$HOME/.bash_aliases"

# enable programmable completion features (you don't need to enable
# this, if it's already enabled in /etc/bash.bashrc and /etc/profile
# sources /etc/bash.bashrc).
# if ! shopt -oq posix; then
#     if [ -f /usr/share/bash-completion/bash_completion ]; then
#         . /usr/share/bash-completion/bash_completion
#         elif [ -f /etc/bash_completion ]; then
#         . /etc/bash_completion
#     fi
# fi

source_if_exists /usr/share/bash-completion/bash_completion
source_if_exists /etc/bash_completion

# BRL
# Coloured man page support
# using 'less' env vars (format is '\E[<brightness>;<colour>m')
# export LESS_TERMCAP_mb="\033[01;31m"     # begin blinking
# export LESS_TERMCAP_md="\033[01;31m"     # begin bold
# export LESS_TERMCAP_me="\033[0m"         # end mode
# export LESS_TERMCAP_so="\033[01;44;36m"  # begin standout-mode (bottom of screen)
# export LESS_TERMCAP_se="\033[0m"         # end standout-mode
# export LESS_TERMCAP_us="\033[00;36m"     # begin underline
# export LESS_TERMCAP_ue="\033[0m"         # end underline

bind '"\e[A": history-search-backward'
bind '"\e[B": history-search-forward'

# # https://www.hanselman.com/blog/HowToMakeAPrettyPromptInWindowsTerminalWithPowerlineNerdFontsCascadiaCodeWSLAndOhmyposh.aspx
# # https://devpro.media/install-powerline-ubuntu/#install-powerline
# # Powerline configuration
# if [ -f /usr/share/powerline/bindings/bash/powerline.sh ]; then
#     powerline-daemon -q
#     POWERLINE_BASH_CONTINUATION=1
#     POWERLINE_BASH_SELECT=1
#     source /usr/share/powerline/bindings/bash/powerline.sh
# fi

# Generated for envman. Do not edit.
[ -s "$HOME/.config/envman/load.sh" ] && source "$HOME/.config/envman/load.sh"

# Set up fzf key bindings and fuzzy completion
eval "$(fzf --bash)"

source_if_exists "${XDG_CONFIG_HOME:-$HOME/.config}/asdf-direnv/bashrc"

trap 'source $HOME/.bashrc' USR1

source_if_exists "$HOME/.bash.d/cht.sh"

# export DOTNET_ROOT=/snap/dotnet-sdk/current

# The next line updates PATH for the Google Cloud SDK.
source_if_exists "$HOME/google-cloud-sdk/path.bash.inc"

# The next line enables shell command completion for gcloud.
source_if_exists "$HOME/google-cloud-sdk/completion.bash.inc"

# Check if ssh-agent is running, and if not, start it
# if [ -z $(pgrep ssh-agent) ]; then
#     eval "$(ssh-agent -s)"
# else
#     echo "ssh-agent already running"
# fi

# "C:\Program Files\Google\Chrome\Application\chrome.exe"
BROWSER="$(wslpath "C:\Program Files\Google\Chrome Beta\Application\chrome.exe")"
export BROWSER

HISTIGNORE=$(alias | cut -d "=" -f1 | cut -d " " -f2 | xargs echo | sed 's/ /\:/g')
HISTIGNORE="bash:clear:date:exit:fzf:history:ipython:ls:pwd:python:sh:xonsh:$HISTIGNORE:"
HISTIGNORE=$(echo "$HISTIGNORE" | sed 's/\:/\n/g' | sort -u | xargs echo | sed 's/ /\:/g')
HISTIGNORE="$HISTIGNORE:"
export HISTIGNORE

# PATH="/mnt/c/WINDOWS:/mnt/c/WINDOWS/System32:/mnt/c/Users/b_r_l/AppData/Local/Microsoft/WindowsApps:$PATH"
PATH="$HOME/.local/bin:$PATH"
# deduplicate PATH values
PATH=$(echo "$PATH" | sed 's/:/\n/g' | awk '!x[$0]++' | xargs -i -n 1 echo "::{}::" | xargs echo | sed 's/:: ::/:/g' | sed 's/:://g')
export PATH

# export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1

# # >>> mamba initialize >>>
# # !! Contents within this block are managed by 'mamba init' !!
# export MAMBA_EXE="$HOME/.local/bin/micromamba"
# export MAMBA_ROOT_PREFIX="$HOME/micromamba"
# __mamba_setup="$("$MAMBA_EXE" shell hook --shell bash --prefix "$MAMBA_ROOT_PREFIX" 2>/dev/null)"
# if [ $? -eq 0 ]; then
#     eval "$__mamba_setup"
# else
#     if [ -f "$HOME/micromamba/etc/profile.d/micromamba.sh" ]; then
#         . "$HOME/micromamba/etc/profile.d/micromamba.sh"
#     else
#         export PATH="$HOME/micromamba/bin:$PATH" # extra space after export prevents interference from conda init
#     fi
# fi
# unset __mamba_setup
# # <<< mamba initialize <<<

# >>> conda initialize >>>
# !! Contents within this block are managed by 'conda init' !!
__conda_setup="$("$HOME/micromamba/bin/conda" 'shell.bash' 'hook' 2>/dev/null)"
if [ $? -eq 0 ]; then
    eval "$__conda_setup"
else
    if [ -f "$HOME/micromamba/etc/profile.d/conda.sh" ]; then
        . "$HOME/micromamba/etc/profile.d/conda.sh"
    else
        export PATH="$HOME/micromamba/bin:$PATH"
    fi
fi
unset __conda_setup
# <<< conda initialize <<<

eval "$(register-python-argcomplete pipx)"

echo 'finished ~/.bashrc'
echo "script end: $0"
# END BRL
