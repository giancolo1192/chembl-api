import requests
import json
import csv
import re
import numpy as np 
from collections import defaultdict

path = '/Users/giancolombi/Desktop/moon/Neuro/titles.csv'
columns = defaultdict(list) # each value in each column is appended to a list


with open(path) as f:
    reader = csv.DictReader(f) # read rows into a dictionary format
    for row in reader:
        inchikey = row['InChiKey']
        print 'this is the current inchi: %s' % inchikey