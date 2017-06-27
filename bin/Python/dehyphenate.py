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
from greek_tools import is_number

def dehyphenate(treeIn):
        initial_match_count = 0
        inset_match_count = 0
        pair_count = 0
	last_words = treeIn.xpath("//html:span[@class='ocr_word'][last()] | //span[@class='ocr_word'][last()]",namespaces={'html':"http://www.w3.org/1999/xhtml"})
	first_words = treeIn.xpath("//html:span[@class='ocr_word'][1] | //span[@class='ocr_word'][1]",namespaces={'html':"http://www.w3.org/1999/xhtml"})
        for word in last_words:
            print word.text
        if len(last_words) > 0 and len(first_words) > 0:
                last_first_pairs = zip(last_words,first_words[1:]+[None])
                last_first_pairs = [(None,first_words[0])] + last_first_pairs
                for pair in last_first_pairs:
                    if pair[1] == None:
                        print pair[0].text, "DONE"
                    elif pair[0] == None:
                        print "START", pair[1].text
                    #this avoids corner case where a character has been deleted by unicode violation in the parser
                    elif (not pair[0].text == None) and (not pair[1].text == None):
                        hyph_end = None
                        print "pair[0].text", pair[0].text
                        if  pair[0].text[-1] == u'-':
                            hyph_end = pair[0]
                            initial_match_count = initial_match_count + 1 
                            #print "im trying to set hyph_end because ", hyph_end.text
                        else:
                            try:
                                 if pair[0].getprevious().text[-1] == u'-':
                                     hyph_end = pair[0].getprevious()
                                     inset_match_count = inset_match_count + 1
                                     #print "a previous hyph_end! ", hyph_end.text
                            except:
                                 pass

 			if not (hyph_end == None):
                            second_part = pair[1]
                            #if the first thing in this line is a number, then it's
                            #probably a line number and shouldn't be appended to the hyphen
                            if is_number(second_part.text) and not (second_part.getnext() == None):
                                second_part = second_part.getnext() 
                            #print "found hyphenated end form: ", hyph_end.text
                            pair_count = pair_count + 1
                            dehyphenated_form = u'' + hyph_end.text[:-1] + second_part.text
                            #print "the dehyphenated form is: ", dehyphenated_form
                            hyphen_position = str(len(hyph_end.text))
                            hyph_end.set('data-dehyphenatedform', dehyphenated_form)
                            hyph_end.set('data-hyphenposition', hyphen_position)
                            hyph_end.set('data-hyphenendpair',str(pair_count))
                            second_part.set('data-dehyphenatedform', '')
                            second_part.set('data-hyphenstartpair',str(pair_count))
                        #print(etree.tostring(pair[0], method='xml', encoding="utf-8", pretty_print=True))
                        #print(etree.tostring(pair[1], encoding="utf-8", pretty_print=True))
	return treeIn

def identify(treeIn):
        words = treeIn.xpath("//html:span[@class='ocr_word'] | //span[@class='ocr_word']",namespaces={'html':"http://www.w3.org/1999/xhtml"})
        for word in words:
            if word.get('id') == None:
                word.set('id','_'+str(id(word)))
            if word.get('data-manually-confirmed') == None:
                word.set('data-manually-confirmed','false')
        return treeIn

def remove_meta_tags(treeIn):
	metas = treeIn.xpath("//html:meta",namespaces={'html':"http://www.w3.org/1999/xhtml"})
        if len(metas) > 0:
            metas[0].getparent().append(etree.Comment("The following meta tags have been commented out to conform to HTML5 until such time as they have been approved by HTML5"))
	for meta in metas:
		string_rep = etree.tostring(meta, pretty_print=True)
                meta.getparent().append(etree.Comment(string_rep))
                meta.getparent().remove(meta)
        return treeIn

def add_dublin_core_tags(treeIn):
    head = treeIn.xpath("//html:head",namespaces={'html':"http://www.w3.org/1999/xhtml"})
    m = etree.SubElement(head[0],"meta")
    m.set("name","DCTERMS.contributor")
    m.set("content","Bruce Robertson (OCR processing)")
    m2 = etree.SubElement(head[0],"meta")
    m2.set("name","DCTERMS.description")
    m2.set("content","OCR output of page images processed through the ciaconna OCR system, which in turn is based on OCRopus.")
    return treeIn
spellcheck_dict = {}
euro_sign = unicode(u"\N{EURO SIGN}") 
print sys.argv[1]
try:
    dir_in = sys.argv[1]
    print dir_in
    dir_in_list = os.listdir(dir_in)
    dir_out = sys.argv[2]
except (IndexError, ValueError) as e:
    print e
    print "usage: dehyphenate.py dir_in dir_out"
    exit()
        
for file_name in dir_in_list:
        if file_name.endswith('.html'):
                simplified_name = file_name
                if file_name.startswith('output-'):
                        simplified_name = file_name[7:]
                #print simplified_name
                name_parts = simplified_name.split('_')
                #print name_parts
                simplified_name = name_parts[0] + '_' + name_parts[1] #+ '.html'
                fileIn_name = os.path.join(dir_in,file_name)
                fileOut_name = os.path.join(dir_out,simplified_name)
                try:
                    fileIn= codecs.open(fileIn_name,'r','utf-8',errors='strict')
                except Exception as e:
                    print "codec exception: ", e
            
                fileOut = open(fileOut_name,'w')
		print "checking", fileIn_name, "sending to ", fileOut_name
                try:
                    parser = etree.XMLParser(recover=True, ns_clean=True)
                    treeIn = etree.parse(fileIn, parser)
                    treeIn = remove_meta_tags(treeIn)
                    print "removed tags"
                    treeIn = identify(treeIn)
                    print "identified"
		    treeIn = dehyphenate(treeIn)
		    treeIn = add_dublin_core_tags(treeIn)
                    fileOut.write(etree.tostring(treeIn,
                        encoding="UTF-8", xml_declaration=True,  doctype="<!DOCTYPE html>",method="xml" ))
                    fileOut.close()
                except lxml.etree.XMLSyntaxError as e:
                    print "lxml error", e



