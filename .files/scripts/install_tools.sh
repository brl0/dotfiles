#!/bin/bash
# Install linux/wsl tools

echo "script begin: $0"

pkg_installer "$HOME/dotfiles/.files/pkgs/apt.txt" "sudo apt-get install -y"

# install webi
curl -sS https://webi.sh/webi | sh; \
source "$HOME/.config/envman/PATH.env"
pkg_installer "$HOME/dotfiles/.files/pkgs/webi.txt" "webi"

# install x
eval "$(curl https://get.x-cmd.com)"
pkg_installer "$HOME/dotfiles/.files/pkgs/x_install.txt" "x install"

# python tools
pkg_installer "$HOME/dotfiles/.files/pkgs/pipx.txt" "pipx install"
pkg_installer "$HOME/dotfiles/.files/pkgs/xpip.txt" "xpip install"
pkg_installer "$HOME/dotfiles/.files/pkgs/micromamba.txt" "micromamba install -y"

# install mamba environment
micromamba create -y -n brl -f "$HOME/dotfiles/.files/pkgs/brl.yml"

echo "script end: $0"
