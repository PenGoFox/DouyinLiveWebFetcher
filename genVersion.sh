#/bin/bash

commitHash=`git rev-parse --short HEAD`

if [ $? -eq 0 ]; then
    echo version = \"$commitHash\" > version.py
else
    echo get commit hash failed!
fi
