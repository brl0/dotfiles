#!/bin/bash
# Install linux/wsl tools

echo "script begin: $0"

xargs -a .brl/pkgs/apt.txt -r apt install -y

# install webi
curl -sS https://webi.sh/webi | sh; \
# shellcheck source=/home/brl0/.config/envman/PATH.env
source ~/.config/envman/PATH.env
xargs -a .brl/pkgs/webi.txt -r webi

# install x
eval "$(curl https://get.x-cmd.com)"
xargs -a .brl/pkgs/x_install.txt -r x install

xargs -a .brl/pkgs/brew.txt -r brew install

# python tools
xargs -a .brl/pkgs/pipx.txt -r pipx install
xargs -a .brl/pkgs/xpip.txt -r xpip install
xargs -a .brl/pkgs/micromamba.txt -r micromamba install -y

# install mamba environment
micromamba create -y -n brl -f .brl/pkgs/brl.yml

echo "script end: $0"
