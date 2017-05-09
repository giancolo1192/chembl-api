#! /usr/bin/env python

import requests
import json
import csv
import re
import numpy as np 
from collections import defaultdict
######

########################################################################

# We use the compound ChEMBL ID, target ChEMBL ID and assay ChEMBL ID as inputs for our API calls

#check for the status of the ChEMBL API
status = json.loads(requests.get("http://www.ebi.ac.uk/chemblws/status/").content)

#Only execute if the ChEMBL API is UP and running
if status['service']['status'] == "UP":

    print """
# =========================================================
# 1. Use InChiKey to get compund details
# =========================================================
        """

###Look into testing with InChiKey
    ####Insert InChiKey as a variable script
    InChiKey = 'MLDQJTXFUGDVEO-UHFFFAOYSA-N'    
    if InChiKey == 'MLDQJTXFUGDVEO-UHFFFAOYSA-N':

    #with open('compoundlist.csv') as csvfile:
        #reader = csv.DictReader(csvfile)
        #for row in reader:
            #InChiKey = (row['InChiKey'])
        InChiKey = 'MLDQJTXFUGDVEO-UHFFFAOYSA-N'    
        just_compound = True

    ########################################################################
    #Description: Get individual compound by standard InChi Key
    #Input: Standard InChi Key
    #Output: Compound Record
        InChiKey_data = json.loads(requests.get("http://www.ebi.ac.uk/chemblws/compounds/stdinchikey/%s.json" % InChiKey).content)
        compound_ID = InChiKey_data["compound"]["chemblId"]
        print compound_ID

        print """
# =========================================================
# 1. Use ChEMBL ID for the rest of the compound details
# =========================================================
        """
    
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
        print "We got the compound bioactivities!"
    #print to verify we got the json

    ########################################################################
    #Description: Get alternative compound forms (e.g. parent and salts) of a compound 
    #Input: Compound ChEMBLID 
    #Output: List of ChEMBLIDs which correspond to alternative forms of query compound 
        compound_altforms = json.loads(requests.get("http://www.ebi.ac.uk/chemblws/compounds/%s/form.json" % compound_ID).content)
        print "We got the compounds alternate forms!"
    #print to verify we got the json

    ########################################################################
    #Description: Get mechanism of action details for compound (where compound is a drug) 
    #Input: Compound ChEMBLID 
    #Output: List of drug mechanism of action and ChEMBL target details 
        compound_mech_of_action = json.loads(requests.get("http://www.ebi.ac.uk/chemblws/compounds/%s/drugMechanism.json" % compound_ID).content)
        print "We got the compound mechanism of action!"
    #print to verify we got the json

        if just_compound != True:
            print """
# =========================================================
# Use Target ChEMBL ID to get target info
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

        if just_compound != True:
            print """
# =========================================================
# Use Assay ChEMBL ID to get compund details
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
    #with open('data.txt', 'w') as outfile:
        #json.dump(jsonData, outfile, sort_keys = True, indent = 4,
               #ensure_ascii = False)
    
    print "\n"
    print "Success! All data about %s has been collected" % compound_data['compound']['preferredCompoundName']
    
else:
    ###Return thois print so we know that the ChEMBL API is not "UP"  ~Working
    print "ChEMBL API is not UP!"