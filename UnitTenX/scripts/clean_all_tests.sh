#!/bin/bash
# Copyright 2025 Claudionor N. Coelho Jr

dir_path="test"

if [ ! -d "$dir_path" ]; then
    echo "Directory '$dir_path' does not exist."
    exit 1
fi

for dir in $dir_path/*
do
	echo "Entering $dir"
	cd "$dir"
        make clean
        cd -
done
