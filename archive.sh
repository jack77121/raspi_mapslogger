#!/bin/bash
DIRECTORY='log'
if [ -d "$DIRECTORY" ]; then
	# Control will enter here if $DIRECTORY exists.
	echo "exist"
	echo `pwd`
	cd log
	for f in *.log; do
		echo $f
		filename=$(echo $f|cut -d '_' -f 1)
		echo $filename
		if [ ! -d "$filename" ]; then
			mkdir ${filename}
			echo "mkdir done"
		fi
		mv ${f} ${filename}
	done
fi
