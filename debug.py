#! /usr/bin/env python
import urllib
import pprint
import requests
import json
import csv
import re
import boto3
import os
import sys
from py2neo import Graph, Node, Relationship
from py2neo import Path, authenticate
######

# Sever connection
# ec2 = boto3.client('ec2')
# masterInstance = ec2.describe_instances(
#     Filters=[
#         {
#             'Name':'tag:Rank',
#             'Values':['Master']
#         },
#         {
#             'Name':'tag:Group',
#             'Values':['TruvitechDB']
#         }
#     ]
# )
# IP = masterInstance['Reservations'][0]['Instances'][0]['PublicDnsName']
# authenticate(IP + ":7474", 'neo4j', 'Rn)BZ-C<adh4')
# graph = Graph('http://' + IP + ":7474/db/data", secure=False)

#Local connection
authenticate("localhost:7474", 'april', 'L8kc,![(^X3Q')
graph = Graph("localhost:7474/db/data", secure=False)

tx = graph.begin()
query = """
        MERGE (r:Resource {name: 'ChEMBL'})
        return r
        """
results = graph.run(query).data()

# We use the compound ChEMBL ID, target ChEMBL ID and assay ChEMBL ID as inputs for our API calls
def check_status(url):
    """ Checks for errors in HTTP response

    :param url: the url to check
    :returns: error string or full HTTP response
    """
    try:
        response = requests.get(url)
    except requests.exceptions.ConnectionError as e:
        return "connection error %s" % e
    except requests.exceptions.HTTPError as e:
        return "http error %s" % e
    except requests.exceptions.Timeout as e:
        return "timeout error"
    except requests.exceptions.RequestException as e:
        return "general error %s" % e

    status = response.status_code
    status_i = 0
    if status < 200 or status >= 400:
        while status < 200 or status >=400:
            status_i += 1
            response = requests.get(url)
            status = response.status_code
            if status_i > 10:
                return "status error %d on %d" % (status, global_i)
                break
        return response
    return response

def move_on(url):
    """ Determines whether or not to let the code continue based on HTTP errors.

    :param url: The url to test
    :type url: string
    :returns:
    :rtype:
    """
    ret = {"continue": True, "response": ""}
    handled = check_status(url)
    handledStr = str(handled)
    if hasattr(handled, "status_code") and handled.status_code == 404:
        ret["continue"] == True
    elif hasattr(handled, "content"):
        content = str(handled.content)
        if "error" in content or "Compound not found" in content:
            ret["continue"] = True
        else:
            ret["continue"] = False
            ret["response"] = handled
    elif "error" in handledStr:
        print(handledStr)
        ret["continue"] = True
    return ret

#Check for the status of the ChEMBL API
handled = move_on("http://www.ebi.ac.uk/chemblws/status")
if handled["continue"] == True:
    print("Could not reach ChEMBL")
    sys.exit()
status = json.loads(handled["response"].content)

#Compound list from server
# s3 = boto3.client('s3')
# compounds_object = s3.get_object(
#     Bucket='compounds',
#     Key='compundlist/compoundlist.csv',
#     ResponseContentType='text/csv'
# )
# compounds_dict = csv.DictReader(
#     compounds_object['Body'].read().decode("utf-8-sig").split('\n'),
#     delimiter=','
# )

#Local compound list
c_file = open("../compoundlist-short.csv")
compounds_dict = csv.DictReader(c_file)

#Loops through all InChiKeys
for index,row in enumerate(compounds_dict):
    global_i = index
    if index > 0:
        break
    InChiKey = row['InChiKey']
    compound_data = {}
########################################################################
#Description: Get individual compound by standard InChi Key
#Input: Standard InChi Key
#Output: Compound Record
    handled = move_on("http://www.ebi.ac.uk/chemblws/compounds/stdinchikey/%s.json" % InChiKey)
    if handled["continue"] == True:
        continue
    else:
        response = handled["response"]
    InChiKey_data = json.loads(response.content)
    compound_ID = InChiKey_data["compound"]["chemblId"]

########################################################################
#Description: Get compound by ChEMBLID
#Input: Compound ChEMBLID
#Output: Compound Record
    handled = move_on("http://www.ebi.ac.uk/chemblws/compounds/%s.json" % compound_ID)
    if handled["continue"] == True:
        continue
    else:
        response = handled["response"]
    cmpd_data = json.loads(response.content)
    compound_data.update(cmpd_data)

    ########################################################################
    #Description: Get the image of a given compound.
    #Input: Compound ChEMBLID
    #Output: Byte array image data
    #byte data not used later. Store the image in s3 and link to that?
    # urladdy = 'http://www.ebi.ac.uk/chemblws/compounds/%s/image/' % compound_ID
    # filename = r'/home/ubuntu/chembl-api/image_of_%s.png' % InChiKey
    # urllib.urlretrieve(urladdy, filename)
    # open_path = open('/home/ubuntu/chembl-api/image_of_%s.png' % InChiKey)
    # img_src = open('/home/ubuntu/chembl-api/image_of_%s.png' % InChiKey).read()
    image = {
    'imageURL' : 'http://www.ebi.ac.uk/chemblws/compounds/%s/image/' % compound_ID,
    # 'imageByteArray' : img_src.encode('base64')
    }
    # open_path.close()
    compound_data.update(image)
    #Delete the png after storing byte array
    # os.remove('/home/ubuntu/chembl-api/image_of_%s.png' % InChiKey)

########################################################################
#Description: Get individual compound bioactivities
#Input: Compound ChEMBLID
#Output: List of all bioactivity records in ChEMBLdb for a given compound ChEMBLID
    handled = move_on("http://www.ebi.ac.uk/chemblws/compounds/%s/bioactivities.json" % compound_ID)
    if handled["continue"] == True:
        continue
    else:
        response = handled["response"]
    compound_bioactivities = json.loads(response.content)
    compound_data.update(compound_bioactivities)

########################################################################
#Description: Get alternative compound forms (e.g. parent and salts) of a compound
#Input: Compound ChEMBLID
#Output: List of ChEMBLIDs which correspond to alternative forms of query compound
    handled = move_on("http://www.ebi.ac.uk/chemblws/compounds/%s/form.json" % compound_ID)
    if handled["continue"] == True:
        continue
    else:
        response = handled["response"]
    compound_altforms = json.loads(response.content)
    compound_data.update(compound_altforms)

    #creates the base compound and image nodes with attachment to resource
    #Use CREATE instead of MERGE? (Not with testing ^.^')
    # Can we use Py2neo functions instead of the string to make the query?
    # Would it be a good idea to keep the transaction open at least for one iteration of the loop?
    query = """
    WITH {compound_data} as comp
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
    # graph.run(query,compound_data=compound_data)

    #Add parent nodes and relationships
    for l in compound_data['forms']:
        if l['parent'] == True:
            properties = {}
            properties['compound'] = compound_data['compound']
            properties['parent'] = l
            query = """
            WITH {properties} as comp
            UNWIND comp.compound as data
            UNWIND comp.parent as par
            MATCH (cmpd:Compound) WHERE cmpd.InChiKey = data.stdInChiKey
            MERGE (parent:Compound  {resourceID: par.chemblId})
            MERGE (parent)<-[:SaltOf]-(cmpd)
            """
            # graph.run(query, properties=properties)

    #add bioactivities
    for cnt,j in enumerate(compound_data['bioactivities']):
        if(cnt > 29):
            break
        bioData = j
        properties = {}
        properties['compound'] = compound_data['compound']
        properties['bioData'] = j
        target_chembl = j['target_chemblid']
        bioType = j['bioactivity_type']
        handled = move_on("http://www.ebi.ac.uk/chemblws/targets/%s.json" % target_chembl)
        if handled["continue"] == True:
            continue
        else:
            target_response = handled["response"]
        target_data = json.loads(target_response.content)
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
        print(cnt)
    tx.commit()

c_file.close()
