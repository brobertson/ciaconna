#!/bin/bash
#download the file
#Download and preprocess the text images and data if they aren't downloaded yet
#binarization_threshold="-t 0.7"
#TODO: remove preprocessing, as scantailor is not reliable
#       remove ops that don't specifically pertain to this task
#      check for xml validity of metadata file
columns_command=""
verbose=false
ARCHIVE_ID=""
FILENAME=""
FILE_TO_PROCESS=""
metadata_command=""
days=1
#must be an integer 
gb_memory=2
PPI=500
migne_command=""
scantailor_command=""
tess_command=""
NUMBER_OF_CORES=8
while getopts "l:c:t:v:a:f:d:m:M:P:R:r:s:inT" opt; do
  case $opt in
    v)
      delete_string=""
      verbose=true
    ;;
    c)
      columns_command="-c \"$OPTARG\""
      echo "columns command is: $columns_command"
    ;;
    t)
      binarization_threshold="-t $OPTARG"
      echo "binarization threshold is: $binarization_threshold"
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
    m)
     metadata_command="-m $OPTARG"
     echo "metadata file is $OPTARG"
     METADATA_FILE="$OPTARG"
     if [ ! -f "$METADATA_FILE" ]; then
       echo "metadata file "$METADATA_FILE" does not exist"
       exit 1
     fi
     metadata_command="-m $(readlink -m "$METADATA_FILE")"
    ;;
    M) 
     gb_memory="$OPTARG"
     echo "set memory to $gb_memory GB"
    ;;
    P)
     NUMBER_OF_CORES=$OPTARG
     echo "using $NUMBER_OF_CORES cores in parallel processes"
     if [[ $var =~ ^-?[0-9]+$ ]]; then
       echo "$NUMBER_OF_CORES is not an integer"
       exit 1
     fi
    ;;
    R)
      PPI=$OPTARG
    ;;
    r)
     days=$OPTARG
     echo "duration set to $days days"
     re='^[0-9]+$'
     if ! [[ $days =~ $re ]] ; then
        echo "error: -r must be followed by an integer. $days is not a number." >&2; exit 1
     fi
     ;;
    s)
     DICTIONARY_FILE=$OPTARG
     if [ ! -f "$DICTIONARY_FILE" ]; then
       echo "dictionary file $DICTIONARY_FILE does not exist"
       exit 1
     fi
    ;;
    T)
	    tess_command=" -T "
	    echo "running this job with tesseract"
	    ;;
    i)
     migne_command=" -i "
     echo "migne command is $migne_command"
    ;;
    n)
     scantailor_command=" -n "
     echo "scantailor command is $scantailor_command"
    ;;
  esac
done


#if [ ! -f "$CLASSIFIER_FILE" ]; then
#  echo "classifier file $CLASSIFIER_FILE does not exist"
#  exit 1
#fi

if [ ! -d "$OCR_INPUT_DIR" ]; then
  echo "Please set environment variable 'OCR_INPUT_DIR' to a valid directory: directory '$OCR_INPUT_DIR' does not exist."
  exit 1
fi

if [ ! -d "$OCR_LOG_DIR" ]; then
  echo "Please set environment variable 'OCR_LOG_DIR' to a valid directory: directory '$OCR_LOG_DIR' does not exist."
  exit 1
fi


#set date
FOO=${DATE:=`date +%F-%H-%M-%S`}
OUTPUT_DIR=$(mktemp -d /tmp/temp.$ARCHIVE_ID.$DATE.XXXXXXXX) || { echo "failed to create temp file"; exit 1;}
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
    wget  --no-check-certificate http://www.archive.org/download/${ARCHIVE_ID}/${ARCHIVE_ID}_meta.xml
    metadata_command="-m ${OCR_INPUT_DIR}/${ARCHIVE_ID}_meta.xml"
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
LOG_FILE=$OCR_LOG_DIR/${DATE}_${ARCHIVE_ID}_output.txt
ERROR_FILE=$OCR_LOG_DIR/${DATE}_${ARCHIVE_ID}_error.txt
echo "using log file $LOG_FILE"
echo "using error log file $ERROR_FILE"
rm -rf $OUTPUT_DIR
echo "I'm running sbatch in the following dir: `pwd`"
#submit the job
#in this version, we will make a new shell file for the actual job
#sqsub --mpp=${gb_memory}G -o $LOG_FILE -e $ERROR_FILE -r ${days}d -q serial --mail-start --mail-end   /home/broberts/ciaconna/bin/ocropus_batch.sh -a $FILE_TO_PROCESS -d $DATE -l $CLASSIFIER_FILE $binarization_threshold $columns_command $metadata_command $migne_command -R $PPI -s $DICTIONARY_FILE $scantailor_command

# A  time  limit  of  zero  requests  that no time limit be imposed.  Acceptable time formats include "minutes", "minutes:seconds", "hours:min‐
#              utes:seconds", "days-hours", "days-hours:minutes" and "days-hours:minutes:seconds".

sbatch --ntasks $NUMBER_OF_CORES --mem-per-cpu ${gb_memory} --time ${days}-0 -J ${ARCHIVE_ID}_${DATE} -o $LOG_FILE -e $ERROR_FILE $CIACONNA_HOME/bin/ocropus_batch.sh -P $NUMBER_OF_CORES -a $FILE_TO_PROCESS -d $DATE -l $CLASSIFIER_FILE $binarization_threshold $columns_command $metadata_command $migne_command -R $PPI -s $DICTIONARY_FILE $scantailor_command $tess_command
