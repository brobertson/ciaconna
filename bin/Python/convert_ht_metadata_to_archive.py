import json
import urllib2
import xml.etree.ElementTree as ET
import string

def clean_text_id(string_in):
  return string_in.replace('.', 'PERIOD')

#data = json.load(urllib2.urlopen('http://catalog.hathitrust.org/api/volumes/brief/recordnumber/008882185.json'))
data = json.load(urllib2.urlopen('http://catalog.hathitrust.org/api/volumes/brief/recordnumber/012261788.json'))
#print 'INDENT:', json.dumps(data, sort_keys=True, indent=2)
for key in data['items']:
  print key['htid']
  clean_id = clean_text_id(key['htid'])
  print key
  root = ET.Element('metadata')
  pub = ET.SubElement(root,'publisher')
  pub.text = "Lutetiae Parisiorum"
  identifier = ET.SubElement(root,'identifier')
  identifier.text=clean_id
  b = ET.SubElement(root,'title')
  b.text = "Patrologiae cursus completus ... series graeca"
  cr = ET.SubElement(root,'creator')
  cr.text = "Migne, J.-P."
  vol = ET.SubElement(root,'volume')
  vol.text = key['enumcron']
  ppi = ET.SubElement(root,'ppi')
  ppi.text = '400'
  out = ET.ElementTree(element=root)
  filename = clean_id + "_meta.xml"
  out.write(filename)
