#!/bin/bash
#----------------------
#f=`pwd`
f=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
NOWDATE=`date '+%Y-%m-%d_%T'`

export PYTHONPATH=/opt/client

python2 /opt/client/Correct/Correct.py
