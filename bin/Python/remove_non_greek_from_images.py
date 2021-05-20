#!/usr/bin/env python
import cv2
import numpy as np
import html, os, sys, argparse
from statistics import mean
from lxml import etree
from greek_tools_py3 import is_greek_string, is_number
from pathlib import Path

#parse the arguments 
parser = argparse.ArgumentParser(description='''Convert kraken hocr output so
                                 that word bounding boxes are very likely to enclose the words, plus some space.
                                 This removes all spans of class ocrx_word that
                                 have single space text content. Its output is
                                 namespaced XHTML.''') 
parser.add_argument('--hocrInputDir', help='Path to directory where source files are found', required=True)
parser.add_argument('--imageInputDir', help="Path to directory where source image files are found", required=True)
parser.add_argument('--outputDir', help='Path to directory where output is stored', required=True)
parser.add_argument("-v", "--verbose", help="increase output verbosity", default=False, action="store_true")
args = parser.parse_args()

def get_bbox_val(span, position):
    try:
        parts = html.unescape(span.get('title')).split(';')
        bbox_string = ""
        for part in parts:
            part = part.strip()
            if part.startswith('bbox'):
                bbox_string = part
        if bbox_string == "":
            print("couldn't find the bbox part!")
        return int(bbox_string.split(' ')[position+1])
    except Exception as e:
        print("Exception getting title element on span {}".format(etree.tostring(span)))
        print(e)
        raise

def chunker(seq, size):
    return (seq[pos:pos + size] for pos in range(0, len(seq), 1))

def delete_span(span,img,broaden=0):
    print("gonna be deleted: '{}' ".format(span.text))
    # Start coordinate, here (100, 50)
    # represents the top left corner of rectangle
    start_point = (get_bbox_val(span,0)-broaden, get_bbox_val(span,1))

    # Ending coordinate, here (125, 80)
    # represents the bottom right corner of rectangle
    end_point = (get_bbox_val(span,2)+broaden, get_bbox_val(span,3))

    # White color in BGR
    color = (255, 255, 255)

    # Line thickness of -1 px
    # Thickness of -1 will fill the entire shape
    thickness = -1
    img = cv2.rectangle(img, start_point, end_point, color, thickness)
    return img

def strip_non_greek_word_image_zones(treeIn,img):
    word_spans = treeIn.xpath("//html:span[@class='ocrx_word'] | //html:span[@class='ocr_word']",namespaces={'html':"http://www.w3.org/1999/xhtml"})
    #process first
    for word_triplet in chunker(word_spans,3):
        if (len(word_triplet) == 3):
            print("triplet length:", len(word_triplet))
            print("triplet: ",word_triplet[0].text, word_triplet[1].text, word_triplet[2].text)
            if (is_greek_string(word_triplet[1].text)):
                continue
            if is_number(word_triplet[1].text) or (len(word_triplet[1].text) < 4):
                print("is number or short: '{}'".format(word_triplet[1].text))
                #if either neighbour is greek, we'll give it a pass
                if not(is_greek_string(word_triplet[0].text) or is_greek_string(word_triplet[2].text)):
                    img = delete_span(word_triplet[1],img)
                else:
                    print("spared due to proximity to Greek")
                continue
            img = delete_span(word_triplet[1],img, broaden=5)
    #process last
    return img

if not(os.path.isdir(args.hocrInputDir)):
    print('Input directory "'+image_dNoNoNoNoir+'" does not exist.\n\tExiting ...')
    sys.exit(1)

#Create the output directory if it doesn't exist
try:
    if not os.path.exists(args.outputDir):
        os.makedirs(args.outputDir, exist_ok=True)
except Exception as e:
    print("Error on creating output directory '" + args.outputDir +
    "':\n\t" + str(e) + "\n\tExiting ...")
    sys.exit(1)

if (args.verbose):
    print("Hocr Input dir:", args.hocrInputDir)
    print("Image input dir:", args.imageInputDir)
    print("Output dir:", args.outputDir)

#everthing looks good. Let's loop over the html files in inputDir
xslt_to_xhtml = etree.XML('''\
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
   xmlns:html='http://www.w3.org/1999/xhtml'>

   <xsl:template match="*">
    <xsl:element name="html:{local-name(.)}">
      <xsl:apply-templates select="@*|*|text()"/>
       </xsl:element>
       </xsl:template>

       <xsl:template match="@*">
         <xsl:attribute name="{name(.)}"><xsl:value-of
         select="."/></xsl:attribute>
         </xsl:template>

         </xsl:stylesheet>''')
transform_to_xhtml = etree.XSLT(xslt_to_xhtml)

EXTENSIONS = ('.hocr','.html', '.htm')
XHTML_NAMESPACE = "http://www.w3.org/1999/xhtml"
for root, dirs, files in os.walk(args.hocrInputDir):
    for file_name in files:
        if file_name.endswith(EXTENSIONS):
            print('filename: ',file_name)
            print('barname:', Path(file_name).stem)
            print('basename: ',os.path.basename(file_name))
            img_filename = Path(file_name).stem + '.png'
            if not(os.path.isfile(os.path.join(args.imageInputDir,img_filename))):
                print("the corresponding image file is not here:",img_filename)
                print("skipping ...")
                continue
            print("trying to open image file")
            #img = cv2.imread(os.path.join(args.imageInputDir,img_filename))
            with open(os.path.join(args.hocrInputDir,file_name)) as file: # Use file to refer to the file
                try:
                    img_in = cv2.imread(os.path.join(args.imageInputDir,img_filename), cv2.IMREAD_UNCHANGED)
                    tree = etree.parse(file)
                    find_xhtml_body = etree.ETXPath("//{%s}body" % XHTML_NAMESPACE)
                    results = find_xhtml_body(tree)
                    xhtml = transform_to_xhtml(tree)
                    img_out = strip_non_greek_word_image_zones(xhtml,img_in)
                    #make mask of where the transparent bits are
                    #trans_mask = img_out[:,:,3] == 0

                    #replace areas of transparency with white and not transparent
                    #img_out[trans_mask] = [255, 255, 255, 255]

                    #new image without alpha channel...
                    #new_img = cv2.cvtColor(img_out, cv2.COLOR_BGRA2BGR)

                    #xhtml.write(os.path.join(args.outputDir,file_name),pretty_print=True, xml_declaration=True,   encoding="utf-8")
                    # Load the image
                    #src = cv2.imread(argv[1], 0)
                    # Check if image is loaded fine
                    #if src is None:
                    #    print ('Error opening image: ' + argv[1])
                    #    exit(1)
                    #src = cv2.imread("uiug.30112023840660-1583374486_0100.tif", 0)
                    #_, thresh = cv2.threshold(src,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
                    #thresh = cv2.bitwise_not(thresh)
                    #connectivity = 4  # You need to choose 4 or 8 for connectivity type
                    #num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(thresh , connectivity , cv2.CV_32S)
                    # Line thickness means fill
                    #thickness = 4
                    # color
                    #color=(0,0,0)
                    #outimage=src
                    #outpath = os.path.join(argv[2],basename)
                    #print("\toutput to", outpath)
                    cv2.imwrite(os.path.join(args.outputDir,img_filename),img_out)
                except Exception as e:
                    print("This exception was thrown on file {}".format(file_name))
                    print(e)
                    print("Exiting")
                    exit()

