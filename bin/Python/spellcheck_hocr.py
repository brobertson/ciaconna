#!/usr/bin/python
# coding: utf-8
from gamera.core import init_gamera
init_gamera()
import lxml
from lxml import etree
import sys
import re
from greek_tools import preprocess_word, dump, split_text_token
import codecs
import os
import unicodedata
import HTMLParser
import yaml
html_parser = HTMLParser.HTMLParser()
spellcheck_dict = {}
euro_sign = unicode(u"\N{EURO SIGN}")
dir_in = sys.argv[2]
dir_out = sys.argv[3]
if  not os.path.isdir(dir_in) or not os.path.isdir(dir_out):
        print "usage: spellcheck.csv dir_in dir_out"
        exit()
##with codecs.open(sys.argv[1],'r','utf-8') as spellcheck_file:
##   dict_in = yaml.load(spellcheck_file)
##   for data in dict_in:
##           [original_form, replacement, frequency, spellcheck_mode]  = data
##           if spellcheck_mode != "False":
##                  spellcheck_dict[unicodedata.normalize('NFC',original_form)] = (unicodedata.normalize('NFC',replacement), frequency, spellcheck_mode)
##
with codecs.open(sys.argv[1],'r','utf-8') as spellcheck_file:
	for line in spellcheck_file:
		line = line.strip()
		#print line
		[original_form, replacement, frequency, spellcheck_mode] = line.split(euro_sign)
		#print original_form, replacement, spellcheck_mode
		if spellcheck_mode != "False":
                        spellcheck_dict[unicodedata.normalize('NFC',original_form)] = (unicodedata.normalize('NFC',replacement), frequency, spellcheck_mode)
print "dictionary length: ", len(spellcheck_dict)
print "reading dir ", sys.argv[2]

        
for file_name in os.listdir(dir_in):
        if file_name.endswith('.html'):
                simplified_name = file_name
                if file_name.startswith('output-'):
                        simplified_name = file_name[7:]
                print simplified_name
                name_parts = simplified_name.split('_')
                print name_parts
                simplified_name = name_parts[0] + '_' + name_parts[1] + '.xhtml'
                fileIn_name = os.path.join(dir_in,file_name)
                fileOut_name = os.path.join(dir_out,simplified_name)
                fileIn= codecs.open(fileIn_name,'r','utf-8')
                fileOut = open(fileOut_name,'w')
		print "checking", fileIn_name, "sending to ", fileOut_name
		try:
                        treeIn = etree.parse(fileIn)
                        root = treeIn.getroot()
                        htmlHead = treeIn.xpath("/html:html/html:head",namespaces={'html':"http://www.w3.org/1999/xhtml"})
                        if len(htmlHead) == 1:
                                etree.SubElement(htmlHead[0], 'link', rel='stylesheet', href='ocrtest.css', type='text/css')
                                linkElt = etree.SubElement(htmlHead[0], 'script', type='text/javascript', src='http://code.jquery.com/jquery-1.11.2.min.js')
                                etree.SubElement(htmlHead[0], 'link', rel="stylesheet", href="stylesheets/tipsy.css", type="text/css")
                                etree.SubElement(htmlHead[0], 'script',type='text/javascript', src='http://code.jquery.com/jquery-migrate-1.2.1.min.js')
                                linkElt = etree.SubElement(htmlHead[0], 'script', type='text/javascript', src='javascripts/jquery.tipsy.js')
                                linkElt = etree.SubElement(htmlHead[0], 'script', type='text/javascript', src='javascripts/tipsy.hocr.js')
                        else:
                                head = treeIn.xpath("/html/head")
                                linkElt = etree.SubElement(head[0], 'link', rel='stylesheet', href='ocrtest.css', type='text/css')
                                                           
                        hocr_word_elements = treeIn.xpath("//html:span[@class='ocr_word'] | //span[@class='ocr_word']",namespaces={'html':"http://www.w3.org/1999/xhtml"})
                        for word_element in hocr_word_elements:
                           dhf = word_element.get('dehyphenatedForm')
                           hyphenated_form = False
                           if dhf == None:
                              try:
                                 word = unicodedata.normalize('NFC',word_element.text)
                              except TypeError:
                                 word = unicodedata.normalize('NFC',unicode(word_element.text))
                              
                           elif dhf == "":
                              # It is the tail of a dehyphenated form
                              continue
                           else:
                              word = dhf
                              hyphenated_form = True
                           try:
                              print "Word:", word
                              parts = split_text_token(word)
                              print "Parts:", parts
                              error_word = preprocess_word(parts[1])

                              print "an error word:", error_word
                              (replacement, frequency, spellcheck_mode) = spellcheck_dict[error_word]
                              if spellcheck_mode == "True" or spellcheck_mode == "TrueLower":
                                 replacement = parts[1]
                              #if there is no entry, then we will throw a Key Error and not do any of this:
                              print replacement, frequency, spellcheck_mode
                              parts = (parts[0], replacement, parts[2])
                              print "replaced", error_word, "with", replacement
                              #dump(parts[1])
                              output = parts[0] + parts[1] + parts[2]
                              if hyphenated_form:
                                 hyphen_position = int(word_element.get('hyphenPosition'))-1
                                 end_no = word_element.get("hyphenEndPair")
                                 hyphen_end_element = treeIn.xpath("//html:span[@hyphenStartPair='" + end_no + "'] | //span[@hyphenStartPair='" + end_no + "']",namespaces={'html':"http://www.w3.org/1999/xhtml"})
                                 #hyphen_end_element = treeIn.get_element_by_id(word_element.get("hyphenEndId"))
                                 word_element.set('dehyphenatedForm',output)
                                 word_element.text = output[0:hyphen_position] + '-'
                                 if len(hyphen_end_element) == 1:
                                    hyphen_end_element[0].text = output[hyphen_position:]
                                    hyphen_end_element[0].set("data-spellcheck-mode",spellcheck_mode)
                                 else:
                                   print "there are too many hyphen end elements ", end_id, "has", len(hyphen_end_element)
                                   exit()
                              elif spellcheck_mode == "PunctStrip":
                                     #if the mode is PunctStrip, then provide the original, since it might contain inner brackets, etc.
                                     #Note, however, that we keep the dictionary form 
                                     word_element.set('data-spellchecked-form',replacement) 
                              else:
                                 word_element.text = output
                              word_element.set('data-spellcheck-mode',spellcheck_mode)
                              if word != output:
                                 word_element.set('data-pre-spellcheck',word)
                           except KeyError:
                              print "oops had a key error"
                              if error_word == u'':
                                      word_element.set('data-spellcheck-mode',"Numerical")
                              else:
                                      word_element.set('data-spellcheck-mode',"None")
                        fileOut.write(etree.tostring(treeIn.getroot(), encoding="UTF-8",xml_declaration=True))
                        fileOut.close()
		except:
                        print "failed to parse!"
