#!/bin/bash

# This script is used to test installation of packages and dotfiles using the test Dockerfile.

docker build -t dotfiles -f .files/test/Dockerfile .
docker run -it dotfiles /bin/bash -c "cd ./dotfiles && . .files/dotphiliac/install_dots2.py"
