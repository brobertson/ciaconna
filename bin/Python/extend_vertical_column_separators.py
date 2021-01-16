import cv2
import numpy as np
import os, sys
# [load_image]
# Check number of arguments
argv = sys.argv
if (len(argv) < 1):
    print ('Not enough parameters')
    print ('Usage:\nmorph_lines_detection.py < path_to_image >')
    exit(1)
# Load the image
src = cv2.imread(argv[1], 0)
# Check if image is loaded fine
if src is None:
    print ('Error opening image: ' + argv[1])
    exit(1)
#src = cv2.imread("uiug.30112023840660-1583374486_0100.tif", 0)
basename = os.path.basename(argv[1])
print(basename)
_, thresh = cv2.threshold(src,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
thresh = cv2.bitwise_not(thresh)
connectivity = 4  # You need to choose 4 or 8 for connectivity type
num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(thresh , connectivity , cv2.CV_32S)
# Line thickness means fill
thickness = 4 
# color
color=(0,0,0)
outimage=src
for i in range(num_labels):
    ratio = stats[i,cv2.CC_STAT_HEIGHT] / stats[i,cv2.CC_STAT_WIDTH]
    if (stats[i,cv2.CC_STAT_HEIGHT]> 50  and stats[i,cv2.CC_STAT_LEFT] > 800 and ratio > 10  ):
        print("\tfound a black column:",stats[i,cv2.CC_STAT_WIDTH], "x",stats[i,cv2.CC_STAT_HEIGHT], "at ", stats[i,cv2.CC_STAT_LEFT], stats[i,cv2.CC_STAT_TOP], "ratio",ratio)
        # Using cv2.rectangle() method
        image = cv2.line(src, (stats[i,cv2.CC_STAT_LEFT], stats[i,cv2.CC_STAT_TOP] -50), (stats[i,cv2.CC_STAT_LEFT] + stats[i,cv2.CC_STAT_WIDTH], stats[i,cv2.CC_STAT_HEIGHT] + stats[i,cv2.CC_STAT_TOP] + 50), color, thickness)
        #image = cv2.rectangle(src, (stats[i,cv2.CC_STAT_LEFT], stats[i,cv2.CC_STAT_TOP]), (stats[i,cv2.CC_STAT_LEFT] + stats[i,cv2.CC_STAT_WIDTH], stats[i,cv2.CC_STAT_HEIGHT] + stats[i,cv2.CC_STAT_TOP] - 50), color, thickness)
        # Displaying the image
        #cv2.imshow("ho", image)
        #cv2.waitKey(0)
        #cv2.destroyWindow(winname)
        outimage = image
        #cv2.imwrite('/tmp/out.png',image)
        #break
outpath = os.path.join(argv[2],basename)
print("\toutput to", outpath)
cv2.imwrite(outpath,outimage)
