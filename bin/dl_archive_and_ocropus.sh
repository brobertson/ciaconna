#!/bin/bash
#download the file 
#Download and preprocess the text images and data if they aren't downloaded yet
ARCHIVE_ID=$1
CLASSIFIER=$2

if [ ! -f $CLASSIFIER_FILE ]; then
        echo "classifier file $CLASSIFIER_FILE does not exist"
        exit 1 
fi

OCR_INPUT_DIR=/work/broberts/OCR_Input
DATE=`date +%F-%H-%M`
OUTPUT_DIR=$(mktemp -d /tmp/temp.$ARCHIVE_ID.$DATE.XXXXXXXX) || { echo "failed to create temp file"; exit 1;}
LOG_DIR=/work/broberts/OCR_Logs
cd $OCR_INPUT_DIR
if [ ! -e ${ARCHIVE_ID}_*.zip ]; then
echo "Attempting to download $ARCHIVE_ID from archive.org"
wget -nv --no-check-certificate --spider "http://www.archive.org/download/${ARCHIVE_ID}/${ARCHIVE_ID}_jp2.zip" 2>  ${OUTPUT_DIR}/response.txt
badDL=`grep '200 OK' ${OUTPUT_DIR}/response.txt | wc -l`
echo "status: $badDL"
  if [ "$badDL" == "0" ]; then
    echo "Attempting to download $ARCHIVE_ID tif from archive.org"
    wget -nv --no-check-certificate --spider "http://www.archive.org/download/${ARCHIVE_ID}/${ARCHIVE_ID}_tif.zip" 2>  ${OUTPUT_DIR}/response.txt
    badDL=`grep '200 OK' ${OUTPUT_DIR}/response.txt | wc -l`
    if [ "$badDL" == "0" ]; then
       echo "archive $ARCHIVE_ID not available. Exiting."
       exit 1
    else 
       wget  --no-check-certificate http://www.archive.org/download/${ARCHIVE_ID}/${ARCHIVE_ID}_tif.zip
    fi
  else
    wget  --no-check-certificate http://www.archive.org/download/${ARCHIVE_ID}/${ARCHIVE_ID}_jp2.zip 
  fi 
fi
#make the name of the log file 
LOG_FILE=$LOG_DIR/${ARCHIVE_ID}_${DATE}_output.txt
ERROR_FILE=$LOG_DIR/${ARCHIVE_ID}_${DATE}_error.txt
echo "using log file $LOG_FILE"
#submit the job
sqsub --mpp=2G -o $LOG_FILE -e $ERROR_FILE -r 4d -q serial --mail-start --mail-end /work/broberts/ciaconna/bin/ocropus_batch.sh $OCR_INPUT_DIR/${ARCHIVE_ID}_*.zip $CLASSIFIER
