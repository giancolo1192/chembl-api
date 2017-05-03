#! /usr/bin/env python

import requests
import json
import re
######

########################################################################

# We use the compound ChEMBL ID, target ChEMBL ID and assay ChEMBL ID as inputs for our API calls

#check for the status of the ChEMBL API
status = json.loads(requests.get("http://www.ebi.ac.uk/chemblws/status/").content)

#Only execute if the ChEMBL API is UP and running
if status['service']['status'] == "UP":

    print """
# =========================================================
# 1. Use Compound ChEMBL ID to get compund details
# =========================================================
    """
		
    compound_ID = 'CHEMBL1200485'
    is_target = False
    is_assay = False
    target_ID = 'CHEMBL240'
    assay_ID = 'CHEMBL1217643'
    if is_target == True:
        target_ID = compound_ID

    if is_assay == True:
        assay_ID = compound_ID

    ########################################################################
    #Description: Get compound by ChEMBLID 
    #Input: Compound ChEMBLID 
    #Output: Compound Record 
    compound_data = json.loads(requests.get("http://www.ebi.ac.uk/chemblws/compounds/%s.json" % compound_ID).content)
    print "Compound Name:             %s" % compound_data['compound']['preferredCompoundName']
    print "Compound CHEMBLID:         %s" % compound_data['compound']['chemblId']
    print "Compound stdInChiKey:      %s" % compound_data['compound']['stdInChiKey']
    print "Compound Canonical SMILES: %s" % compound_data['compound']['smiles']
    #print to verify we got the json

    ########################################################################
    #Description: Get the image of a given compound. 
    #Input: Compound ChEMBLID 
    #Output: Byte array image data
    compound_image = "http://www.ebi.ac.uk/chemblws/compounds/%s/image" % compound_ID
    print "\n"
    print "See compound image here: " + compound_image
    #print to verify we got the json

    ########################################################################
    #Description: Get individual compound bioactivities 
    #Input: Compound ChEMBLID 
    #Output: List of all bioactivity records in ChEMBLdb for a given compound ChEMBLID 
    compound_bioactivities = json.loads(requests.get("http://www.ebi.ac.uk/chemblws/compounds/%s/bioactivities.json" % compound_ID).content)
    print "\n"
    print "We got the compound bioactivities!"
    #print to verify we got the json

    ########################################################################
    #Description: Get alternative compound forms (e.g. parent and salts) of a compound 
    #Input: Compound ChEMBLID 
    #Output: List of ChEMBLIDs which correspond to alternative forms of query compound 
    compound_altforms = json.loads(requests.get("http://www.ebi.ac.uk/chemblws/compounds/%s/form.json" % compound_ID).content)
    print "\n"
    print "We got the compounds alternate forms!"
    #print to verify we got the json

    ########################################################################
    #Description: Get mechanism of action details for compound (where compound is a drug) 
    #Input: Compound ChEMBLID 
    #Output: List of drug mechanism of action and ChEMBL target details 
    compound_mech_of_action = json.loads(requests.get("http://www.ebi.ac.uk/chemblws/compounds/%s/drugMechanism.json" % compound_ID).content)
    print "\n"
    print "We got the compound mechanism of action!"
    #print to verify we got the json


    print """
# =========================================================
# 2. Use Target ChEMBL ID to get target info
# =========================================================
    """
    ########################################################################
    #Description: Get target by ChEMBLID 
    #Input: Target ChEMBLID 
    #Output: Target Record
    target_data = json.loads(requests.get("http://www.ebi.ac.uk/chemblws/targets/%s.json" % target_ID).content)
    print "\n"
    print "We got the target!"
    #print to verify we got the json

    ########################################################################
    #Description: Get individual target bioactivities 
    #Input: Target ChEMBLID 
    #Output: List of all bioactivity records in ChEMBLdb for a given target ChEMBLID 
    target_bioactivites = json.loads(requests.get("http://www.ebi.ac.uk/chemblws/targets/%s/bioactivities.json" % target_ID).content)
    print "\n"
    print "We got the target bioactivities!"
    #print to verify we got the json

    ########################################################################
    #Description: Get approved drugs for target 
    #Input: Target ChEMBLID 
    #Output: List of approved drugs and and ChEMBL compound details
    target_drugs = json.loads(requests.get("http://www.ebi.ac.uk/chemblws/targets/%s/approvedDrug.json" % target_ID).content)
    print "\n"
    print "We got the approved drugs for this ChEMBL target!"
    #print to verify we got the json

    print """
# =========================================================
# 3. Use Assay ChEMBL ID to get compund details
# =========================================================
    """

    ########################################################################
    #Description: Get assay by ChEMBLID 
    #Input: Assay ChEMBLID 
    #Output: Assay Record
    assay_data = json.loads(requests.get("http://www.ebi.ac.uk/chemblws/assays/%s.json" % assay_ID).content)
    print "\n"
    print "We got the assay!"
    #print to verify we got the json

    ########################################################################
    #Description: Get individual assay bioactivities 
    #Input: Assay ChEMBLID 
    #Output: List of all bioactivity records in ChEMBLdb for a given assay ChEMBLID 
    assay_bioactivities = json.loads(requests.get("http://www.ebi.ac.uk/chemblws/assays/%s/bioactivities.json" % assay_ID).content)
    print "\n"
    print "We got the assay bioactivities!"
    #print to verify we got the json
else:
    print "ChEMBL API is not UP!"
