#!/bin/bash -e

usage(){
  echo "Usage: $0 -l classifier_model -o output_filename [-v -p] input_filename"
  echo "-v verbose output"
  echo "-p Image has already been processed, useful for paralleling output"
  exit 1
}

#delete_string=" > /dev/null "
verbose=true
rpred_command=" --llocs --alocs -n -N -p 1 -Q 1"
image_is_preprocessed=""
single_column_command=" --threshold 0.4 --hscale 4 --csminheight 50000  --maxcolseps 1 "
columns_command=$single_column_command
migne_columns_command=" --threshold 0.4  --csminheight 1 --maxcolseps 5 "
binarization_threshold=" -t 0.7"
#by default, we don't check for an inverted image
binarization_command=" -n "
columns_bin="ocropus-gpageseg"
#Get the args
while getopts "e::l:o:C:c:t:vpm" opt; do
  case $opt in
    v)
      delete_string=""
      verbose=true
    ;;
    p)
      image_is_preprocessed=true
    ;;
    m)
      echo "using Migne-mode"
      columns_command=$migne_columns_command
      columns_bin="ocropus-gpageseg-migne"
    ;;
    o)
      output_filename=$OPTARG
     if  $verbose ; then
      echo "I have set output_filename to $output_filename"
     fi
    ;;
    c)
      columns_command=$OPTARG
      echo "columns command at page is $columns_command"
    ;;
    t)
      binarization_threshold="-t $OPTARG"
      echo "treshold is $binarization_threshold"
    ;;
    l)
      classifier=$OPTARG
      if [ ! -f $classifier ]; then
        echo "Model file $classifier does not exist"
        usage
      fi
      model_command='-m '$classifier
      if  $verbose ; then
        echo using model $classifier
      fi
    ;;
    C)
      compare_file=$OPTARG
      if [ ! -f $compare_file ]; then
        echo "comparand file $compare_file does not exist"
        usage
      fi
      compare_command=' -C '$compare_file
      if $verbose ; then
        echo using comparand $compare_file
      fi
    ;;
    e)
      file_preprocess_command=$OPTARG
      echo "preproces command is: $file_preprocess_command"
    ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      usage
    ;;
    :)
      echo "Option -$OPTARG requires an argument." >&2
      usage
    ;;
  esac
done

#Test the args
shift $(($OPTIND - 1))
if [ ! $# -gt 0 ]; then
  echo "no filename given"
  usage
fi

if $verbose ; then
  echo "outputfile $output_filename"
fi

#This formulation is apparently best way to check
#for set variable: http://stackoverflow.com/questions/3601515/how-to-check-if-a-variable-is-set-in-bash
if [ -z ${output_filename+x} ]; then
  echo "Output file $output_filename not set"
  usage
fi

output_filename_without_ex=${output_filename%.*}
migne_csv=$output_filename_without_ex.csv
migne_image=${output_filename_without_ex}_dr.png
#Check that ocropus commands are accessible
if $verbose; then
  echo "Checking that the following ocropus scripts exist ..."

for cmd in "ocropus-nlbin" "ocropus-gpageseg" "ocropus-rpred" "ocropus-hocr"; do
  if hash "$cmd" 2>/dev/null; then
    if $verbose ; then
      printf "%-10s" "$cmd"
      printf " OK\n"
    fi
  else
    printf "%-10s" "$cmd"
    printf "missing. Please install.\n"
    exit 1
  fi
done
fi

#Get stripped names to use in naming output, etc.
fbname=`basename "$1"`
if $verbose ; then
  echo
  echo "File basename: $fbname"
fi

barefilename=${fbname%.*}
extension="${fbname##*.}"
if $verbose ; then
  echo "Bare filename: $barefilename"
fi

#make a temporary directory for processing
process_dir=`mktemp -d --suffix=$barefilename`
if $verbose ; then
  echo
  echo "process_dir: $process_dir"
fi
process_file=$1

#Convert image to png if necessary
if [ "$extension" != "png" ]
then
  echo "converting $1 to $process_dir/$barefilename.png"
  eval convert $1 $process_dir/$barefilename.png $delete_string
  process_file=$process_dir/$barefilename.png
fi

if [[ -z "$fbname" ]]; then
  usage
  exit 1
fi
#Perform each step in the processing.
#PG likes a 0.7 threshold, slightly darker than standard 0.5
if $verbose ; then
  echo
  echo "Output from ocropus-nlbin:"
fi
eval ocropus-nlbin -Q 1 $binarization_command $binarization_threshold $process_file -o $process_dir $delete_string > /dev/null

if ! [[ $columns_command = "-b" ]]; then
	echo "applying 'remove vertical bars' process"
	preprocess_filename=`ls $process_dir/*.bin.png`
	preprocess_temp=$(mktemp)
	python $CIACONNA_HOME/bin/Python/remove_vertical_bars.py $preprocess_filename $preprocess_temp
	mv $preprocess_temp $preprocess_filename
fi

#if [[ -x $file_preprocess_command ]]; then
#   echo "performing $file_preprocess_command on $process_dir/*.bin.png"
#   ( $file_preprocess_command  $process_dir/*.bin.png )
#else
#  if $verbose ; then 
#    echo "file preprocess command $file_preprocess_command either is not a file or is not executable. Skipping ..."
#  fi
#fi


if [[ $columns_bin = "ocropus-gpageseg-migne" ]]; then
DALITZ_HOME=$CIACONNA_HOME/Migne
DALITZ_OUTPUT_DIR=$(mktemp -d)
input_file=$process_dir/*.bin.png
echo "Dalitz preprocess Output dir: $DALITZ_OUTPUT_DIR"
python $DALITZ_HOME/remove_title_3.1.py   -tf $DALITZ_HOME/midletters.xml -od $DALITZ_OUTPUT_DIR $input_file
#dir=$(dirname $file)
name=$(basename $input_file)
name_without_extension=${name%.*}

#overwrite the input file for further OCR processing
cp $DALITZ_OUTPUT_DIR/${name_without_extension}_rt_result.png $input_file
#also copy to html output dir
#cp $DALITZ_OUTPUT_DIR/${name_without_extension}_rt_result.png $migne_image
cp $DALITZ_OUTPUT_DIR/${name_without_extension}*csv  $migne_csv
fi
#end migne-specific block

if $verbose ; then
  echo
  echo "Output from $columns_bin:"
  echo "Columns command is: $columns_command"
fi
eval $columns_bin -Q 1  $columns_command  $process_dir'/????.bin.png' $delete_string
#process_dir_for_classifier=`mktemp -d`
#cp -a $process_dir/* $process_dir_for_classifier

if $verbose ; then
  echo
  echo "Output from ocropus-rpred:"
fi
eval ocropus-rpred $rpred_command $model_command $process_dir'/????/??????.bin.png' $delete_string

if $verbose ; then
  echo
  echo "Output from ocropus-hocr:"
fi
eval ocropus-hocr $process_dir'/????.bin.png' -w -o $output_filename $delete_string
#rm -rf $process_dir > /dev/null
echo "removed process dir $process_dir"
