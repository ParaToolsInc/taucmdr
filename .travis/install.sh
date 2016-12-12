#!/bin/bash

INSTALLDIR=$HOME/taucmdr-test

./configure --prefix=$INSTALLDIR && make python_check

export PATH=$INSTALLDIR/conda/bin:$PATH

# Install development requirements enumerated in requirements.txt
pip install -r requirements.txt

