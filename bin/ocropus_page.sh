#!/bin/bash -e

usage(){
	echo "Usage: $0 -l classifier_model -o output_filename [-v -p] input_filename"
	echo "-v verbose output"
	echo "-p Image has already been processed, useful for paralleling output"
	exit 1
}

delete_string=" &> /dev/null "
verbose=false
image_is_preprocessed=""
columns_command=""
#Get the args
while getopts ":l:o:C:c:vp" opt; do
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
	    columns_command="--maxcolseps $OPTARG"
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


fbname=`basename "$1"`
if $verbose ; then
	echo $fbname
fi

barefilename=${fbname%.*}
extension="${fbname##*.}"
if $verbose ; then
echo $barefilename
fi
process_dir=`mktemp -d --suffix=$barefilename`
process_file=$1
#echo preprocessed? $image_is_preprocessed
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
#PG likes a 0.7 threshold, slightly darker than standard 0.5
eval ocropus-nlbin $process_file -t 0.7 -o $process_dir $delete_string
eval ocropus-gpageseg -b --maxseps 1 $columns_command  $process_dir'/????.bin.png' #$delete_string
#end condition of process_dir existing
process_dir_for_classifier=`mktemp -d`
cp -a $process_dir/* $process_dir_for_classifier 
eval ocropus-rpred   $model_command $process_dir_for_classifier'/????/??????.bin.png' $delete_string
eval ocropus-hocr $process_dir_for_classifier'/????.bin.png' -o $output_filename $delete_string
rm -rf $process_dir_for_classifier > /dev/null
rm -rf $process_dir > /dev/null
#ocropus-visualize-results temp

