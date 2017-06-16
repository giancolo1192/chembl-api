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
ec2 = boto3.client('ec2')
masterInstance = ec2.describe_instances(
    Filters=[
        {
            'Name':'tag:Rank', 
            'Values':['Master']
        },
        {
	    'Name':'tag:Group',
	    'Values':['TruvitechDB']
	}
    ]
)
IP = masterInstance['Reservations'][0]['Instances'][0]['PublicDnsName']
authenticate(IP + ":7474", 'neo4j', 'Rn)BZ-C<adh4')

graph = Graph('http://' + IP + ":7474/db/data", secure=False)
query = """
        MERGE (r:Resource {name: 'ChEMBL'})
        """
results = graph.run(query)
tx = graph.begin()
tx.commit()

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
for index,row in enumerate(compounds_dict):
    if index == 0:
	print "PRIME"
    if index % 500 == 0:
	print index
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
    image = {'imageURL' : 'http://www.ebi.ac.uk/chemblws/compounds/%s/image/' % compound_ID,'imageByteArray' : img_src.encode('base64')}
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
k = 1
for index2,i in enumerate(prime):
    if index2 == 0:
	print "QUERIES"
    if index2 % 500 == 0:
	print index2 
    compoundData = i
    query = """
    WITH {compoundData} as comp
    UNWIND comp.compound as data
    MATCH (r:Resource) WHERE r.name = 'ChEMBL'
    MERGE (cmpd:Compound {InChiKey:data.stdInChiKey}) ON CREATE
        SET cmpd.canonicalSMILES = data.smiles, 
        cmpd.resourceID = data.chemblId,
        cmpd.molecularWeight = data.molecularWeight,
        cmpd.molecularFormula = data.molecularFormula,
        cmpd.knownDrug = data.knownDrug,
        cmpd.synonyms = data.synonyms,
        cmpd.rotatableBonds = data.rotatableBonds,
        cmpd.preferredCompoundName = data.preferredCompoundName
    MERGE (r)<-[:From]-(cmpd)
    MERGE (img:Image {URL:comp.imageURL})
    MERGE (cmpd)-[:Image]->(img)
    """
    results = graph.run(query,compoundData=compoundData)
    tx = graph.begin()
    tx.commit()
    for l in i['forms']:
        if l['parent'] == True:
            properties = {}
            properties['compound'] = i['compound']
            properties['parent'] = l
            query = """
            WITH {properties} as comp
            UNWIND comp.compound as data
            UNWIND comp.parent as par
            MATCH (cmpd:Compound) WHERE cmpd.InChiKey = data.stdInChiKey
            MERGE (parent:Compound  {resourceID: par.chemblId})
            MERGE (parent)<-[:SaltOf]-(cmpd)
            """
            results = graph.run(query, properties=properties)
            tx = graph.begin()
            tx.commit()
    for j in i['bioactivities']:
        bioData = j
        properties = {}
        properties['compound'] = i['compound']
        properties['bioData'] = j
        target_chembl = j['target_chemblid']
        bioType = j['bioactivity_type']
        target_data = json.loads(requests.get("http://www.ebi.ac.uk/chemblws/targets/%s.json" % target_chembl).content)
        properties['targetData'] = target_data['target']
        if ('proteinAccession' in target_data['target'].keys()) and ('Kd' in bioType or 'Ki' in bioType or 'IC50' in bioType):
            query = """
            WITH {properties} as comp
            UNWIND comp.bioData as bios
            UNWIND comp.compound as data
            UNWIND comp.targetData as target
            MATCH (cmpd:Compound) WHERE cmpd.InChiKey = data.stdInChiKey
            MATCH (r:Resource) WHERE r.name = 'ChEMBL'
            MERGE (k:Kinase {rcsID: bios.target_chemblid}) ON CREATE
                SET k.targetName = bios.target_name,
                k.nameInRef = bios.name_in_reference,
                k.ingredientCompoundChemblID = bios.ingredient_cmpd_chemblid,
                k.organism = bios.organism,
                k.accession = target.proteinAccession,
                k.targetType = target.targetType,
                k.geneNames = target.geneNames,
                k.compoundCount = target.compoundCount,
                k.bioactivityCount = target.bioactivityCount,
                k.synonyms = target.synonyms
            MERGE (cmpd)-[b:Bioactivity {bioactivityType: bios.bioactivity_type}]-(k) ON CREATE
                SET b.units = bios.units,
                b.value = bios.value,
                b.targetConfidence = bios.target_confidence,
                b.resourceAssayID = bios.assay_chemblid,
                b.assayDescription = bios.assay_description,
                b.assayType = bios.assay_type
            MERGE (l:Literature {ref: bios.reference})
            MERGE (l)<-[:ReferencedIn]-(k)
            """
            results = graph.run(query, properties=properties)
            tx = graph.begin()
            tx.commit()
            accession = target_data['target']['proteinAccession']
            accessionSplit = accession.split(',')
            if len(accessionSplit) > 1:
                for a in accessionSplit:
                    properties['accessionCheck'] = a
                    query = """
                    WITH {properties} as comp
                    UNWIND comp.bioData as bios
                    UNWIND comp.accessionCheck as acc
                    UNWIND comp.targetData as target
                    MATCH (complex:Kinase) WHERE complex.accession = target.proteinAccession
                    MERGE (single:Kinase {accession: acc})
                    MERGE (complex)<-[:Complex]-(single)
                    """
                    results = graph.run(query, properties=properties)
                    tx = graph.begin()
                    tx.commit()
    k += 1
