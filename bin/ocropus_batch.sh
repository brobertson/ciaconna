	#!/bin/bash
	export PYTHONIOENCODING=UTF-8
	# We expect two args: the collection_dir and the classifier_dir
	USAGE_MESSAGE="Usage: ocropus_batch -v -c \"columns command\" -t binarization_threshold (default determined by ocropus defaults, usually 0.5) -a [pdf_file,zip file] -l classifier_file"
	E_BADARGS=65
	INPUT_FILE=$1
	CLASSIFIER_FILE=$2
	OCR_OUTPUT_DIR=/work/broberts/Output
	PPI=500
	binarization_threshold="-t 0.6"
	columns_command=""
	while getopts "l:c:t:v:a:d:m:R:" opt; do
	  case $opt in
	    v)
	      delete_string=""
	      verbose=true
	    ;;
	    c)
	      columns_command="$OPTARG"
	      echo "columns_command is $columns_command"
	    ;;
	    t)
	      binarization_threshold="-t $OPTARG"
	    ;;
	    l)
	      CLASSIFIER_FILE=$OPTARG
	    ;;
	    a)
	      INPUT_FILE=$OPTARG
	      echo "input file is $INPUT_FILE"
	    ;;
	    d)
	     DATE=$OPTARG
	     echo "using date $DATE"
	    ;;
	    m)
	      METADATA_FILE=$OPTARG
	      echo "using metadata file $METADATA_FILE"
	    ;;
	    R)
	     PPI=$OPTARG
	     echo "resolution set to $OPTARG PPI"
	    ;;
	  esac
	done

	echo "binarization threshold: $binarization_threshold"
	#check that env. variables are set
	[ -z "$CIACONNA_HOME" ] && { echo "Need to set CIACONNA_HOME env. variable"; exit 1; }

	if [ ! -d "$OCR_OUTPUT_DIR" ]; then
	  echo "Need to set OCR_OUTPUT_DIR env. variable"
	  exit 1
	fi

	#set date
	FOO=${DATE:=`date +%F-%H-%M`}
	echo "Using Date $DATE"

	if [ ! -f $CLASSIFIER_FILE ]; then
	  
	  echo "classifier file $CLASSIFIER_FILE does not exist"
	  echo $USAGE_MESSAGE
	  exit $E_BADARGS
	fi
	if [ ! -f "$INPUT_FILE" ]; then
	  echo "input file $INPUT_FILE does not exist"
	  echo $USAGE_MESSAGE
	  exit $E_BADARGS
	fi

	file=${INPUT_FILE##*/}
	echo "file $file"
	base=${file%.*}
	base=${base%_*}
	ext=${file##*.}


	if [ ! "$ext" == "pdf" ] && [ ! "$ext" == "zip" ]; then
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
	    echo "converting pdf to pngs"
	    mkdir $IMAGE_DIR
	    cd $IMAGE_DIR
	    /work/broberts/local/bin/pdfimages   -png -p $INPUT_FILE $base
	    #remove inconsequential images
	    find . -size -3500c -delete
	    i=1
	    for f in *.png; do
	       num=$(printf %04d $i)   #zero-pad "$i", if wanted
	       mv "$f" "${base}_$num.png"  #replace the orginal file ending with "$i.pdf"
	       let i++     #increment "$i" for the next file
	    done
	    echo "done converting pdf"
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
	  else
	    echo "directory $IMAGE_DIR already exists. Not decompressing archive."
	  fi
	fi
	classifier_file_base=$(basename $CLASSIFIER_FILE)
	INNER_HOCR_OUTPUT_DIR=${DATE}_${classifier_file_base}_raw_hocr_output
	INNER_SELECTED_DIR=${DATE}_${classifier_file_base}_selected_hocr_output
	HOCR_OUTPUT_DIR=$IMAGE_DIR/$INNER_HOCR_OUTPUT_DIR
	echo "HOCR_OUTPUT_DIR: $HOCR_OUTPUT_DIR"
	SELECTED_DIR=$IMAGE_DIR/$INNER_SELECTED_DIR
	if [ ! -d $HOCR_OUTPUT_DIR ]; then
	  echo "making hocr output dir"
	  mkdir $HOCR_OUTPUT_DIR
	  mkdir $SELECTED_DIR
	fi

	SMALL_IMAGE_DIR=$IMAGE_DIR/${base}_color
	echo "SMALL_IMAGE_DIR: $SMALL_IMAGE_DIR"
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
	    echo "hello there output file is: $HOCR_OUTPUT_DIR/$filebase.html"
	    echo "eval $CIACONNA_HOME/bin/ocropus_page.sh -v -m  $binarization_threshold  -l $CLASSIFIER_FILE -o $HOCR_OUTPUT_DIR/$filebase.html $image_file"
	    eval $CIACONNA_HOME/bin/ocropus_page.sh  -m  $binarization_threshold  -l $CLASSIFIER_FILE -o $HOCR_OUTPUT_DIR/$filebase.html $image_file 
	  else
	    echo "Skipping $HOCR_OUTPUT_DIR/$filebase.html It already exists."
	  fi
	  if [ ! -f $SMALL_IMAGE_DIR/$filebase.jpg ]; then
	    echo "creating $filebase.jpg"
	    convert $image_file -scale 30% $SMALL_IMAGE_DIR/$filebase.jpg
	  fi
	done
	echo "Classifier file base: $classifier_file_base"
	archive_name_base="robertson_${DATE}_${base}_${classifier_file_base}_full"

	cp "$IMAGE_DIR/*_tif/*.xml $IMAGE_DIR/*_jp2/*.xml" ./
	cp "$METADATA_FILE" ./${base}_meta.xml
	zip -r $archive_name_base.zip $HOCR_OUTPUT_DIR/ *.xml
	cd $HOCR_OUTPUT_DIR/..
	cp $HOCR_OUTPUT_DIR/* $SELECTED_DIR
	tar -czf $archive_name_base.tar.gz $INNER_HOCR_OUTPUT_DIR $INNER_SELECTED_DIR *.xml
	cd $OCR_OUTPUT_DIR/Zips
	ln -s $IMAGE_DIR/$archive_name_base.zip
	cd $OCR_OUTPUT_DIR/Tars
	ln -s $IMAGE_DIR/$archive_name_base.tar.gz
	cd $OCR_OUTPUT_DIR/Jpgs
	#if [ ! -d $SMALL_IMAGE_DIR ]; then
	ln -s $SMALL_IMAGE_DIR
	#fi

