#!/bin/bash
# script to update the dotfiles repo
pushd ~/dotfiles || return
git pull
popd || return
