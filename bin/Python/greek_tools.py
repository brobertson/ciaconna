#!/usr/bin/python
# -*- coding: utf8 -*-
import unicodedata

def memoize(f):
    cache= {}
    def memf(*x):
        if x not in cache:
            cache[x] = f(*x)
        return cache[x]
    return memf

#@memoize
def can_combine(char1,char2):
    #print "can"  + unicodedata.name(char1).encode('utf-8') + " and " + unicodedata.name(char2).encode('utf-8') + " combine?"
    normalized_form = unicodedata.normalize('NFC',char1+char2)
    length = len(normalized_form)
    #print "it is length: ", length
    if length == 1:
        return normalized_form
    else:
        return False

#@memoize
def recursive_combine(chars, rejects):
    if len(chars) == 1:
        return [chars, rejects]

    combo = can_combine(chars[0], chars[1])
    the_rest = chars[2:]
    if len(the_rest) == 0:
        the_rest = ''
    if combo:
        return recursive_combine(combo + the_rest, rejects)
    else:
        rejects = rejects + chars[1]
        return recursive_combine(chars[0] + the_rest, rejects)

def dump(stringIn):
        for char in stringIn:
                try:
                        print '\t\t' + unicodedata.name(char) +" (" + unicodedata.category(char) + ")"
                except ValueError:
                        print '\t\t' + char.encode('unicode-escape')
#@memoize
def is_greek_char(char):
                import re
                return bool(re.match(ur'([\u0373-\u03FF]|[\u1F00-\u1FFF]|\u0300|\u0301|\u0313|\u0314|\u0345|\u0342|\u0308)',char,re.UNICODE))

#@memoize
def is_hebrew_char(char):
		import re
		return bool(re.match(ur'([\u05D0-\u05F2])',char,re.UNICODE))

#@memoize
def is_greek_capital(char):
	import re
	return bool(re.match(ur'([\u0391-\u03A9])',char,re.UNICODE))

#@memoize
def is_capitalized(word):
    return (is_greek_capital(word[0]) or (word == word.capitalize()))

#@memoize
def is_uc_word(string_in):
	count = 0
	threshold = 0.7
        count = 0
        if string_in == None or len(string_in) < 1:
                return False
        for char in string_in:
                if is_greek_capital(char):
                        count = count + 1
        factor = float(count) / float(len(string_in))
        #print "factor: ", factor
        if factor > threshold:
                return True
        else:
                return False

#@memoize
def is_number(string_in):
    #for the purposes of OCR, we include Latin capital O and Latin capital I as digits :-)
    #the point here isn't to clean, but rather to discern if, in a Latin OCR output context, the word is likely a number
    import re
    allowed_punct='\.' #what punctuation do you want to include as part of a number?
    allowed_chars = 'OIi'
    return bool(re.match('^[\d' + allowed_chars + allowed_punct + ']+$', string_in))

#@memoize
def is_greek_string(string_in):
	import string,re
	regex = re.compile('[%s]' % re.escape(string.punctuation + u'—·' + u'0123456789'))
        greekness_threshold = 0.7
        #print "String to test for greekness: ", string_in.encode('utf-8')
        string_in = regex.sub('',string_in,re.UNICODE)
	#print "cleaned string to test: ", string_in.encode('utf-8')
        count = 0
        if string_in == None or len(string_in) < 1:
                return False
        for char in string_in:
                if is_greek_char(char) or is_hebrew_char(char):
                        count = count + 1
        factor = float(count) / float(len(string_in))
        #print "factor: ", factornjpPERIOD32101077772836_0240
        if factor > greekness_threshold:
                return True
        else:
                return False

##@memoize
def delete_non_greek_tokens(tokens):
        tokens_out = []
        for token in tokens:
                if is_greek_string(token):
                        #print token.encode('utf-8'), " GREEK"
                        tokens_out.append(token)
        #        else:
                        #print token.encode('utf-8'), " LATIN"
        return tokens_out

def split_text_token(stringIn):
	import re
	superscripts = u'\u00B2\u00B3\u00B9\u2070\u2074\u2075\u2076\u2077\u2078\u2079'
	word_parts = re.match(u'(^[\d' + superscripts + u'·»«„\*\[\("〈,-\.\?’|‖“⟨]*)(.*?)([⟩”«»„.,!?;†·:〉\'\(\)\d\]\[|' + superscripts + u']*$)',stringIn,re.UNICODE)
   	try:
      		parts = word_parts.groups()
	except AttributeError:
		parts = ('',stringIn,'')
	return parts

def preprocess_word(word):
    import re
    # ensures that word is in Python's NFD, and checks for bogus circumflexes
    # that don't compose properly
    word = word.replace(' ', '')
    import unicodedata
    circumflex = unicode(u"\N{COMBINING GREEK PERISPOMENI}")
    other_circumflex = unicode(u"\N{COMBINING CIRCUMFLEX ACCENT}")
    greek_koronis = unicode(u"\N{GREEK KORONIS}")
    smooth_breathing = unicode(u"\N{COMBINING COMMA ABOVE}")
    apostrophe = u"’"#unicode(u"\N{APOSTROPHE}")
    mod_apostrophe = unicode(u"\N{MODIFIER LETTER APOSTROPHE}")
    right_single_quote = unicode(u"\N{RIGHT SINGLE QUOTATION MARK}")
    real_apostrophe = unicode(u"\N{APOSTROPHE}")
    word = re.sub(ur'^' + apostrophe + ur'([I1ΙιΕEAP])(.*)$', r'\1' + smooth_breathing+ r'\2', word)
    word = word.replace(other_circumflex, circumflex)
    word = word.replace(greek_koronis, apostrophe)
    word = word.replace(right_single_quote, apostrophe)
    word = word.replace(mod_apostrophe, apostrophe)
    word = word.replace(real_apostrophe, apostrophe)
    #latin replacements
    word = unicodedata.normalize('NFC', word)
    #remove internal punctuation. Uses negative lookahead and lookbehind assertions
    #word =  re.sub(ur'(?<!^)[·.,\'](?!$)',r'',word)
    return word

#this really doesn't do anything special, but it is handy to have
#a memoized version around :-)
#@memoize
def greek_string_length(stringIn):
    return len(stringIn)

#@memoize
def strip_accents(stringIn):
    import unicodedata
    return ''.join(c for c in unicodedata.normalize('NFD', stringIn)
                   if not unicodedata.combining(c))


def in_dict(dictionary,word):
    from greek_tools import split_text_token
    return split_text_token(word)[1].replace('\'',u'’') in dictionary


def in_dict_lower(dictionary,word):
    from greek_tools import split_text_token
    return split_text_token(word)[1].replace('\'',u'’').lower() in dictionary
