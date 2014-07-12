#!/bin/bash -e

usage(){
  echo "Usage: $0 -l classifier_model -o output_filename [-v -p] input_filename"
  echo "-v verbose output"
  echo "-p Image has already been processed, useful for paralleling output"
  exit 1
}

delete_string=" > /dev/null "
verbose=false
image_is_preprocessed=""
columns_command=" --threshold 0.4 --hscale 4 --csminheight 50000  --maxcolseps 1 "
binarization_threshold=" -t 0.7"
#Get the args
while getopts "e::l:o:C:c:t:vp" opt; do
  case $opt in
    v)
      delete_string=""
      verbose=true
    ;;
    p)
      image_is_preprocessed=true
    ;;
    o)
      output_filename=$OPTARG
    ;;
    c)
      columns_command=$OPTARG
      #echo "columns command at page is $columns_command"
    ;;
    t)
      binarization_threshold="-t $OPTARG"
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

if [ -z  $output_filename ]; then
  echo "Output file $output_filename not set"
  usage
fi

#Check that ocropus commands are accessible
if $verbose; then
  echo "Checking that the following ocropus scripts exist ..."
fi
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
echo "process_dir: $process_dir"
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
eval ocropus-nlbin $binarization_threshold $process_file -o $process_dir $delete_string

if [[ -x $file_preprocess_command ]]; then
   echo "performing $file_preprocess_command on $process_dir/*.bin.png"
   ( $file_preprocess_command  $process_dir/*.bin.png )
else
  if $verbose ; then 
    echo "file preprocess command $file_preprocess_command either is not a file or is not executable. Skipping ..."
  fi
fi

if $verbose ; then
  echo
  echo "Output from ocropus-gpageseg:"
fi
eval ocropus-gpageseg  $columns_command  $process_dir'/????.bin.png' $delete_string
#process_dir_for_classifier=`mktemp -d`
#cp -a $process_dir/* $process_dir_for_classifier

if $verbose ; then
  echo
  echo "Output from ocropus-rpred:"
fi
eval ocropus-rpred   $model_command $process_dir'/????/??????.bin.png' $delete_string

if $verbose ; then
  echo
  echo "Output from ocropus-hocr:"
fi
eval ocropus-hocr $process_dir'/????.bin.png' -o $output_filename $delete_string
rm -rf $process_dir > /dev/null

