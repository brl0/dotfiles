# BRL
echo "processing .bash_profile"
if [ -r ~/.profile ]; then
    . ~/.profile
else
    if [ -f "$HOME/.bashrc" ]; then
        . "$HOME/.bashrc"
    fi
fi
echo "finished .bash_profile"
# /BRL
