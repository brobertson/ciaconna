#!/bin/bash
export PYTHONIOENCODING=UTF-8
#set the directory of the collection of books
#COLLECTION_DIR=/usr/local/OCR_Processing/Texts/Athenaeus/Pngs
# We expect two args: the collection_dir and the classifier_dir
USAGE_MESSAGE="Usage: ocropus_batch pdf_file classifier_file"
EXPECTED_ARGS_MIN=2
EXPECTED_ARGS_MAX=2
E_BADARGS=65
PDF_FILE=$1
CLASSIFIER_FILE=$2
OCR_OUTPUT_DIR=/work/broberts/Output
PPI=400
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
if [ ! -f $PDF_FILE ]; then
        echo "pdf file $PDF_FILE does not exist"
        echo $USAGE_MESSAGE
        exit $E_BADARGS
fi

file=${PDF_FILE##*/}
echo "file $file"
base=${file%.*}
ext=${file##*.}


if [ ! "$ext" == "pdf" ]; then
	echo "pdf file $PDF_FILE does not have a recognized extension: $ext"
	echo $USAGE_MESSAGE
        exit $E_BADARGS
fi

if [ ! -d $OCR_OUTPUT_DIR/$base ]; then
	echo "working directory $OCR_OUTPUT_DIR/$base does not exist. Making it."
	mkdir "$OCR_OUTPUT_DIR/$base"
fi
IMAGE_DIR=$OCR_OUTPUT_DIR/$base/$base-PNG-$PPI
if [ ! -d $IMAGE_DIR ]; then
	echo "converting pdf to pngs at resolution $PPI..."
	mkdir $IMAGE_DIR
	cd $IMAGE_DIR
        pdftoppm -r $PPI  -png $PDF_FILE $base
	echo "done converting" 
fi

HOCR_OUTPUT_DIR=$IMAGE_DIR/$DATE
if [ ! -d $HOCR_OUTPUT_DIR ]; then
        echo "making hocr output dir"
        mkdir $HOCR_OUTPUT_DIR
fi

SMALL_IMAGE_DIR=$IMAGE_DIR/Jpgs
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
		/home/broberts/rigaudon/Scripts/ocropus_me.sh -v -l $CLASSIFIER_FILE -o $HOCR_OUTPUT_DIR/$filebase.html $image_file 2>&1
	fi
	if [ ! -f $SMALL_IMAGE_DIR/$file_base.jpg ]; then
		echo "creating $file_base.jpg"
		convert $image_file -scale 30% $SMALL_IMAGE_DIR/$filebase.jpg
	fi
done
zip -r $base-$DATE.zip $HOCR_OUTPUT_DIR/
ln -s $base-$DATE.zip $OCR_OUTPUT_DIR/Zips/$base-$DATE.zip
