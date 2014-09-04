#
# Removal of title and inter-column letters for Patrologia Graeca
#
# Christoph Dalitz, Bruce Robertson, Fabian Schmitt (2013)
#
# Version    Date     Changes
#   1.0   2013/12/02  first creation
#   1.1   2023/12/04  removed restriction that center letters be large
#                     (fails for broken letters)
#                     removed restriction that bottom title be very near center
#                     (fails for not centered pages)
#   1.2   2013/12/09  new options -cr and -rb
#   2.0   2013/12/19  middle column now found with Hough transform
#                     capital Latin letters in middle column detected
#                     with training data and distance rejection 
#   2.1   2014/01/04  command line options for title and footnote removal
#   3.0   2014/01/09  textual information additionally printed into CSV file
#                     inter-column letters classified as 'A' to 'D'
#                     colors for RGB output easily changable as variable
#   3.1   2014/01/13  feature nrows weighted with 1/mheight
#                     => more robust to variations in font size or resolution
#

from gamera.core import *
from gamera.plugins import *
from gamera.plugins.listutilities import median
from gamera import knn

import math
import time
import sys
import os

# colors for RGB output
rgbcolors = { "header": RGBPixel(0,255,0),          # green
              "footnotetitle": RGBPixel(0,230,230), # cyan
              "footnotetext": RGBPixel(50,50,255),  # blue
              "A": RGBPixel(255,235,0),             # yellow
              "B": RGBPixel(255,140,0),             # orange
              "C": RGBPixel(255,0,0),               # red
              "D": RGBPixel(128,0,0) }              # maroon
        
infiles = []
opt_rc = True
opt_rb = True
opt_rs = False
opt_rt = True
opt_verbose = False
opt_st = False
opt_fn = False 
opt_outdir = "."
opt_trainfile = None

usagemsg = "Usage:\n\t" + sys.argv[0] + " [Options] <infile1> [<infile2> ...]\n" +\
    "Options:\n" +\
    "\t-tf <xmlfile>\n" +\
    "\t      Gamera training file containing only the capital letters (A-D)\n" +\
    "\t-od <dir>\n" +\
    "\t      output directory\n" +\
    "\t-ncr  do *not* correct rotation\n" +\
    "\t-nrb  do *not* remove black copy border\n" +\
    "\t-nrt  do *not* remove title\n" +\
    "\t-fn   remove footnotes\n" +\
    "\t-rs   use runlength smearing instead of bbox merging\n" +\
    "\t      for title extraction (slower but maybe more robust to skew)\n" +\
    "\t-st   preprocessed with scantailer\n" +\
    "\t-v    verbose (writes images 'step*.png')\n"

# parse commandline
i = 1
while i < len(sys.argv):
    if sys.argv[i] == "-rs":
        opt_rs = True
    elif sys.argv[i] == "-od":
        i += 1; opt_outdir = sys.argv[i]
    elif sys.argv[i] == "-tf":
        i += 1; opt_trainfile = sys.argv[i]
    elif sys.argv[i] == "-nrc":
        opt_rc = False
    elif sys.argv[i] == "-nrb":
        opt_rb = False
    elif sys.argv[i] == "-nrt":
        opt_rt = False
    elif sys.argv[i] == "-fn":
        opt_fn = True
    elif sys.argv[i] == "-v":
        opt_verbose = True
    elif sys.argv[i] == "-st":
        opt_st = True
        opt_rb = False
        opt_rc = True
    elif sys.argv[i][0] == "-":
        sys.stderr.write(usagemsg)
        sys.exit(1)
    else:
        infiles.append(sys.argv[i])
    i += 1
if not opt_trainfile:
    sys.stderr.write("Error: no training file given\n")
    sys.stderr.write(usagemsg)
    sys.exit(1)
if not os.path.exists(opt_trainfile):
    sys.stderr.write("Error: file '" + opt_trainfile + "' not found\n")
    sys.stderr.write(usagemsg)
    sys.exit(1)
if not os.path.exists(opt_outdir) or not os.path.isdir(opt_outdir):
    sys.stderr.write("Error: directory '" + opt_outdir + "' not found\n")
    sys.stderr.write(usagemsg)
    sys.exit(1)
if len(infiles) == 0:
    sys.stderr.write(usagemsg)
    sys.exit(1)
for f in infiles:
    if not os.path.exists(f):
        sys.stderr.write("Error: file '" + f + "' not found\n")
        sys.stderr.write(usagemsg)
        sys.exit(1)
    

#=======================================================
# utility functions
#=======================================================

# bbox_to_csv:
#   prints bbox coordinates of rect for CSV output
#   when rect is None, header information is returned
#-------------------------------------------------------
def bbox_to_csv(rect = None):
    if rect is None:
        return "ul_x;ul_y;ll_x;ll_y;lr_x;lr_y;ur_x;ur_y"
    else:
        return str(rect.ul_x) + ";" + str(rect.ul_y) + ";" + \
            str(rect.ll_x) + ";" + str(rect.ll_y) + ";" + \
            str(rect.lr_x) + ";" + str(rect.lr_y) + ";" + \
            str(rect.ur_x) + ";" + str(rect.ur_y)

# hough_lines:
#   finds the dominant approx. vertical lines
#   returns the top and bottom x-coords of 2*aol lines
#-------------------------------------------------------
def hough_lines(ccs, img, sidespace, aol=2):
    
    #init parameters
    all_points = []
    points_left = []
    points_right = []
    upper_edges = []
    lower_edges = []

    h = img.height
    w = img.width
    r_max = (h*h + w*w)**0.5

    nAng = 40
    nRad = int(r_max)   #probably less nRad will do it

    t_min = -0.15
    t_max = 0.15

    d_ang = (t_max - t_min) / float(nAng)
    d_rad = r_max / float(nRad)

    sin_t = [math.sin(t_min + t * d_ang)for t in range(0,nAng)]
    cos_t = [math.cos(t_min + t * d_ang)for t in range(0,nAng)]

    th = sidespace
    for cc in ccs:
        #six points of interest
        #----------------------------------
        left_top = Point(cc.ul_x,cc.ul_y)
        left_center = Point(cc.ul_x, cc.ul_y + cc.height / 2)
        left_bottom = Point(cc.ul_x, cc.ul_y + cc.height)
        right_top = Point(cc.ul_x + cc.width, cc.ul_y)
        right_center = Point(cc.ul_x + cc.width, cc.ul_y + cc.height / 2)
        right_bottom = Point(cc.ul_x + cc.width, cc.ul_y + cc.height)

        #left 
        #----------------------------------
        dist_center_left = img.runlength_from_point(left_center,"white","left")
        dist_top_left = img.runlength_from_point(left_top,"white","left")
        dist_bottom_left = img.runlength_from_point(left_bottom,"white","left")
        dist_left = min([dist_center_left, dist_top_left, dist_bottom_left])
            
        if (dist_left > th) or ((opt_st == True) and (cc.ul_x - dist_left <= 1)):
            points_left.append(left_center)
            points_left.append(left_top)
            points_left.append(left_bottom)
        
        #right  
        #----------------------------------
        dist_top = img.runlength_from_point(right_top,"white","right")
        dist_center = img.runlength_from_point(right_center,"white","right")
        dist_bottom = img.runlength_from_point(right_bottom,"white","right")
        dist_right = min([dist_center, dist_top, dist_bottom])
        
        if (dist_right > th) or ((opt_st == True) and (w - cc.lr_x - dist_right <= 1)):
            points_right.append(right_center)
            points_right.append(right_top)
            points_right.append(right_bottom)
    
    all_points.append(points_left)
    all_points.append(points_right)
    
    for point_array in all_points:
        acc = [[0 for x in range(nAng)] for y in range(nRad)]
    
        #create Accumulator array
        #----------------------------------
        for point in point_array:
            u = point.x
            v = point.y
    
            for ia in range(0,nAng):
                ir = int(round((u * cos_t[ia] + v * sin_t[ia]) / d_rad))
        
                if(ir >= 0 and ir < nRad):
                    acc[ir][ia] += 1

        loc_max =  [0 for x in range((nAng+1) * (nRad+1))]
        loc_max_r = [0 for x in range((nAng+1) * (nRad+1))]
        loc_max_a =  [0 for x in range((nAng+1) * (nRad+1))]
    
        #create local maxima array
        #----------------------------------
        for one in range(len(acc)): #index rad
            for another in range(len(acc[one])):#index ang
                #top neighbor
                #----------------------------------
                if(one != 0):
                    if(acc[one - 1][another] > loc_max[another * nRad + one]):
                        loc_max[another * nRad + one] = acc[one - 1][another]
                        loc_max_r[another * nRad + one] = one
                        loc_max_a[another * nRad + one] = another
                #left neighbor
                #----------------------------------
                if(another != 0):
                    if(acc[one][another - 1] > loc_max[another * nRad + one]):
                        loc_max[another * nRad + one] = acc[one][another - 1]
                        loc_max_r[another * nRad + one] = one
                        loc_max_a[another * nRad + one] = another
                #bottom neighbor
                #----------------------------------
                if(one != nRad - 1):
                    if(acc[one + 1][another] > loc_max[another * nRad + one]):
                        loc_max[another * nRad + one] = acc[one + 1][another]
                        loc_max_r[another * nRad + one] = one
                        loc_max_a[another * nRad + one] = another
                #right neihgbor
                #----------------------------------
                if(another != nAng - 1):
                    if(acc[one][another + 1] > loc_max[another * nRad + one]):
                        loc_max[another * nRad + one] = acc[one][another + 1]
                        loc_max_r[another * nRad + one] = one
                        loc_max_a[another * nRad + one] = another
            
                #is the values of the actual point higher than the highest of its 4 neigbors?
                #----------------------------------
                if(acc[one][another] > loc_max[another * nRad + one]):
                    loc_max[another * nRad + one] = acc[one][another];
                    loc_max_r[another * nRad + one] = one
                    loc_max_a[another * nRad + one] = another
                else:
                    loc_max[another * nRad + one] = 0
                    loc_max_r[another * nRad + one] = 0
                    loc_max_a[another * nRad + one] = 0
    
        irad = -w / 4
        loc_max_cpy = list(loc_max)
        loc_max.sort()
    
        #finding the lines
        #----------------------------------
        for line in range(0,aol):
            maxima = loc_max_cpy.index(loc_max.pop())
            new_rad = loc_max_r[maxima]
            while(abs(new_rad - irad) < w * 0.25):
                maxima = loc_max_cpy.index(loc_max.pop())
                new_rad = loc_max_r[maxima]
                loc_max_cpy[maxima] = 0
            iang = loc_max_a[maxima]
            irad = new_rad
        
            ang = iang * d_ang + t_min
            rad = irad * d_rad

            edges = []
            """y = (p * x) + q """
            """x = (y - q) / p """

            sin_ang = sin_t[iang]
            cos_ang = cos_t[iang]
            if(abs(sin_ang) > 0.000001):
                p = -1.0 * cos_ang /sin_ang
                q = float(rad) / sin_ang
                if(abs(p) > 0.000001):
                    #other lines
                    #----------------------------------
                    #probably y = 0 and y = h-1 will do in nearly horizontal lines
                    edges.append(Point(0,int(round(q))))
                    edges.append(Point(int(round(-q/p)),0))
                    edges.append(Point(w-1, int(round(p*(w-1) + q))))
                    edges.append(Point(int(round(((h-1)-q)/p)),h-1))
                else:
                    #horizontal line
                    #----------------------------------
                    edges.append(Point(0,int(rad)))
                    edges.append(Point(w,int(rad)))
            else:
                #vertical line
                #----------------------------------
                edges.append(Point(int(rad),0))
                edges.append(Point(int(rad),h))

            #taking two points, that cut the image boundaries
            #----------------------------------
            to_del = []
            for e in edges:
                if(e.x > w or e.x < 0 or e.y > h or e.y < 0):
                    to_del.append(e)
            for e in to_del:
                edges.remove(e)
            
            if(edges[0].y == 0):
                upper_edges.append(edges[0].x)
            else:
                lower_edges.append(edges[0].x)
            
            if(edges[1].y == 1):
                upper_edges.append(edges[1].x)
            else:
                lower_edges.append(edges[1].x)
            
    upper_edges.sort()
    lower_edges.sort()

    return (upper_edges, lower_edges)


#=======================================================
# here starts the main program
#=======================================================

init_gamera()


# loop over input files
#------------------------------------
import os
for infile in infiles:

    # extensionless basename of file
    filebase = os.path.basename(infile)
    filename = os.path.splitext(filebase)[0]

    bboxdata = "name;" + bbox_to_csv() + "\n"

    # load image and basic preprocessing
    #------------------------------------
    origimg = load_image(infile)
    img = origimg.to_onebit()
    if opt_rb:
        img.remove_border()
    if opt_rc:
        (angle, accuracy) = img.rotation_angle_projections(-5,5)
        if abs(angle) > accuracy:
            #print "rotation of", angle, "detected: rotate image"
            img = img.rotate(angle)

    # compute some statistics
    #------------------------------------
    ccs = img.cc_analysis()
    mheight = median([cc.nrows for cc in ccs])
    mwidth = median([cc.ncols for cc in ccs])
    print "mheight: ", mheight, "; mwidth: ", mwidth
    # more preprocessing: remove big black fragments
    to_remove = []
    for cc in ccs:
        if(cc.height > mheight * 5):
            img.draw_filled_rect(cc.ul,cc.lr,0)
            to_remove.append(cc)
            #print cc.ul
    for cc in to_remove:
        ccs.remove(cc)
        
    # locate middle column
    (upper_edges, lower_edges) = hough_lines(ccs, img, sidespace=mwidth*4)
    all_lines = [min(upper_edges[1],lower_edges[1]),
                 max(upper_edges[2], lower_edges[2])]
    center_x = (all_lines[0] + all_lines[1]) / 2
    bboxdata += "columnsep;" + str(upper_edges[1]) + ";0;" + \
        str(lower_edges[1]) + ";" + str(img.height) + ";" + \
        str(lower_edges[2]) + ";" + str(img.height) + ";" + \
        str(upper_edges[2]) + ";0\n"
    if opt_verbose:
        tmp_rgb = img.to_rgb()
        for i in range(len(upper_edges)):
            tmp_rgb.draw_line(Point(upper_edges[i],0), Point(lower_edges[i],img.nrows-1), RGBPixel(255,0,255), 3)
        tmp_rgb.save_PNG("step1_lines4columns.png")


    # segment image into lines/words
    #------------------------------
    img.reset_onebit_image() # undo CC labeling
    rgb = img.to_rgb()
    if opt_rs:
        allwords = img.runlength_smearing(Cx=(mwidth*20), Cy=(mheight*2), Csm=mwidth)
    else:
        allwords = img.bbox_merging(Ex=(mwidth*5), Ey=0)
    
    if opt_verbose:
        tmp_rgb = img.graph_color_ccs(allwords)
        for w in allwords:
            tmp_rgb.draw_hollow_rect(w, RGBPixel(255,0,0))
        tmp_rgb.save_PNG("step2_boxes4title.png")
    ## ignore noise (probably crude => improve)
    #words = []
    #for w in allwords:
    #    words.append(w)
    words = allwords


    # find title: top line
    #------------------------------------------------
    if opt_rt:
        headerccs = []
        words.sort(lambda s1, s2: s1.ul_y-s2.ul_y)
        # top words
        first = None
        # find center title
        center_i = -1
        for i, w in enumerate(words):
            if(w.contains_x(center_x) and w.ncols > 4*mwidth) or (w.contains_x(all_lines[1]) and w.ncols > 4*mwidth) or (w.contains_x(all_lines[0]) and w.ncols > 4*mwidth):
                center_i = i
                rgb.highlight(w, rgbcolors["header"])
                headerccs.append(w)
                w.fill_white()
                break

        # remove every word that overlaps with center title
        center_w = words[center_i]
        for i in range(center_i - 1,-1,-1): # backward to front
            w = words[i]
            if w.intersects_y(center_w):
                rgb.highlight(w, rgbcolors["header"])
                headerccs.append(w)
                w.fill_white()
            else:
                break
        for i in range(center_i + 1, len(words)): # forward to end
            w = words[i]
            if w.intersects_y(center_w):
                rgb.highlight(w, rgbcolors["header"])
                headerccs.append(w)
                w.fill_white()
            else:
                break
        if len(headerccs) > 0:
            bboxdata += "header;" + \
                bbox_to_csv(headerccs[0].union_rects(headerccs)) + "\n"

    # find footnote and its title:
    # assumption: footnote title is centered on bottom half in the
    # search_fraction strip, everything below footnote title is footnote
    #-------------------------------------------------------------------
    if opt_fn:
        if opt_rs:
            img.reset_onebit_image() # undo labeling
            words = img.bbox_merging(Ex=(mwidth*5), Ey=0)
            words.sort(lambda s1, s2: s1.ul_y-s2.ul_y)
            if opt_verbose:
                tmp_rgb = img.graph_color_ccs(words)
                for w in words:
                    tmp_rgb.draw_hollow_rect(w, RGBPixel(255,0,0))
        x_search_fraction = 0.6
        #How far down the page do we start looking for app. crit?
        y_search_fraction = 0.6
        search_region = Rect(Point(center_x - int(0.5*x_search_fraction*img.width),int(img.nrows * (1-y_search_fraction))), Point(Point(center_x + int(0.5*x_search_fraction*img.width),img.nrows-1)))

        if opt_verbose:
            tmp_rgb.draw_hollow_rect(search_region, RGBPixel(0,255,0))
            tmp_rgb.save_PNG("step3_boxes4footnotes.png")
        delta = 5 * mwidth
        found = False
        for w in words:
            if not found:
                ## this condition does not work when page not centered:
                if search_region.contains_rect(w) and \
                        w.ul_x < center_x and w.lr_x > center_x and\
                        w.ncols > (mwidth * 10):
                        # and abs(img.center_x-w.center_x) < delta
                    rgb.highlight(w,rgbcolors["footnotetitle"])
                    w.fill_white()
                    found = True
            else:
                rgb.highlight(w, rgbcolors["footnotetext"])
                w.fill_white()

        img.reset_onebit_image()


    # find letters 'A' to 'D' in inter-column space
    #------------------------------------------------------------------
    vert_delta_top = mheight * 2
    vert_delta_bottom = mheight * 5
    #Tuned to NJP pdfs
    ext = int (mwidth/3.5 + 0.5) #int(mwidth*2.0/3.0 + 0.5)
    ccs = img.bbox_merging(ext,ext,iterations=1)
    if opt_verbose:
        tmp_rgb = img.graph_color_ccs(ccs)
        for w in ccs:
            tmp_rgb.draw_hollow_rect(w, RGBPixel(255,0,0))
        tmp_rgb.save_PNG("step4_boxes4middlecol.png")

    glyphs = []
    for cc in ccs:
        factor = float(cc.center_y) / float(img.height)
                
        leftside_x =  upper_edges[1] - factor * (upper_edges[1] - lower_edges[1])
        rightside_x = upper_edges[2] - factor * (upper_edges[2] - lower_edges[2])
        
        if cc.center_x < rightside_x and cc.center_x > leftside_x:
            glyphs.append(cc)
    glyphs.sort(lambda s1, s2: s1.ul_y-s2.ul_y)


    # initialize classifier
    classifier = knn.kNNInteractive([],["moments","volume64regions","nrows_feature","aspect_ratio"],0)
    classifier.set_weights_by_feature("nrows_feature",[1/float(mheight)])
    classifier.num_k = 3
    classifier.from_xml_filename(opt_trainfile)
    classifier.confidence_types = [CONFIDENCE_AVGDISTANCE]

    # compute rejection threshhold
    stats = classifier.knndistance_statistics()
    d_t = 1.2 * max([s[0] for s in stats])

    # classification with distance reject
    classifier.classify_list_automatic(glyphs)
    for g in glyphs:
        if g.get_confidence(CONFIDENCE_AVGDISTANCE) < d_t:
            characterclass = g.get_main_id().upper()
            rgb.highlight(g, rgbcolors[characterclass])
            bboxdata += characterclass + ";" + bbox_to_csv(g) + "\n"
            g.fill_white()

    rgb.save_PNG(os.path.join(opt_outdir, filename + "_rt_result_rgb.png"))
    img.save_PNG(os.path.join(opt_outdir, filename + "_rt_result.png"))
    f = open(os.path.join(opt_outdir, filename + "_rt_result.csv"), "w")
    f.write(bboxdata)
    f.close()
