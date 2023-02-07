echo 'Performing upgrades...'

sudo apt update
sudo apt full-upgrade -y
sudo apt auto-remove -y

brew update
brew upgrade $(brew outdated --cask --greedy)
brew upgrade
brew cu -a -y --cleanup
brew cleanup
brew unlink python
brew unlink python3.8
brew unlink python3.9
brew unlink python3.10
brew unlink python3.11

topgrade --disable conda
mamba update --no-banner -n base -y --all

echo 'Upgrades complete.'
