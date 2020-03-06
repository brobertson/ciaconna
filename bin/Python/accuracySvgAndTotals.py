#!/usr/bin/python3
#given a directory of xhtml files and a directory of corresponding images,
#this generates an svg strip representing the accuracy
#of the ocr output and saves it in the xhtml directory as 'accuracyReport.svg'
def makeTotalsFile(hocrPath):
    import os, sys, lxml
    from lxml import etree
    total_ocr_words = 0
    total_correct_words = 0
    namespaces = {'html': 'http://www.w3.org/1999/xhtml'}
    if not os.path.isdir(hocrPath):
            sys.exit("Directory '"+ hocrPath +"' does not exist.")
    if not os.access(hocrPath, os.W_OK):
        sys.exit("Directory '"+ hocrPath +"' is not writeable.")
    for filename in os.listdir(hocrPath):
      if filename.endswith((".html",".xhtml",".hocr")):
        filePath = os.path.join(hocrPath,filename)
        try: 
            tree = etree.parse(filePath)
            root = tree.getroot()
            number_in_this = len(root.findall(".//html:span[@class='ocr_word']",namespaces))
            correct_words_in_this = len(root.findall(".//html:span[@class='ocr_word'][@data-spellcheck-mode='True']",namespaces))
        except lxml.etree.XMLSyntaxError:
            print("Error reading XML in", filename)
            number_in_this = 0
            correct_words_in_this = 0
        total_ocr_words += number_in_this
        total_correct_words += correct_words_in_this
    print("total: ", total_ocr_words, "; total correct:", total_correct_words)
    out="<lace:totals xmlns:lace='http://heml.mta.ca/2019/lace'><lace:total_words>" + str(total_ocr_words) + "</lace:total_words><lace:total_accurate_words>"+ str(total_correct_words) + "</lace:total_accurate_words></lace:totals>"
    print("writing this data to ",hocrPath+"total.xml")
    with open(os.path.join(hocrPath,"totals.xml"), "w") as text_file:
        text_file.write(out)

def percentageToHSLString(percentage):
    saturation = "73%"
    lightness = "55%"
    burgundy = "hsl(1, 91%, 50%)"
    black = "hsl(0, 0%, 0%)"
    if (percentage == 0):
        return black
    else:
        out =  "hsl(" + str(int(percentage*200)) + "," + saturation + "," + lightness + ")"
        return out
percentageToHSLString(0.2)

def pageAccuracy(pageIn):
    import lxml
    from lxml import etree
    namespaces = {'html': 'http://www.w3.org/1999/xhtml'}
    try:
        tree = etree.parse(pageIn)
        root = tree.getroot()
        number_in_this = len(root.findall(".//html:span[@data-spellcheck-mode]",namespaces))
        correct_words_in_this = len(root.findall(".//html:span[@class='ocr_word'][@data-spellcheck-mode='True']",namespaces))
    except lxml.etree.XMLSyntaxError:
        print("Error reading XML in", pageIn)
        number_in_this = 0
        correct_words_in_this = 0
    if (number_in_this == 0):
        return 0
    else:
        return (correct_words_in_this / number_in_this)
        
#given a directory of xhtml files and a directory of corresponding images,
#this generates an svg strip representing the accuracy
#of the ocr output and saves it in the xhtml directory as 'accuracyReport.svg'
def makeAccuracySVG(hocrPath, imagesXar):
    import os, sys, zipfile
    from lxml import etree
    from pathlib import Path
    from zipfile import BadZipfile
    x_strip_width = 2
    svg_height = str(20)
    total_ocr_words = 0
    total_correct_words = 0
    namespaces = {'svg': 'http://www.w3.org/2000/svg'}
    if not os.path.isfile(imagesXar):
        sys.exit(imagesXar +  " is not a file. Exiting")
    if not os.path.isdir(hocrPath):
            sys.exit("Directory '"+ hocrPath +"' does not exist. Exiting.")
    if not os.access(hocrPath, os.W_OK):
        sys.exit("Directory '"+ dirPath +"' is not writeable. Exiting.")
    try:
        z = zipfile.ZipFile(imagesXar)
    except BadZipfile:
        sys.exit("File " + imagesXar + " is not a proper zip file. Exiting.")
    imageFiles = z.namelist()
    imageFiles.sort()
    #print(imageFiles)
    count = 0
    width = str(len(imageFiles) * x_strip_width)
    svg_root = etree.XML("<svg:svg xmlns:svg='http://www.w3.org/2000/svg' width='" + width +  "' height='" + svg_height + "' id='svg_accuracy_report'></svg:svg>")
    tree = etree.ElementTree(svg_root)
    for filename in imageFiles:
      if filename.endswith((".jpg",".jpeg",".png")):
        #print(filename)
        count += 1
        corresponding_text_file = Path(filename).stem + ".html"
        correspondingfilePath = os.path.join(hocrPath,corresponding_text_file)
        if os.path.isfile(correspondingfilePath):
            accuracy_percentage_for_page=pageAccuracy(correspondingfilePath)
            fill=percentageToHSLString(accuracy_percentage_for_page)
        else:
            fill="hsl(0, 0%, 86%)"#light grey
        svg_rect='''<svg:a xmlns:svg='http://www.w3.org/2000/svg'
                    href="side_by_side_view.html?positionInCollection={}">
                <svg:rect data-doc-name="{}" x="{}" y="0" width="{}" height="{}" style="fill:{}">
                    <svg:title>{}</svg:title>
                </svg:rect>
            </svg:a>'''.format(str(count),corresponding_text_file,str(count*x_strip_width),str(x_strip_width),svg_height,fill,str(count))
        svg_root.append( etree.XML(svg_rect))     
    #print(str(etree.tostring(tree.getroot(), encoding='unicode', method='xml')))
    with open(os.path.join(hocrPath,"accuracyReport.svg"), "w") as text_file:
        text_file.write(str(etree.tostring(tree.getroot(), encoding='unicode', method='xml')))

def main():
    import sys, os
    if not(len(sys.argv) == 3):
        print("usage:",os.path.basename(sys.argv[0]), "hocr_dir_path images_file.xar")
        exit(1)
    else:
        makeTotalsFile(sys.argv[1])
        makeAccuracySVG(sys.argv[1], sys.argv[2])

if __name__== "__main__":
  main()
