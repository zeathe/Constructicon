#!/bin/bash

pushd ../MacOSXx86_64/Python/v2.6
export PYTHONBIN=`pwd`/bin/python
export PYTHONPATH=`pwd`/lib
popd

${PYTHONBIN} $*
