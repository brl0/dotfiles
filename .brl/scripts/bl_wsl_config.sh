#!/bin/bash
# Create symbolic links for commonly used directories
# BRL XPS8500

echo "script begin: $0"

/bin/bash ~/dotfiles/.brl/scripts/update_links.sh

sudo ln -s ~/wsl/wsl.conf /etc/wsl.conf

chmod -R +x ~/code

mkdir ~/repos

# /bin/bash ~/dotfiles/.brl/scripts/git_config.sh

/bin/bash ~/dotfiles/.brl/scripts/copy_ssh.sh

/usr/bin/env python3 ~/dotfiles/.brl/scripts/install_dots.py

/bin/bash ~/dotfiles/.brl/scripts/install_tools.sh

echo "script end: $0"
# END
