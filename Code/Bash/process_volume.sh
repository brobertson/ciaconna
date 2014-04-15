#!/bin/bash
#export RIGAUDON_HOME=/home/broberts/rigaudon/
export DATE=`date +%F-%H-%M`
export ARCHIVE_ID=$1
export CLASSIFIER_FILE=$2
export TEXT_STAGING_DIR=/usr/local/OCR_Processing/Texts/

export PROCESSING_DIR=$TEXT_STAGING_DIR/$ARCHIVE_ID

#Download and preprocess the text images and data if they aren't downloaded yet
if [ ! -d $PROCESSING_DIR ]; then
  mkdir $PROCESSING_DIR
  cd $PROCESSING_DIR
  echo "Attempting to download $ARCHIVE_ID from archive.org"
  curl -IL "http://www.archive.org/download/${ARCHIVE_ID}/${ARCHIVE_ID}_jp2.zip" >  /tmp/response.txt 
  grep HTTP/1.1 /tmp/response.txt | tail -1 | grep 404
  badDL=$?
  echo "status: $badDL"
  if [ "$badDL" -eq "0" ]; then
    #the jp2 archive is not available, so we'll guess that it's tiff
    wget http://www.archive.org/download/${ARCHIVE_ID}/${ARCHIVE_ID}_tif.zip
  else
    wget  http://www.archive.org/download/${ARCHIVE_ID}/${ARCHIVE_ID}_jp2.zip
  fi
  wget http://www.archive.org/download/${ARCHIVE_ID}/${ARCHIVE_ID}_meta.xml
#  sleep 2
#  wget http://www.archive.org/download/${ARCHIVE_ID}/${ARCHIVE_ID}_abbyy.gz
  echo 'Uncompressing ...'
  gunzip *gz
  unzip *zip
  tar xvf *tar
fi 

filename=$(basename $CLASSIFIER_FILE)
export filename=${filename%.*}
echo 'filename: ', $filename
export barebookname=$ARCHIVE_ID
#${BOOK_NAME%%_*}
BOOK_DIR=`find -L $PROCESSING_DIR/*_jp2 $PROCESSING_DIR/*_tif  -maxdepth 0 -type d`
echo 'BOOK_DIR: ', $BOOK_DIR
export JPG_COLOR_IMAGES=$BOOK_DIR/${barebookname}_color
export PNG_IMAGES=$BOOK_DIR/${barebookname}_png
export HOCR_OUTPUT=$BOOK_DIR/${DATE}_${filename}_raw_hocr_output
export HOCR_SELECTED=$BOOK_DIR/${DATE}_${filename}_selected_hocr_output

export RELATIVE_HOCR_OUTPUT=${DATE}_${filename}_raw_hocr_output
export RELATIVE_HOCR_SELECTED=${DATE}_${filename}_selected_hocr_output

cd $BOOK_DIR
mv ../${ARCHIVE_ID}_meta.xml ./

if [ ! -d $PNG_IMAGES ]; then
 echo 'converting to png'
 mkdir $PNG_IMAGES
  parallel convert {} $PNG_IMAGES/{.}.png ::: *jp2 *tif *tiff *png 
fi

mkdir $HOCR_OUTPUT
mkdir $HOCR_SELECTED

echo 'submit to ocropus'
echo " processing `ls $PNG_IMAGES/*`"
echo "putting in $HOCR_OUTPUT"
cd $PNG_IMAGES
parallel $RIGAUDON_HOME/Scripts/ocropus_me.sh -l $CLASSIFIER_FILE -o $HOCR_OUTPUT/{.}.html {} ::: *png
#$RIGAUDON_HOME/SGE_Scripts/SGE_Gamera_Collection/process_collection.sh $PROCESSING_DIR $CLASSIFIER_DIR
cd $HOCR_OUTPUT 
rename 's/.html/_jp2_thresh_128.html/' *html
rename 's/^/output-/' *html
LACE_DIR=heml:/home/brucerob/Lace/

cd $BOOK_DIR

if [ ! -d $JPG_COLOR_IMAGES ]; then
 mkdir $JPG_COLOR_IMAGES
 parallel convert -quality 30 -depth 8 {}  $JPG_COLOR_IMAGES/{.}.jpg ::: *jp2 *tif *tiff *png

#for image_file in `ls *jp2 *tif *tiff *png`
#  do  
#    echo "making image for $image_file"
#    convert -quality 30 -depth 8 $image_file  $JPG_COLOR_IMAGES/${image_file%.*}.jpg
#  done
  scp -r $JPG_COLOR_IMAGES $LACE_DIR/static/Images/Color
fi

echo "done making color images"

echo  "does metadata file exist?"
ls ${barebookname}_meta.xml

cp $HOCR_OUTPUT/* $HOCR_SELECTED/
tar -zcf  $BOOK_DIR/robertson_${DATE}_${barebookname}_${filename}_full.tar.gz $RELATIVE_HOCR_OUTPUT  $RELATIVE_HOCR_SELECTED  ${barebookname}_meta.xml
cd -
cd $BOOK_DIR

scp  $BOOK_DIR/robertson_${DATE}_${barebookname}_${filename}_full.tar.gz $LACE_DIR/static/Lace_Resources/Inbox

echo "$BOOK_DIR $DATE done using $filename classifier. `ls $HOCR_SELECTED | wc -l` files created. Materials at http://heml.mta.ca/Lace/runs/${BOOK_DIR}." | mutt -s "$BOOK_DIR at sharcnet"  -- bruce.g.robertson@gmail.com

#rm -rf  $HOCR_OUTPUT
#rm -rf  $HOCR_SELECTED
