mkdir -p -v ~/.ssh
cp -r /mnt/c/Users/b_r_l/.ssh/id_* ~/.ssh/
sudo chmod 700 ~/.ssh
sudo chmod 600 ~/.ssh/id_*
sudo chmod 644 ~/.ssh/id_*.pub
