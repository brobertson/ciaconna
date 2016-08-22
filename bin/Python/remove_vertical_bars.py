import sys
#import mahotas as mh
#import numpy as np
#from pylab import imshow, gray, show
#from os import path
#from gamera.plugins import numpy_io
from gamera.core import load_image
#from gamera.core import *
from gamera.plugins.listutilities import median

class ImageSegmentationError(Exception):
	def __init__(self, value):
		self.value = value
	def __str__(self):
		return repr(self.value)
		
def my_filter(imageIn):
	MAX_CCS = 8000
	count = 0
	image = imageIn
	#imageIn.remove_border()
	ccs = image.cc_analysis()
	print "filter started on",len(ccs) ,"elements..."
	if len(ccs) < 1:
		raise ImageSegmentationError("there are no ccs")
	if len(ccs) > MAX_CCS:
		raise ImageSegmentationError("there are more than " + str(MAX_CCS) + " ccs.")
	median_black_area = median([cc.black_area()[0] for cc in ccs])
	#filter long vertical runs left over from margins
	median_height = median([cc.nrows for cc in ccs])
	for cc in ccs:
		if((cc.nrows / cc.ncols > 6) and (cc.nrows > 1.5 * median_height) ):
			cc.fill_white()
			del cc
			count = count + 1

	for cc in ccs:
		if(cc.black_area()[0] > (median_black_area * 10)):
			cc.fill_white()
			del cc
			count = count + 1
	for cc in ccs:
		if(cc.black_area()[0] < (median_black_area / 10)):
			cc.fill_white()
			del cc
			count = count + 1
	print "filter done.",len(ccs)-count,"elements left."


def my_application():
   print sys.argv[1]
   image = load_image(sys.argv[1])
   image= image.to_onebit()
   my_filter(image)
   image.save_PNG(sys.argv[2])


from gamera.core import *
init_gamera()

my_application()
