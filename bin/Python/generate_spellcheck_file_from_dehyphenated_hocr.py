#!/usr/bin/python
# coding: utf-8
import sys
import difflib
import leven
import codecs
import unicodedata
from greek_tools import preprocess_word, strip_accents, in_dict_lower, dump, split_text_token, delete_non_greek_tokens, is_uc_word, is_greek_char, is_greek_string
from read_dict5 import makeDict
import lxml
from lxml import etree
import re
import codecs
import os
import unicodedata
import HTMLParser
import yaml
superscripts = u'\u00B2\u00B3\u00B9\u2070\u2074\u2075\u2076\u2077\u2078\u2079'

try:
    dir_in = sys.argv[1]
    #print dir_in
    dir_in_list = os.listdir(dir_in)
   # dir_out = sys.argv[2]
except (IndexError, ValueError) as e:
    print e
    print "usage: list_words_from_dehyphenated_hocr.py dir_in dir_out"
    exit()




def add_word(word_count, word):
    
    word_no_punct = split_text_token(word)[1]
    word_no_punct = preprocess_word(word_no_punct)
    if len(word_no_punct) > 0:
        word = word_no_punct
    if True: #is_greek_string(word):
        if word not in word_count:
            word_count[word] = 1
        else:
            word_count[word] += 1
    return word_count

def get_hocr_words(treeIn, word_count):
    words = treeIn.xpath("//html:span[@class='ocr_word'] | //span[@class='ocr_word']",namespaces={'html':"http://www.w3.org/1999/xhtml"})
    #word_count = {}
    for word in words:
        dhf = word.get('data-dehyphenatedform')
        if dhf == '':
            next
        elif dhf != None:
            add_word(word_count, dhf)
            #print "appending dhf", dhf
        elif word.text[-1] != "-":#ommit blown hyphenated forms
            add_word(word_count, word.text)
            #print "apending word", word.text
def make_ligatures(word):
	for pair in [[u'ae',u'æ'],[u'ff',u'ﬀ'],[u'oe',u'œ'],[u'fl',u'ﬂ'],[u'fi',u'ﬁ']]:
		word = word.replace(pair[0],pair[1])
	return word


def makeDict(fileName, migne_mode=False):
    import greek_tools
    frequency_limit = 0
    words = []
    mine = codecs.open(fileName, 'r', 'utf-8')
    for line in mine:
        line = unicodedata.normalize('NFC', line)
        try:
            (word, freq) = line.split(',')
        except ValueError:
            print "this line is wrong:", line
            sys.exit()
        freq = int(freq.rstrip('\r\n'))
        if freq > frequency_limit:
            word_prep = preprocess_word(word.rstrip('\n\r\x11'))
            if migne_mode:
                word_prep = make_ligatures(word_prep)
            words.append(word_prep)
##    for word in words:
##        print word
    return (words)

def makeNoAccentDict(fileName):
  no_accent_dict = {}
  mine = codecs.open(fileName, 'r', 'utf-8')
  for line in mine:
    (no_accent, word) = line.split(',')
    word = word.rstrip('\r\n')
    no_accent = no_accent.rstrip('\n\r\x11')
    no_accent_dict[no_accent] = word
  return no_accent_dict

def inNoAccentDict(word, no_acent_dict):
    try:
        output = no_accent_dict[strip_accents(word)]
        return output
    except:
        return False
    
def findOccurences(s, ch):
    return [i for i, letter in enumerate(s) if letter == ch]

def bothHalvesInDict(str1,str2):
  return ((str1 in dict) or in_dict_lower(dict,str1)) and ((str2 in dict) or in_dict_lower(dict,str2))

#print "making dicts"
import time
start_time = time.time()
dict = makeDict(sys.argv[2])
dict_time = time.time() - start_time
minutes = dict_time / 60.0
dict = set(dict)
no_accent_dict = makeNoAccentDict(sys.argv[3])
#print "dict building took", minutes, " minutes."
marker=u"€"

word_count = {}

for file_name in dir_in_list:
        if file_name.endswith('.html'):
                simplified_name = file_name
                if file_name.startswith('output-'):
                        simplified_name = file_name[7:]
                #print simplified_name
                name_parts = simplified_name.split('_')
                #print name_parts
                simplified_name = name_parts[0] + '_' + name_parts[1] + ".txt"
                fileIn_name = os.path.join(dir_in,file_name)
                fileOut_name = os.path.join(dir_in,simplified_name)
                fileIn= codecs.open(fileIn_name,'r','utf-8', errors="ignore")
                fileOut = open(fileOut_name,'w')
		#print "checking", fileIn_name, "sending to ", fileOut_name
                try:
                    treeIn = etree.parse(fileIn)
                    get_hocr_words(treeIn, word_count)
                except(lxml.etree.XMLSyntaxError):
                    print >> sys.stderr, "XMLSyntaxError on printing ", simplified_name
                    pass

total_count = 0
total_biomass = 0
counts = {}
biomass = {}
output_array = []
output_dict = {}
punct_split='([\.,·;’\[\]\)\(])'
punct_re = re.compile(punct_split)
count = 0
total = len(word_count)
latin_suffixes=[u'que',u'ne',u've']
for w in sorted(word_count, key=word_count.get, reverse=True):
    count = count + 1
    operation = "False"
    output = ""
    terminal_chars=u"ς"              
    if w in dict:
        operation = "True"
    elif (in_dict_lower(dict,w) == True):
        operation = "TrueLower"
    elif inNoAccentDict(w,no_accent_dict):
        output = inNoAccentDict(w,no_accent_dict)
        operation="NoAcc"
    elif (len(punct_re.split(w)) == 3):
            punct_stripped = punct_re.sub('',w)
            if punct_stripped in dict or in_dict_lower(dict,punct_stripped):
                operation="PunctStrip"
                output=punct_stripped
            else:
                split_on_punct = punct_re.split(w)
                if bothHalvesInDict(split_on_punct[0], split_on_punct[2]):
                    output = split_on_punct[0] + split_on_punct[1] + ' ' + split_on_punct[2]
                    operation = "SplitOnPunct"

    if operation == "False":
        split = re.split(marker,re.sub('([' + terminal_chars + '])',r'\1'+marker,w))
        if len(split) > 1:
            output = ''
            operation = "Split"
            for component in split:
                if component != '':
                    if not (component in dict):
                        no_accent_component = inNoAccentDict(component,no_accent_dict)
                        if no_accent_component:
                            output = output + ' ' + no_accent_component
                            operation = "SplitNoAcc"
                        elif in_dict_lower(dict,component):
                            output = output + ' ' + component
                        else:
                            operation = "False"
                            output = ""
                            break
                    else:
                        output = output + ' ' + component

    if operation=="False":
        try:
            digit_groups = re.match(u'(^[·«„\[\("〈]*)([I\d' + superscripts + u']*?)([«»„.,!?;†·:〉\)\]' + u']*$)',w,re.UNICODE).groups()
            output = digit_groups[0] + re.sub('I','1',digit_groups[1]) + digit_groups[2]
            operation = "Numerical"
        except:
            pass
    for a_suffix in latin_suffixes:
        if w.endswith(a_suffix) and (w[:-1*len(a_suffix)] in dict or in_dict_lower(dict,w[:-1*len(a_suffix)])):
            operation = "True"
##    if operation=="False" and re.match(u'[^\w\s]+',w,re.UNICODE):
##        operation = "Punctuation"
    if operation == "False" and (len(w) > 1):
        subs = [

            [u'd',[u'ὅ',u'ό']],
            [u'δ',[u'ὅ',u'ὀ',u'ό',u'ὄ',u'ὁ',u'ό',u'ο',u'd']],
            [u'ῖ',[u'ὶ']],[u'Τ',[u'Υ']],
            [u'ἶ',[u'ἷ']],
            [u'ἷ',[u'ἶ']],
            [u'T',[u'Υ']],
            [u'l',[u'I',u'ί',u'ἰ',u'ἱ',u'Ἰ',u'ἴ',u'i',u'ι']],
            [u'A',[u'Α',u'Ἀ',u'Ἁ',u'Λ']],
            [u'3',[u'Β',u'B']],
            [u'7',[u'Τ',u'ί',u'Γ',u'T']],
            [u'Ε',[u'E',u'Ἐ']],
            [u'Α',[u'A',u'Ἀ',u'Δ']],
            [u'Ἀ',[u'Ἄ',u'Ἁ']],
            [u'Δ',[u'Ἀ',u'Α']],
            [u'α',[u'z',u'ο',u'a',u'σ']],
            [u'β',[u'ἵ',u'ῆ',u'ἐ',u'θ',u'ψ']],
            [u'ἐ',[u'ἑ',u'ἔ',u'ἔ']],
            [u'ἀ',[u'ἁ',u'ἅ',u'ἂ',u'ἄ']],
            [u'ἁ',[u'ἀ']],
            [u'ἅ',[u'ἄ',u'ἂ']],
            [u'ἄ',[u'θ',u'ἀ']],
            [u'ὰ',[u'ἄ',u'ἂ',u't',u'ἀ',u'ᾶ']],
            [u'ά',[u'ἀ',u'ἄ',u'ἁ',u'ό']],
            [u'ᾶ',[u'ᾷ',u'ἆ']],
            [u'ἔ',[u'ἕ']],
            [u'ε',[u'ὲ',u'ἐ',u'e',u's']],
            [u'ἐ',[u'ἑ']],
            [u'ἑ',[u'ἐ']],
            [u'έ',[u'ἐ',u'ἑ']],
            [u'ἱ',[u'ἰ',u'ἷ']],
            [u'ἴ',[u'ἷ',u'ἵ']],
            [u'ἰ',[u'ἱ',u'ἴ',u'ὶ',u'ί']],
            [u'ὶ',[u'ἱ',u'i']],
            [u'ι',[u'ἰ',u'ἱ',u'ὶ',u'ί',u'i']],
            [u'ἠ',[u'ἡ']],
            [u'ἡ',[u'ἠ']],
            [u'ῆ',[u'ὴ',u'ἧ',u'ῇ',u'ή']],
            [u'ἤ',[u'ἥ']],
            [u'ὴ',[u'ή']],
            [u'ή',[u'ὴ',u'ῆ']],
            [u'θ',[u'ﬁ']],
            [u'δ',[u'θ']],
            [u'ο',[u'ὸ',u'c',u'o',u'σ']],
            [u'ὀ',[u'ὁ']],
            [u'ὁ',[u'ὀ']],
            [u'ό',[u'ὁ',u'ὀ']],
            [u'ὸ',[u'b',u'ὁ',u'δ']],
            [u'ὅ',[u'ὄ']],
            [u'ϲ',[u'c']],
            [u'λ',[u'ἵ']],
            [u'ῦ',[u'ὺ']],
            [u'v',[u'v']],
            [u'v',[u'ν',u'υ']],
            [u'Τ',[u'Ἰ',u'Ἴ',u'T',u'Γ',u'Υ']],
            [u'Z',[u'Ζ']],
            [u'Ἰ',[u'Ἴ',u'Ἵ',u'Ἱ']],
            [u'Ὁ',[u'Ὅ']],
            [u'Κ',[u'Χ',u'K']],
            [u'Λ',[u'Α',u'Δ',u'A']],
            [u'Μ',[u'M']],
            [u'Π',[u'Β']],
            [u'Χ',[u'X']],
            [u'Ὡ',[u'Ὠ']],
            [u'ή',[u'ἡ']],
            [u'ῇ',[u'ᾗ',u'ᾖ']],
            [u'ἡ',[u'ἥ']],
            [u'ἤ',[u'ἥ']],
            [u'ῃ',[u'η']],
            [u'η',[u'ή']],
            [u'κ',[u'x']],
            [u'ὕ',[u'ὔ']],
            [u'ὔ',[u'ὕ']],
            [u'ρ',[u'ῥ',u'p']],
            [u'ς',[u's']],
            [u'σ',[u'κ']],
            [u'τ',[u'r',u'x']],
             [u'φ',[u'ρ']],
            [u't',[u'λ',u'ι',u'ῖ',u'ἰ',u'ἱ',u'ί']],
            [u'ύ',[u'ὐ',u'ὑ']],
            [u'ὐ',[u'ύ',u'ὑ']],
            [u'ὑ',[u'ὐ']],
            [u'ώ',[u'ῴ']],
            [u'ῶ',[u'ὧ',u'ώ']],
            [u'ὠ',[u'ὡ']],
            [u'ὡ',[u'ὠ',u'ὼ']],
            [u'D',[u'Π',u'Β',u'Ο',u'U']],
            [u'B',[u'Β']],
            [u'E',[u'Ε',u'Ἐ',u'F']],
            [u'Ε',[u'E',u'Ἐ',u'Ἑ']],
            [u'Ἐ',[u'Ἑ',u'Ἔ']],
            [u'B',['H']],
            [u'H',[u'Π',u'Η',u'Ἡ',u'Ἡ']],
            [u'I',[u'Ι',u'J',u'l',u'Π']],
            [u'J',[u'I']],
            [u'K',[u'Κ']],
            [u'M',[u'Μ']],
            [u'N',[u'Ν']],
            [u'O',[u'Ο',u'0']],
            [u'0',[u'O',u'Ο']],
            [u'P',[u'Ῥ',u'Ρ']],
            [u'Ρ',[u'Ῥ',]],
            [u'R',[u'H']],
            [u'Q',[u'O']],
            [u'T',[u'Τ',u'Γ']],
            [u'X',[u'Χ','T']], #now Latin
            [u'Z',[u'Ζ']],
            [u'a',[u'α',u'e',u'n',u's',u'u']],
            [u'b',[u'h']],
            [u'æ',[u'œ']],
            [u'œ',[u'æ']],
            [u'c',[u'e',u'o',u'q',u'ϲ']],
            [u'e',[u'c',u'o',u'ε']],
            [u'f',[u'i',u'l',u'ﬀ']],
            [u'g',[u'y']],
            [u'ﬀ',[u'ﬁ']],
            [u'ﬁ',[u'ﬂ']],
            [u'ﬀi',[u'fﬁ']],
            [u'h',[u'b',u't']],
            [u'i',[u'l',u'ι',u'ἱ',u'ἰ']],
            [u'm',[u'n']],
            [u'l',[u't',u'ﬂ',u'i']],
            [u'u',[u'n',u'o',u'ν']],
            [u'n',[u'u',u'm',u'a']],
            [u'o',[u'ο',u'q',u'c']],
            [u'p',[u'q',u'ρ']],
            [u'q',[u'c',u'p']],
            [u'r',['t','v',u'τ']],
            [u's',[u'ς']],
            [u't',[u'i',u'r',u'l']],
            [u'v',[u'y',u'r',u'u',u'æ',u'ν']],
            [u'x',[u'z']],
            [u'y',[u'γ']],
            [u'fi',[u'ﬁ']],
            [u'ﬁ',[u'f']],
            [u'ae',[u'æ']],
            [u'τ',[u'ι']],
             [u's',[u'a',u'n',u'e']],
            [u'1',[u'ί']],
            [u'1',[u'l',u'i',u'I']],
            [u'8',[u's']]
            ]
        for subst in subs:
            for replacement in subst[1]:
                for instance in findOccurences(w,subst[0]):
                    #sub_attempt = re.sub(subst[0],replacement,w)
                    #sub_attempt = w.replace(subst[0],replacement)
                    #replace this instance with the target character
                    try:
                        sub_attempt = w[:instance] +  replacement + w[instance+1:]
                    except UnicodeDecodeError as e:
                        print >> sys.stderr, e, w, replacement
                    if sub_attempt in dict:
                        output = sub_attempt
                        try:
				operation = "Sub " + subst[0] + "->" + replacement
			except UnicodeDecodeError as e:
                        	print >> sys.stderr, e, w, replacement
                        break
                    elif in_dict_lower(dict,sub_attempt):
                        output = sub_attempt
                        try:
				operation = "SubLower " + subst[0] + "->" + replacement
                        except UnicodeDecodeError as e:
                                print >> sys.stderr, e, w, replacement
			break
                    elif inNoAccentDict(sub_attempt, no_accent_dict) and (len(sub_attempt) > 4 or w[0].isupper()):
                        output = inNoAccentDict(sub_attempt, no_accent_dict)
                        try:
				operation = "SubNoAcc " + subst[0] + "->" + replacement
                        except UnicodeDecodeError as e:
                                print >> sys.stderr, e, w, replacement
			break
    if operation == "False":
        dup_letters_removed = re.sub(r'(.)\1{1,}',r'\1',w)
        if dup_letters_removed in dict:
            operation = "Dedup"
            output = dup_letters_removed
        elif (in_dict_lower(dict,dup_letters_removed) == True):
            operation = "DedupLower"
            output = dup_letters_removed
        elif inNoAccentDict(dup_letters_removed, no_accent_dict):
           output =  inNoAccentDict(dup_letters_removed, no_accent_dict)
           operation = "DedupNoAcc"
    if operation == "False":
        l = len(w)
        half = l/2
        for pointer in range(1,half-3):
                if bothHalvesInDict(w[:half-pointer+1], w[half-pointer+1:]):
                    operation="True"
                    output= w[:half-pointer+1] + " " + w[half-pointer+1:]
                    break
                if bothHalvesInDict(w[:pointer+half], w[pointer+half:]):
                    output = w[:pointer+half] + " " + w[pointer+half:]
                    operation="True"
                    break
    print w + marker + output + marker + str(word_count[w]) + marker + operation
    #print "#", str(100.0 * count / total), "complete"
    #output_array.append((w,output,word_count[w],operation))
    if operation != "False":
        output_dict[w] = (output,word_count[w],operation)
##    if operation == "False":
##        try:
##            dump(w)
##        except:
##            print "Error in dump on word", w
    total_count = total_count + int(word_count[w])
    total_biomass = total_biomass + int(word_count[w]) * len(w)
    try:
        counts[operation] = counts[operation] + word_count[w]
        biomass[operation] = biomass[operation] + word_count[w] * len(w)
    except:
        counts[operation] = word_count[w]
        biomass[operation] = word_count[w] * len(w)
print >> sys.stderr, "Total words:", total_count
#print >> sys.stderr, counts
total_fixed = 0
total_biomass_fixed = 0
for out in sorted(counts, key=counts.get, reverse=True):
    print >> sys.stderr, out, counts[out]
    if not out == "False":
        total_fixed = total_fixed + counts[out]
        total_biomass_fixed = total_biomass_fixed + biomass[out]
try:
	print >> sys.stderr, "#Total fixed: ", str(total_fixed)
	print >> sys.stderr, "#Percentage good:", str(total_fixed * 100.00 / total_count)
	print >> sys.stderr, "#Biomass correct: ", str( total_biomass_fixed * 100.00 / total_biomass)
	##with open(sys.argv[4], 'w') as outfile:
	##    outfile.write( yaml.dump(output_dict, default_flow_style=True) )
except ZeroDivisionError:
	print >> sys.stderr, "#Total count is ZERO???"
