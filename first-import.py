#! /usr/bin/env python
import urllib
import requests
import json
import csv
import re
import boto3
import os
import requests
import sys
from py2neo import Graph
from py2neo import Path, authenticate
######

########################################################################
# set up authentication parameters
authentication = authenticate("ec2-54-164-94-156.compute-1.amazonaws.com:7474", "neo4j", "Rn)BZ-C<adh4")

# Connect to graph and add constraints.
neo4jUrl = os.environ.get('NEO4J_URL','http://ec2-54-164-94-156.compute-1.amazonaws.com:7474/db/data')

graph = Graph(neo4jUrl, secure=False)
query = """
        MERGE (r:Resource {name: 'ChEMBL'})
        """
results = graph.run(query)
tx = graph.begin()
commit = tx.commit()

# We use the compound ChEMBL ID, target ChEMBL ID and assay ChEMBL ID as inputs for our API calls

#check for the status of the ChEMBL API
status = json.loads(requests.get("http://www.ebi.ac.uk/chemblws/status/").content)

s3 = boto3.client('s3')
compounds_object = s3.get_object(
    Bucket='compounds', 
    Key='compundlist/compoundlist.csv', 
    ResponseContentType='text/csv'
)
compounds_dict = csv.DictReader(
    compounds_object['Body'].read().split('\n'), 
    delimiter=','
)
#prime stores all found compound data
prime = []

#Loops through all InChiKeys
for indx ,row in enumerate(compounds_dict):
    if indx % 100 == 0:
	print indx
    InChiKey = row['InChiKey']
    compound_data = {}
########################################################################
#Description: Get individual compound by standard InChi Key
#Input: Standard InChi Key
#Output: Compound Record
    response = requests.get("http://www.ebi.ac.uk/chemblws/compounds/stdinchikey/%s.json" % InChiKey).content
    if 'error' in response or 'Compound not found' in response:
        continue
    InChiKey_data = json.loads(requests.get("http://www.ebi.ac.uk/chemblws/compounds/stdinchikey/%s.json" % InChiKey).content)
    compound_ID = InChiKey_data["compound"]["chemblId"]

########################################################################
#Description: Get compound by ChEMBLID 
#Input: Compound ChEMBLID 
#Output: Compound Record 
    cmpd_data = json.loads(requests.get("http://www.ebi.ac.uk/chemblws/compounds/%s.json" % compound_ID).content)
    compound_data.update(cmpd_data)
########################################################################
#Description: Get the image of a given compound. 
#Input: Compound ChEMBLID 
#Output: Byte array image data
    urladdy = 'http://www.ebi.ac.uk/chemblws/compounds/%s/image/' % compound_ID
    filename = r'/home/giancolombi/Desktop/image_of_%s.png' % InChiKey
    urllib.urlretrieve(urladdy, filename)
    open_path = open('/home/giancolombi/Desktop/image_of_%s.png' % InChiKey)
    img_src = open('/home/giancolombi/Desktop/image_of_%s.png' % InChiKey).read()
    image = {'picture' : img_src.encode('base64')}
    open_path.close()
    compound_data.update(image)
    #Delete the png after storing byte array
    os.remove('/home/giancolombi/Desktop/image_of_%s.png' % InChiKey)
    
########################################################################
#Description: Get individual compound bioactivities 
#Input: Compound ChEMBLID 
#Output: List of all bioactivity records in ChEMBLdb for a given compound ChEMBLID 
    compound_bioactivities = json.loads(requests.get("http://www.ebi.ac.uk/chemblws/compounds/%s/bioactivities.json" % compound_ID).content)
    compound_data.update(compound_bioactivities)
########################################################################
#Description: Get alternative compound forms (e.g. parent and salts) of a compound 
#Input: Compound ChEMBLID 
#Output: List of ChEMBLIDs which correspond to alternative forms of query compound 
    compound_altforms = json.loads(requests.get("http://www.ebi.ac.uk/chemblws/compounds/%s/form.json" % compound_ID).content)
    compound_data.update(compound_altforms)
    
    prime.append(compound_data)

for i in prime:
    
    compoundData = i
    query = """
    WITH {compoundData} as comp
    UNWIND comp.compound as data
    MATCH (r:Resource) WHERE r.name = 'ChEMBL'
    MERGE (cmpd:Compound {InChiKey:data.stdInChiKey}) ON CREATE
        SET cmpd.smiles = data.smiles, 
        cmpd.resourceID = data.chemblID,
        cmpd.molecularWeight = data.molecularWeight,
        cmpd.molecularFormula = data.molecularFormula,
        cmpd.knownDrug = data.knownDrug,
        cmpd.synonyms = data.synonyms,
        cmpd.rotatableBonds = data.rotatableBonds,
        cmpd.preferredCompoundName = data.preferredCompoundName
    MERGE (r)<-[:From]-(cmpd)
    """
    results = graph.run(query,compoundData=compoundData)
    tx = graph.begin()
    tx.commit()
    for j in i['bioactivities']:
        bioData = j
        properties = {}
        properties['compound'] = i['compound']
        properties['bioData'] = j
        query = """
        WITH {properties} as comp
        UNWIND comp.bioData as bios
        UNWIND comp.compound as data
        MATCH (cmpd:Compound) WHERE cmpd.InChiKey = data.stdInChiKey
        MATCH (r:Resource) WHERE r.name = 'ChEMBL'
        MERGE (k:Kinase {rcsID: bios.target_chemblid}) ON CREATE
            SET k.targetName = bios.target_name,
            k.nameInRef = bios.name_in_reference,
            k.ingredientCompoundChemblID = bios.ingredient_cmpd_chemblid,
            k.organism = bios.organism
        MERGE (cmpd)<-[:Bioactivity]-(k)
        """
        #target_chembl = j['target_chemblid']
        #target_data = json.loads(requests.get("http://www.ebi.ac.uk/chemblws/targets/%s.json" % target_chembl).content)
        #if 'proteinAccession' in target_data['target'].keys():
            #print target_data['target']['proteinAccession']
        #else:
        #keep track of which target doesn't have Accession
        results = graph.run(query, properties=properties)
        tx = graph.begin()
        tx.commit()
            
print "Done w/ compounds"
