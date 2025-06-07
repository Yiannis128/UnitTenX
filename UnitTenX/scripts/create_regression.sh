#!/bin/bash
# Copyright 2025 Claudionor N. Coelho Jr

dir_path="test"

mkdir -p $1

if [ ! -d "$dir_path" ]; then
    echo "Directory '$dir_path' does not exist."
    exit 1
fi

pushd $1 > /dev/null
target_path=`pwd`
popd > /dev/null

cd $dir_path

for dir in *
do
	echo "... copying $dir"
	mkdir -p $target_path/$dir
	cp $dir/Makefile $target_path/$dir/
	cp $dir/*.cc $target_path/$dir/
done

cd - > /dev/null
