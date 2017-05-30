#! /usr/bin/env python

import requests
import json
import csv
import re
import numpy as np 
import boto3
from collections import defaultdict
from neo4j.v1 import GraphDatabase
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
    compounds_object['Body'].read().split('\n'), 
    delimiter=','
)

prime = []

for row in compounds_dict:
    InChiKey = row['InChiKey']
    
########################################################################
#Description: Get individual compound by standard InChi Key
#Input: Standard InChi Key
#Output: Compound Record
    InChiKey_data = json.loads(requests.get("http://www.ebi.ac.uk/chemblws/compounds/stdinchikey/%s.json" % InChiKey).content)
    compound_ID = InChiKey_data["compound"]["chemblId"]

########################################################################
#Description: Get compound by ChEMBLID 
#Input: Compound ChEMBLID 
#Output: Compound Record 
    compound_data = json.loads(requests.get("http://www.ebi.ac.uk/chemblws/compounds/%s.json" % compound_ID).content)
    
########################################################################
#Description: Get the image of a given compound. 
#Input: Compound ChEMBLID 
#Output: Byte array image data
    compound_image = "http://www.ebi.ac.uk/chemblws/compounds/%s/image" % compound_ID

########################################################################
#Description: Get individual compound bioactivities 
#Input: Compound ChEMBLID 
#Output: List of all bioactivity records in ChEMBLdb for a given compound ChEMBLID 
    compound_bioactivities = json.loads(requests.get("http://www.ebi.ac.uk/chemblws/compounds/%s/bioactivities.json" % compound_ID).content)

########################################################################
#Description: Get alternative compound forms (e.g. parent and salts) of a compound 
#Input: Compound ChEMBLID 
#Output: List of ChEMBLIDs which correspond to alternative forms of query compound 
    compound_altforms = json.loads(requests.get("http://www.ebi.ac.uk/chemblws/compounds/%s/form.json" % compound_ID).content)

########################################################################
#Description: Get mechanism of action details for compound (where compound is a drug) 
#Input: Compound ChEMBLID 
#Output: List of drug mechanism of action and ChEMBL target details 
    compound_mech_of_action = json.loads(requests.get("http://www.ebi.ac.uk/chemblws/compounds/%s/drugMechanism.json" % compound_ID).content)
    
    #put the data together
    compound_data.update(compound_bioactivities)
    compound_data.update(compound_altforms)
    prime.append(compound_data)
    
print "done"
    
