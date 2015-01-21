# -*- coding: utf-8 -*-
from gamera.core import init_gamera
init_gamera()
import lxml
from lxml import etree
import sys
import codecs
from operator import itemgetter, attrgetter
DEBUG=False
import greek_tools
from copy import deepcopy

class hocrWord():
    """associates word text with bbox"""


class hocrLine():
    """Associates lines, words with their text and bboxes"""

    """Associates hocr lines with text origin"""

def evaluate_greekness(string_in):
   import re
   from greek_tools import is_greek_char
   import string
   regex = re.compile('[%s]' % re.escape(string.punctuation + u'—·' + u'0123456789'))
   string_in = regex.sub('',string_in,re.UNICODE)
   count = 0
   for char in string_in:
      if is_greek_char(char):
         count = count + 1
   length = len(string_in)
   if length == 0:
      factor = 0
   else:
      factor = float(count) / float(len(string_in))
   return factor

def parse_bbox(stringIn):
    from gamera.core import Rect
    from gamera.core import Point
    dimensions = stringIn.split()
    if not dimensions[0] == 'bbox' or not len(dimensions) == 5:
        raise ValueError('bounding box not in proper format: "%s"'%dimensions)
    a_rect = Rect(Point(int(dimensions[1]),int(dimensions[2])),Point(int(dimensions[3]),int(dimensions[4])))
    return (a_rect)#dimensions[1:])


def get_hocr_lines_for_tree(treeIn):

    root = treeIn.getroot()
    hocr_line_elements = treeIn.xpath("//html:span[@class='ocr_line'] | //span[@class='ocr_line']",namespaces={'html':"http://www.w3.org/1999/xhtml"})
    line_counter = 0
    lines_out = []
    all_words = []
    for hocr_line_element in hocr_line_elements:
        #print "line: ", line_counter, parse_bbox(hocr_line_element.get('title'))
        line_counter += 1
        words = hocr_line_element.xpath(".//html:span[@class='ocr_word'] | .//span[@class='ocr_word'] ",namespaces={'html':"http://www.w3.org/1999/xhtml"})
        word_counter = 0
        words_out = []
        for word in words:
           # print "\tword: ", word_counter, word.text, parse_bbox(word.get('title'))
            aWord = hocrWord()
            aWord.text = ""
            if word.text:
               aWord.text += word.text
            #get rid of any inner elements, and just keep their text values
            for element in word.iterchildren():
              if element.text:
                 aWord.text += element.text
              word.remove(element)
            #set the contents of the xml element to the stripped text
            word.text = aWord.text
            aWord.bbox = parse_bbox(word.get('title'))
            aWord.element = word
            words_out.append(aWord)
        aLine = hocrLine()
        all_words = all_words + words_out
        aLine.words = words_out
        aLine.element = hocr_line_element
        aLine.bbox = parse_bbox(hocr_line_element.get('title'))
        lines_out.append(aLine)
    return lines_out, all_words



def sort_bbox(words):
    words.sort( key=attrgetter('bbox.lr_y'))
    words.sort( key=attrgetter('bbox.lr_x'))
    words.sort(key=attrgetter('text'))
    return words

def openfile(filename):
   fileIn= codecs.open(filename,'r','utf-8')
   parser = etree.XMLParser(remove_blank_text=True)
   treeIn = etree.parse(fileIn, parser)
   return treeIn

def getkey(line,item_no):
   try:
      a = int(line.get('title').split()[item_no])
   except:
      a = -1 
   #print a
   return a

def getx(line):
   x = getkey(line,1)
   fl = int(x/600.0)
   #print x, fl
   return fl

def gety(line):
   return getkey(line,2)

def getx1(word):
   return getkey(word,1)

def gety1(word):
   return getkey(word,2)

def getx2(word):
   return getkey(word,3)

def gety2(word):
   return getkey(word,4)

tree = openfile(sys.argv[1])
container = tree.xpath("//html:div[@class='ocr_page'] | //div[@class='ocr_page']",namespaces={'html':"http://www.w3.org/1999/xhtml"})[0]
max_x = max(container,getx)
#print "max x", max_x
max_y = max(container, gety)
container[:] = sorted(container, key=gety)
container[:] = sorted(container, key=getx)
tree.write("new-data.xhtml")
lines = tree.xpath("//html:span[@class='ocr_line'] | //div[@class='ocr_line']",namespaces={'html':"http://www.w3.org/1999/xhtml"})
startxs = []
endxs = []
startys = []
endys = []
lengths = []
scale_factor = 20.0
for line in lines:
   startxs.append(int(getkey(line,1)/40.0))
   endxs.append(int(getkey(line,3)/40.0))
   startys.append(int(getkey(line,2)/40.0))
   endys.append(int(getkey(line,4)/40.0))
   lengths.append(int(getkey(line,3)/scale_factor) - int(getkey(line,1)/scale_factor))
page_bottom = max(endys)
from collections import Counter
c = Counter(startxs)
sorted_startxes = sorted(c.most_common(2),key=lambda a: a[0])
#print sorted_startxes
c = Counter(endxs)
sorted_endxes = sorted(  c.most_common(2),key=lambda a: a[0])
#print sorted_endxes
c = Counter(lengths)
#print "lengths:",sorted(  c.most_common(2),key=lambda a: a[0])
mode_length_scaled = c.most_common(1)[0][0]
#print "mode length", mode_length
leftleft = sorted_startxes[0][0]
leftright = sorted_endxes[0][0]
rightleft = sorted_startxes[1][0]
rightright = sorted_endxes[1][0]
#print '-'* leftleft + '|' + '=' * (leftright - leftleft) + '|'+ '-'*(rightleft - leftright) + '|' + '='*(rightright-rightleft) + '|' 
lines = tree.xpath("//html:span[@class='ocr_line'] | //div[@class='ocr_line']",namespaces={'html':"http://www.w3.org/1999/xhtml"})
new_lines = []
mode_length = (mode_length_scaled * scale_factor)
for line in lines:
   left_edge = getkey(line,1)/scale_factor
   if int(getkey(line,3)/scale_factor)  > int(1.3 * mode_length_scaled) + left_edge:
      right_chars = ''
      right_words = []
      left_chars = ''
      left_words = []
      for word in line:
         #print word.tag
         centre_x = int(getkey(word,1)) + (getkey(word,3)-getkey(word,1))/2.0 #+ getkey(word,3)/2
         if (centre_x) < (mode_length + left_edge * scale_factor):
            left_chars = left_chars + word.text
            left_words.append(word)
         else:
            right_chars = right_chars + word.text
            right_words.append(word)
        
      left_score = evaluate_greekness(left_chars)
      right_score = evaluate_greekness(right_chars)
      #print left_chars, left_score
      #print right_chars, right_score
      agg_score = left_score - right_score
      #print "agg_score", agg_score
      sided = False
      if agg_score > 0.7:
         sided = True
         left_greek = True
      elif agg_score < -0.7:
         sided = True
         left_greek = False
      else:
         sided = False

      if sided:
         #print "left greek?", left_greek
         #print "I'm sided"
         new_line = etree.Element("{http://www.w3.org/1999/xhtml}span")
         new_line.set('class','ocr_line')
         #print etree.tostring(new_line)
         for word in right_words:
            new_line.append(word)
         #print "line len:", len(new_line)
         attribute = "bbox " + str(getx1(min(new_line,key=getx1))) + " " + str(gety1(min(new_line,key=gety1))) + " " + str(getx2(max(new_line,key=getx2))) + " " + str(gety2(max(new_line,key=gety2)))
         new_line.set('title',attribute)
         new_lines.append(new_line)
         attribute = "bbox " + str(getx1(min(line,key=getx1))) + " " + str(gety1(min(line,key=gety1))) + " " + str(getx2(max(line,key=getx2))) + " " + str(gety2(max(line,key=gety2)))
         line.set('title',attribute)

div = tree.xpath("//html:div[@class='ocr_page'] | //div[@class='ocr_page']",namespaces={'html':"http://www.w3.org/1999/xhtml"})[0]
for line in new_lines:
   div.append(line)
#sort again
container = tree.xpath("//html:div[@class='ocr_page'] | //div[@class='ocr_page']",namespaces={'html':"http://www.w3.org/1999/xhtml"})[0]
max_x = max(container,getx)
#print "max x", max_x
max_y = max(container, gety)
container[:] = sorted(container, key=gety)
container[:] = sorted(container, key=getx)
htmlHead = tree.xpath("/html:html/html:head",namespaces={'html':"http://www.w3.org/1999/xhtml"})
if len(htmlHead) == 1:
   style = etree.SubElement(htmlHead[0], '{http://www.w3.org/1999/xhtml}style', type='text/css')
   style.text = """span.ocr_line {
  display:block;
}"""
#remove the <br>s
for bad in tree.xpath("//html:br",namespaces={'html':"http://www.w3.org/1999/xhtml"}):
    bad.getparent().remove(bad)
tree.write(sys.stdout, pretty_print=True, encoding="utf-8")
