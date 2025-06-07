#!/bin/bash
# Copyright 2025 Claudionor N. Coelho Jr

dir_path="test"

if [ ! -d "$dir_path" ]; then
    echo "Directory '$dir_path' does not exist."
    exit 1
fi

for dir in $dir_path/*
do
	echo ""
	echo "======================================================"
	echo "Entering $dir"
	echo "======================================================"
	echo ""
	cd "$dir" 
        grep CRASH *.cc | sed 's/^[ \t]*//'
        cd - >/dev/null
done
