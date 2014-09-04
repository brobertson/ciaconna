#!/bin/bash
DALITZ_HOME=/home/brucerob/Dalitz/
file=$1
OUTPUT_DIR=$(mktemp -d)
echo "Dalitz preprocess Output dir: $OUTPUT_DIR"
python $DALITZ_HOME/remove_title_3.1.py   -tf $DALITZ_HOME/midletters.xml -od $OUTPUT_DIR $file
dir=$(dirname $file)
name=$(basename $file)
name_without_extension=${name%.*}

#overwrite the input file
cp $OUTPUT_DIR/${name_without_extension}_rt_result.png $file
