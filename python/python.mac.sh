#!/bin/bash

pushd $(dirname $(which ${BASH_SOURCE[0]}))

#pushd ../MacOSXx86_64/Python/v2.6
#export PYTHONBIN=`pwd`/bin/python
#export PYTHONPATH=`pwd`/lib
#popd

export PYTHONPATH=${PYTHONPATH}:`pwd`/lib

popd

#${PYTHONBIN} $*
python $*
