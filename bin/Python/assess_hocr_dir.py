#!/usr/bin/python
# coding: utf-8
import lxml
from lxml import etree
import lxml.html.html5parser
import sys
import re
import codecs
import os
import unicodedata
import HTMLParser
from greek_tools import is_greek_string

def count_things(treeIn, totals):
        words = treeIn.xpath("//html:span[@class='ocr_word'] | //html:span[@class='ocrx_word'] | //span[@class='ocr_word']",namespaces={'html':"http://www.w3.org/1999/xhtml"})
        for word in words:
            totals['word_count'] = totals['word_count'] + 1
            if word.get("data-spellcheck-mode") == "None":
                totals['no_spellcheck_all'] = totals['no_spellcheck_all'] + 1
            if word.get('data-manually-confirmed') == 'true':
                totals['verified'] +=1
            if (word.text) and (is_greek_string(word.text)):
                totals['greek_word_count'] = totals['greek_word_count'] + 1
                if word.get("data-spellcheck-mode") == "None":
                    totals['no_spellcheck_greek_words'] = totals['no_spellcheck_greek_words'] + 1
                if word.get('data-manually-confirmed') == 'true':
                    totals['verified_greek_words'] += 1
        return totals

#print sys.argv[1]
try:
    dir_in = sys.argv[1]
    #print dir_in
    dir_in_list = os.listdir(dir_in)
except (IndexError, ValueError) as e:
    print e
    print "usage: assess_hocr_dir.py dir_in"
    exit()
totals = {
    "greek_word_count": 0,
    "word_count": 0,
    "no_spellcheck_all": 0,
    "no_spellcheck_greek_words": 0,
    "verified": 0,
    "verified_greek_words": 0
}
for file_name in dir_in_list:
        #print file_name
        if file_name.endswith('.html'):
                fileIn_name = os.path.join(dir_in,file_name)
                try:
                    fileIn= codecs.open(fileIn_name,'r','utf-8',errors='strict')
                except Exception as e:
                    pass #print "codec exception: ", e
		#print "checking", fileIn_name 
                try:
                    parser = etree.XMLParser(recover=True, ns_clean=True)
                    treeIn = etree.parse(fileIn, parser)
                    totals = count_things(treeIn, totals)
                    #print totals
                except lxml.etree.XMLSyntaxError as e:
                    pass #print "lxml error", e
#print "grand total:", totals
try:
    accuracy=(100-(100* totals['no_spellcheck_all'] / totals['word_count']))
    greek_accuracy=(100- (100 * totals['no_spellcheck_greek_words'] / totals['greek_word_count']))
    if (totals['word_count'] == 0):
        accuracy=0
        greek_accuracy=0
    verified_greek_word_pct=(100*totals['verified_greek_words'] / totals['greek_word_count'])
    verified_words_pct=(100*totals['verified'] / totals['word_count'])
    print("accuracy %02d%%, Greek acc. %02d%%; completed %02d%%, Greek completed %02d%%" % (accuracy, greek_accuracy, verified_words_pct, verified_greek_word_pct)) 
except ZeroDivisionError:
    print("accuracy %02d%%, Greek acc. %02d%%; completed %02d%%, Greek completed %02d%%" % (0,0,0,0))
    print("there was an error in calculating these results. Here is a dump of the totals:",totals)

