#!/bin/bash
# Create symbolic links for commonly used directories
# BRL XPS8500

echo "script begin: $0"

/bin/bash ~/dotfiles/.files/scripts/update_links.sh

sudo ln -s ~/wsl/wsl.conf /etc/wsl.conf

chmod -R +x ~/code

mkdir ~/repos

# /bin/bash ~/dotfiles/.files/scripts/git_config.sh

/bin/bash ~/dotfiles/.files/scripts/copy_ssh.sh

/usr/bin/env python3 ~/dotfiles/.files/scripts/install_dots.py

/bin/bash ~/dotfiles/.files/scripts/install_tools.sh

echo "script end: $0"
# END
