#!/bin/bash

PY_FILES=$(
    find . -name '*.py' \
    | grep -v "^\./src/" \
    | grep -v "^\./build/" \
    | grep -v "^\./ZenPacks/zenoss/AWS/lib/" \
    | grep "^\./ZenPacks/zenoss/AWS/"
)
python pep8.py --max-line-length=85 --show-source $PY_FILES
