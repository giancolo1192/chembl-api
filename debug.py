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
        return "connection error %s" % e[0]
    except requests.exceptions.HTTPError as e:
        return "http error %s" % e[0]
    except requests.exceptions.Timeout as e:
        return "timeout error"
    except requests.exceptions.RequestException as e:
        return "general error %s" % e[0]

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

    ret['continue'] is a strict Boolean. So it is best to test the return of this function in strict terms.

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
