#!/bin/bash
echo "first arg: $1"
id=${2##*/}
echo "path: $id"
id=${id%.pdf}
echo "id: $id"
echo "classifier file: $1"

/work/broberts/ciaconna/bin/dl_archive_and_ocropus.sh  -f $2 -m /work/broberts/Metadata_Files/${id}_meta.xml -t 0.6 -c ' --threshold 0.4 ' -l $1
