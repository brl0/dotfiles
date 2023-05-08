#!/bin/bash
# Create symbolic links for commonly used directories
# BRL XPS8500

echo 'script begin'

/bin/bash ~/dotfiles/.brl/scripts/update_links.sh

sudo ln -s ~/wsl/wsl.conf /etc/wsl.conf

chmod -R +x ~/code

mkdir ~/repos

# git config --global user.name "Brian Larsen"
# git config --global user.email "B_R_L@hotmail.com"
# git config --global core.editor nano

/bin/bash ~/dotfiles/.brl/scripts/copy_ssh.sh

echo 'script complete'
# END
