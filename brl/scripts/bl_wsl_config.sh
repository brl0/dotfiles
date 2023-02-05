#!/bin/bash
# Create symbolic links for commonly used directories
# BRL XPS8500

echo 'script begin'

# ln -s /mnt/c/ ~/c
# ln -s /mnt/c/Users/b_r_l/ ~/b_r_l
# ln -s /mnt/c/Users/b_r_l/ ~/B_R_L
# # ln -s /mnt/c/Users/b_r_l/ ~/brl
# ln -s /mnt/c/Users/b_r_l/Downloads/ ~/downloads
# ln -s /mnt/c/Users/b_r_l/Google\ Drive/ ~/g
# ln -s /mnt/c/Users/b_r_l/Google\ Drive/ ~/gdrive
# ln -s /mnt/c/Users/b_r_l/OneDrive/ ~/one
# ln -s /mnt/c/Users/b_r_l/OneDrive/ ~/onedrive
# ln -s /mnt/c/Users/b_r_l/OneDrive/.gnupg/ ~/.gnupg
# ln -s /mnt/c/Users/b_r_l/OneDrive/Documents/ ~/docs
# ln -s /mnt/c/Users/b_r_l/OneDrive/Documents/ ~/Documents
# ln -s /mnt/c/Users/b_r_l/OneDrive/Documents/backup/ ~/backup
# ln -s /mnt/c/Users/b_r_l/OneDrive/Documents/code/ ~/code
# ln -s /mnt/c/Users/b_r_l/OneDrive/Documents/code/scripts/ ~/bin
# ln -s /mnt/c/Users/b_r_l/OneDrive/Documents/code/scripts/ ~/scripts
# ln -s /mnt/c/Users/b_r_l/OneDrive/Documents/projects/ ~/projects
# ln -s /mnt/c/Users/b_r_l/OneDrive/wsl/ ~/wsl
# ln -s /mnt/d/ ~/d
# ln -s /mnt/d/local/ ~/local
# ln -s /mnt/e/ ~/e

pushd ~
xargs -a .brl.wsl_links.txt -i -r echo {} | xargs -r -d -t "|" ln -s

sudo ln -s /mnt/c/Users/b_r_l/OneDrive/wsl/wsl.conf /etc/wsl.conf

chmod -R +x ~/code

mkdir ~/repos

git config --global user.name "Brian Larsen"
git config --global user.email "B_R_L@hotmail.com"
git config --global core.editor nano

cp -r /mnt/c/Users/b_r_l/.ssh ~/
chmod 700 ~/.ssh
chmod 600 ~/.ssh/id_*
chmod 644 ~/.ssh/id_*.pub

popd
echo 'script complete'
# END
