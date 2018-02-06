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
tx.commit()

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
    print(index)

c_file.close()
