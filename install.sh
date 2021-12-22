#!/bin/sh

set -e

install_dir=/usr/bin

ln -fs "$PWD"/dotmgt/dotmgt.py "$install_dir"/dotmgt
ln -fs "$PWD"/txtpp/src/txtpp.py "$install_dir"/txtpp

echo Done
