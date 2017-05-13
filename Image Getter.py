import urllib
import requests
import json
import csv
import re
import numpy as np 
from collections import defaultdict
import base64
import cStringIO
import os

compound_ID = 'CHEMBL1336'
InChiKey = 'MLDQJTXFUGDVEO-UHFFFAOYSA-N'

urladdy = "http://www.ebi.ac.uk/chemblws/compounds/%s/image" % compound_ID
filename = r"/Users/giancolombi/Desktop/moon/Neuro/InChi_Data/image_of_%s.png" % InChiKey
urllib.urlretrieve(urladdy, filename)
open_path = open("/Users/giancolombi/Desktop/moon/Neuro/InChi_Data/image_of_%s.png" % InChiKey)
img_src = open("/Users/giancolombi/Desktop/moon/Neuro/InChi_Data/image_of_%s.png" % InChiKey).read()


image = {'picture' : img_src.encode('base64')}
open_path.close()
os.remove("/Users/giancolombi/Desktop/moon/Neuro/InChi_Data/image_of_%s.png" % InChiKey)
print("File Removed!")