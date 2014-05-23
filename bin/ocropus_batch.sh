#!/bin/bash
export PYTHONIOENCODING=UTF-8
#set the directory of the collection of books
#COLLECTION_DIR=/usr/local/OCR_Processing/Texts/Athenaeus/Pngs
# We expect two args: the collection_dir and the classifier_dir
USAGE_MESSAGE="Usage: ocropus_batch pdf_file classifier_file"
EXPECTED_ARGS_MIN=2
EXPECTED_ARGS_MAX=2
E_BADARGS=65
INPUT_FILE=$1
CLASSIFIER_FILE=$2
OCR_OUTPUT_DIR=/work/broberts/Output
PPI=400

#check that env. variables are set
[ -z "$CIACONNA_HOME" ] && { echo "Need to set CIACONNA_HOME env. variable"; exit 1; }

#set date
FOO=${DATE:=`date +%F-%H-%M`}
echo "Using Date $DATE"

if [ $# -lt $EXPECTED_ARGS_MIN -o $# -gt $EXPECTED_ARGS_MAX ]
then
  echo $USAGE_MESSAGE
  exit $E_BADARGS
fi
if [ ! -f $CLASSIFIER_FILE ]; then
	echo "classifier file $CLASSIFIER_FILE does not exist"
        echo $USAGE_MESSAGE
        exit $E_BADARGS
fi
if [ ! -f "$INPUT_FILE" ]; then
        echo "pdf file $INPUT_FILE does not exist"
        echo $USAGE_MESSAGE
        exit $E_BADARGS
fi

file=${INPUT_FILE##*/}
echo "file $file"
base=${file%.*}
base=${base%_*}
ext=${file##*.}


if [ ! "$ext" == "pdf" ] && [ ! "$ext" == "zip"]; then
	echo "pdf file $INPUT_FILE does not have a recognized extension: $ext"
	echo $USAGE_MESSAGE
        exit $E_BADARGS
fi

if [ ! -d $OCR_OUTPUT_DIR/$base ]; then
	echo "working directory $OCR_OUTPUT_DIR/$base does not exist. Making it."
	mkdir "$OCR_OUTPUT_DIR/$base"
fi
IMAGE_DIR=$OCR_OUTPUT_DIR/$base/$base-PNG-$PPI

if [  "$ext" == "pdf" ]; then
if [ ! -d $IMAGE_DIR ]; then
	echo "converting pdf to pngs at resolution $PPI..."
	mkdir $IMAGE_DIR
	cd $IMAGE_DIR
        pdftoppm -r $PPI  -png $INPUT_FILE $base
	echo "done converting" 
fi
fi

if [ "$ext" == "zip" ]; then
if [ ! -d $IMAGE_DIR ]; then
	echo "uncompressing zip file"
	mkdir $IMAGE_DIR
        cd $IMAGE_DIR
	unzip "$INPUT_FILE"
	echo "done uncompressing"
	for image_file in $(ls *_jp2/*.jp2 *_tif/*.tif)
	do
		b=$(basename $image_file)
		filebase=${b%.*}
       	 	fileext=${b##*.}
                if [ ! -f $filebase.png ]; then 
			echo "converting $image_file to $filebase.png"
			convert $image_file $filebase.png
		fi
	done
fi
fi
classifier_file_base=$(basename $CLASSIFIER_FILE)
INNER_HOCR_OUTPUT_DIR=${DATE}_${classifier_file_base}_raw_hocr_output
INNER_SELECTED_DIR=${DATE}_${classifier_file_base}_selected_hocr_output
HOCR_OUTPUT_DIR=$IMAGE_DIR/$INNER_HOCR_OUTPUT_DIR
SELECTED_DIR=$IMAGE_DIR/$INNER_SELECTED_DIR
if [ ! -d $HOCR_OUTPUT_DIR ]; then
        echo "making hocr output dir"
        mkdir $HOCR_OUTPUT_DIR
	mkdir $SELECTED_DIR
fi

SMALL_IMAGE_DIR=$IMAGE_DIR/${base}_color
if [ ! -d $SMALL_IMAGE_DIR ]; then
        echo "making jpg output dir"
        mkdir $SMALL_IMAGE_DIR
fi

cd "$IMAGE_DIR"
echo "processing image files"
for image_file in $(ls *.png)
do
	filebase=${image_file%.*}
	fileext=${image_file##*.}
	if [ ! -f $HOCR_OUTPUT_DIR/$filebase.html ]; then
		echo "processing $image_file into $filebase.html"
		$CIACONNA_HOME/bin/ocropus_page.sh -v -l $CLASSIFIER_FILE -o $HOCR_OUTPUT_DIR/$filebase.html $image_file 2>&1
	fi
	if [ ! -f $SMALL_IMAGE_DIR/$file_base.jpg ]; then
		echo "creating $file_base.jpg"
		convert $image_file -scale 30% $SMALL_IMAGE_DIR/$filebase.jpg
	fi
done
echo "Classifier file base: $classifier_file_base"
archive_name_base="robertson_${DATE}_${base}_${classifier_file_base}_full"

zip -r $archive_name_base.zip $HOCR_OUTPUT_DIR/
cd $HOCR_OUTPUT_DIR/..
cp $HOCR_OUTPUT_DIR/* $SELECTED_DIR
tar -czf $archive_name_base.tar.gz $INNER_HOCR_OUTPUT_DIR $INNER_SELECTED_DIR
cd -
cd $OCR_OUTPUT_DIR/Zips
ln -s $IMAGE_DIR/$archive_name_base.zip
cd $OCR_OUTPUT_DIR/Tars
ln -s $IMAGE_DIR/$archive_name_base.tar.gz
cd $OCR_OUTPUT_DIR/Jpgs
if [ ! -d $SMALL_IMAGE_DIR ]; then
  ln -s $SMALL_IMAGE_DIR
fi

