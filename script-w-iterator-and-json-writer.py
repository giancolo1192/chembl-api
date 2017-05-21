#! /usr/bin/env python

import requests
import json
import csv
import re
import numpy as np 
import boto3
from collections import defaultdict
######

########################################################################

# We use the compound ChEMBL ID, target ChEMBL ID and assay ChEMBL ID as inputs for our API calls

#check for the status of the ChEMBL API
status = json.loads(requests.get("http://www.ebi.ac.uk/chemblws/status/").content)

s3 = boto3.client('s3')
compounds_object = s3.get_object(
    Bucket='compounds', 
    Key='compundlist/compoundlist_short.csv', 
    ResponseContentType='text/csv'
)
compounds_dict = csv.DictReader(
    compounds_object['Body'].read().split('\n'), delimiter=','
)

columns = defaultdict(list) # each value in each column is appended to a list

for row in compounds_dict:
    InChiKey = row['InChiKey']
    #print 'this is the current inchi: %s' % InChiKey
########################################################################
#Description: Get individual compound by standard InChi Key
#Input: Standard InChi Key
#Output: Compound Record
    InChiKey_data = json.loads(requests.get("http://www.ebi.ac.uk/chemblws/compounds/stdinchikey/%s.json" % InChiKey).content)
    compound_ID = InChiKey_data["compound"]["chemblId"]
    print "InChiKey_data: "
    for key in InChiKey_data['compound']:
        print key
    print '\n'
    #print 'with ChEMBL ID: ' + compound_ID
    #print '\n'

########################################################################
#Description: Get compound by ChEMBLID 
#Input: Compound ChEMBLID 
#Output: Compound Record 
    compound_data = json.loads(requests.get("http://www.ebi.ac.uk/chemblws/compounds/%s.json" % compound_ID).content)
    print "Compound Data: "
    for key in compound_data['compound']:
        print key
    print "\n"
    #print "Compound Name:             %s" % compound_data['compound']['preferredCompoundName']
    #print "Compound CHEMBLID:         %s" % compound_data['compound']['chemblId']
    #print "Compound stdInChiKey:      %s" % compound_data['compound']['stdInChiKey']
    #print "Compound Canonical SMILES: %s" % compound_data['compound']['smiles']
#print to verify we got the json

########################################################################
#Description: Get the image of a given compound. 
#Input: Compound ChEMBLID 
#Output: Byte array image data
#     compound_image = "http://www.ebi.ac.uk/chemblws/compounds/%s/image" % compound_ID
    #print "\n"
    #print "See compound image here: " + compound_image
#print to verify we got the json

########################################################################
#Description: Get individual compound bioactivities 
#Input: Compound ChEMBLID 
#Output: List of all bioactivity records in ChEMBLdb for a given compound ChEMBLID 
    compound_bioactivities = json.loads(requests.get("http://www.ebi.ac.uk/chemblws/compounds/%s/bioactivities.json" % compound_ID).content)
    print "bioactivities: "
    for bioactivity in compound_bioactivities['bioactivities']:
        for key3 in bioactivity:
            print key3
        break
    print "\n"
    #print "We got the compound bioactivities!"
#print to verify we got the json

########################################################################
#Description: Get alternative compound forms (e.g. parent and salts) of a compound 
#Input: Compound ChEMBLID 
#Output: List of ChEMBLIDs which correspond to alternative forms of query compound 
    compound_altforms = json.loads(requests.get("http://www.ebi.ac.uk/chemblws/compounds/%s/form.json" % compound_ID).content)
    print "Compound Forms: "
    for form in compound_altforms['forms']:
        print form
    print "\n"
    #print "We got the compounds alternate forms!"
#print to verify we got the json

########################################################################
#Description: Get mechanism of action details for compound (where compound is a drug) 
#Input: Compound ChEMBLID 
#Output: List of drug mechanism of action and ChEMBL target details 
    compound_mech_of_action = json.loads(requests.get("http://www.ebi.ac.uk/chemblws/compounds/%s/drugMechanism.json" % compound_ID).content)
    print "Compound Mech of Action: "
    print compound_mech_of_action
    break
    #print "We got the compound mechanism of action!"
    #print "\n"
#print to verify we got the json


    merged_data = InChiKey_data.items() + compound_data.items() + compound_bioactivities.items() + compound_altforms.items() +  compound_mech_of_action.items()
    # string dump of the merged dict
#     with open("/Users/giancolombi/Desktop/moon/Neuro/InChi_Data/data_for_%s.json" % InChiKey, "w") as json_file:
#         json.dump(merged_data, json_file)

    
