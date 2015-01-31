import ngram
import sys
def file_as_string(filename):
	with open (filename, "r") as myfile:
		data=myfile.read().replace('\n', '')
	return data

a = file_as_string(sys.argv[1])
b = file_as_string(sys.argv[2])
value = ngram.NGram.compare(a,b)
print value , sys.argv[2]
