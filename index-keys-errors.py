import requests
import json
import csv
import re
import numpy as np 
import boto3
from math import *

s3 = boto3.client('s3')
bucket = 'compounds'
compounds_object = s3.get_object(
    Bucket=bucket, 
    Key='compundlist/compoundlist.csv', 
    ResponseContentType='text/csv'
)
compounds_dict = csv.DictReader(
    compounds_object['Body'].read().decode('utf-8-sig').encode('utf-8').split('\n'), 
    delimiter=','
)

compound_properties = []
bioactivities_properties = []
errors = []
iterator = 0

for row in compounds_dict:
    iterator += 1
    if iterator % 10 == 0:
	print iterator
    InChiKey = row['InChiKey']
    response = requests.get("http://www.ebi.ac.uk/chemblws/compounds/stdinchikey/%s.json" % InChiKey).content
    if 'error' in response or 'Compound not found' in response:
	errors.append(response)
	print errors
	continue
    compound_data = json.loads(response)
    compound_ID = compound_data["compound"]["chemblId"]
    compound_bioactivities = json.loads(requests.get("http://www.ebi.ac.uk/chemblws/compounds/%s/bioactivities.json" % compound_ID).content)

    for key in compound_data:
        for i in compound_data[key]:
            if i not in compound_properties:
                compound_properties.append(i)

    keys_list = []
    def get_keys(d_or_l, keys_list):
        if isinstance(d_or_l, dict):
            for k, v in iter(sorted(d_or_l.iteritems())):
                if isinstance(v, list):
                    get_keys(v, keys_list)
                elif isinstance(v, dict):
                    get_keys(v, keys_list)
                keys_list.append(k)   #  Altered line
        elif isinstance(d_or_l, list):
            for i in d_or_l:
                if isinstance(i, list):
                    get_keys(i, keys_list)
                elif isinstance(i, dict):
                    get_keys(i, keys_list)
        else:
            print "** Skipping item of type: {}".format(type(d_or_l))
        return keys_list

    get_keys(compound_bioactivities, keys_list)
    for i in keys_list:
        if i not in bioactivities_properties:
            bioactivities_properties.append(i)

with open('keys.txt', 'w') as text_file:
    text_file.write('Compounds: \n')
    for cproperty in compound_properties:
        text_file.write('%s\n' % cproperty)
    
    text_file.write('\n')

    text_file.write('Bioactivities: \n')
    for bproperty in bioactivities_properties:
        text_file.write('%s\n' % bproperty)

    text_file.write('\n')
    for error in errors:
	text_file.write('%s\n' % error)
        
