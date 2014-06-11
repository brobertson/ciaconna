#!/bin/bash
#download the file
#Download and preprocess the text images and data if they aren't downloaded yet
binarization_threshold="-t 0.7"
columns_command=""
verbose=false
ARCHIVE_ID=""
FILENAME=""
FILE_TO_PROCESS=""
while getopts "l:c:t:v:a:f:d:" opt; do
  case $opt in
    v)
      delete_string=""
      verbose=true
    ;;
    c)
      columns_command="-c $OPTARG"
    ;;
    t)
      binarization_threshold="-t $OPTARG"
    ;;
    l)
      CLASSIFIER_FILE=$OPTARG
    ;;
    a)
      ARCHIVE_ID=$OPTARG
      echo "archive id is $ARCHIVE_ID"
    ;;
    f)
      FILENAME=$OPTARG
      echo "process file is $FILENAME"
    ;;
    d)
      DATE=$OPTARG
      echo "date is $DATE"
    ;;

  esac
done

if [ ! -f $CLASSIFIER_FILE ]; then
  echo "classifier file $CLASSIFIER_FILE does not exist"
  exit 1
fi

OCR_INPUT_DIR=/work/broberts/OCR_Input
#set date
FOO=${DATE:=`date +%F-%H-%M`}
OUTPUT_DIR=$(mktemp -d /tmp/temp.$ARCHIVE_ID.$DATE.XXXXXXXX) || { echo "failed to create temp file"; exit 1;}
LOG_DIR=/work/broberts/OCR_Logs
cd $OCR_INPUT_DIR
if [ ! -z "$ARCHIVE_ID" ]; then
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
  FILE_TO_PROCESS=$OCR_INPUT_DIR/${ARCHIVE_ID}_*.zip
else # ARCHIVE_ID is unset, so we have our own filename
  echo "ARCHIVE_ID unset"
  if [ ! -e "$FILENAME" ]; then
    echo "process archive $FILENAME does not exist. Please set either -a or -f"
    exit 1
  else
    FILE_TO_PROCESS="$FILENAME"
    #set archive id here.
   echo "FILE_TO_PROCESS: $FILE_TO_PROCESS"
   file=${FILE_TO_PROCESS##*/}
   echo $file
   base=${file%.*}
   echo $base
   ARCHIVE_ID=${base%_*} 
   echo "ARCHIVE_ID: $ARCHIVE_ID"
  fi # end if [ ! -e "$FILENAME" ]
fi # end if [ ! -z "$ARCHIVE_ID" ]

#make the name of the log file
LOG_FILE=$LOG_DIR/${ARCHIVE_ID}_${DATE}_output.txt
ERROR_FILE=$LOG_DIR/${ARCHIVE_ID}_${DATE}_error.txt
echo "using log file $LOG_FILE"
rm -rf $OUTPUT_DIR
#submit the job
sqsub --mpp=2G -o $LOG_FILE -e $ERROR_FILE -r 4d -q serial --mail-start --mail-end  /work/broberts/ciaconna/bin/ocropus_batch.sh -a "$FILE_TO_PROCESS" -d $DATE -l $CLASSIFIER_FILE $binarization_threshold $columns_command
