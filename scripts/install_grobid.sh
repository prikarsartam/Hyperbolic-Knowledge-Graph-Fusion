#!/bin/bash
set -e

echo "Starting GROBID installation..."
cd /home/naturalis/programs/hyperbolic_KG

if [ ! -d "grobid" ]; then
    git clone https://github.com/kermitt2/grobid.git
    cd grobid
    ./gradlew clean install --no-daemon
    echo "GROBID installed successfully."
else
    echo "GROBID is already cloned."
fi
