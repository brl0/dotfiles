#!/bin/bash
# Create symbolic links for commonly used directories
# BRL XPS8500

echo 'script begin'

pushd ~ || exit
xargs -a ~/dotfiles/.brl/wsl_links.txt -i -r echo {} | xargs -r -n 2 ln -s
popd || exit

echo 'script complete'
# END
