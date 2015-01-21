from PIL import Image
import imagehash
import sys
hash = imagehash.average_hash(Image.open(sys.argv[1]))
otherhash = imagehash.average_hash(Image.open(sys.argv[2]))
#print "Is same?", (hash == otherhash)
if  (hash - otherhash) < 11:
	print sys.argv[1], "Is similar to", sys.argv[2]
else:
	print sys.argv[2], "Is not similar to", sys.argv[2]


