#!/bin/bash
# Create symbolic links for commonly used directories
# BRL XPS8500

echo 'script begin'

if [[ -n "$1" ]]; then
    CONFIG_FILE="$1"
else
    script_dir=$(dirname "$0")
    CONFIG_FILE="$script_dir/../config/dotfiles.yaml"
fi

pushd ~ || exit

# xargs -a ~/dotfiles/.files/config/wsl_links.txt -i -r echo {} | xargs -r -n 2 ln -s

while read -r key value; do
    ln -s "$value" "$HOME/$key"
done < <(yq eval '.symlinks | to_entries | .[] | "\(.key) \(.value)"' "$CONFIG_FILE")

popd || exit

echo 'script complete'
# END
