from base64 import b64encode
from getpass import getpass
import re
import urllib
import uuid
import json
import requests
import urllib3
from xml.dom import minidom
from os import system, name
import time

import xml.etree.ElementTree as ET

reason = input("Reason to transfer Identities (INC, JIRA or ALM number) : ")
url = input("DSB URL : ")
# username = input("Enter username : ")
# password = getpass("Enter password : ", stream=None)
inputFile = input("Enter input file location(with file name) : ")    
outputFile = input("Enter output file location(with file name) : ")        
d1 = time.time();

# reason = 'CESCHTRENT-14747'
# url = 'https://qa03-dsb-app.eng.rr.com'
# inputFile = 'D:/MOBILETRANSFER/UAT-TEST.csv'
# outputFile = 'D:/MOBILETRANSFER/UAT-TEST-OUT.csv'
logDMIDSB =True

urllib3.disable_warnings()
total = 0
sucess = 0
failure = 0
flushCounter = 0

# QA: https://qa03-dsb-app.eng.rr.com
# UAT: https://cdpuvdsbapa0001.eng.rr.com
# PROD: https://http.dsb.charter.com/


# # parse xml
def parseQueryAccount(ANSWER):
    returnVal = ['ERROR', 'UNKNOWN']
    try:
        tree = ET.fromstring(ANSWER)
        status = tree.find('./Header/Status')
        if status is not None:
            status = status.attrib['id']
        if status is not None and status.upper() == 'ERROR':
            msg = tree.find('./Body/Account/Exception/Message').attrib['value']
            returnVal = ['ERROR', 'Error in query account: ' + msg]
        elif status is not None and status.upper() == 'OK':
            dsbid = tree.find("./Body/Account/ID/[@ns='DSB']").attrib['value']
            returnVal = ['SUCCESS', dsbid]        
        else:
            returnVal = ['ERROR', 'UNKNOWN']
        return returnVal
    except Exception:
        returnVal = ['ERROR', ex]
        return returnVal;    


def parseTransferIdentity(ANSWER):
    returnVal = ['ERROR', 'UNKNOWN']
    try:
        tree = ET.fromstring(ANSWER)
        status = tree.find('./Header/Status')
        if status is not None:
            status = status.attrib['id']
        if status is not None and status.upper() == 'ERROR':
            customerSuccess = tree.findall("./Body/Customer[@status='ok']")
            if customerSuccess is not None and len(customerSuccess) != 0:
                returnVal = ['SUCCESS', '']
            else:
                returnVal = ['ERROR', 'Error in Identity transfer: ']
                accountStatus = tree.find('./Body/Account').attrib['status']
                if accountStatus is not None and accountStatus.upper() == 'ERROR':
                    msg = tree.find('./Body/Account/Exception/Message').attrib['value']
                    returnVal = ['ERROR', 'Error in Identity transfer: ' + msg]
        else:
            returnVal = ['SUCCESS', '']        
        return returnVal
    except Exception as ex:
        returnVal = ['ERROR', ex]
        return returnVal; 


def prepareQueryAccountRequest(fromAccountNumber, fromSpcDivisionId, transactionId, endpointId):
    division = fromSpcDivisionId.split('.')
    body = (
            '<ASBMessage version="2.0" id="' + transactionId + '">'
            +'<Header><Endpoint>'
            +'<ID value="' + endpointId + '"/>'
            +'</Endpoint><Context id="request"/><Itinerary><Endpoint uri="asb://asb.twcable.com/dsb/channel/common"/></Itinerary></Header><Body><Account operation="query">'
            +'<ID value="' + makeIt9Digit(accountNumber=fromAccountNumber) + '" ns="ESB"/>'
            +'<Division id="' + division[0] + '"/>'
            +'<Billing id="' + division[1] + '"/>'
            +'</Account></Body></ASBMessage>'
            )
    return body;


def prepareTransferIdentityRequest(DSBId, toAccountNumber, toSpcDivisionId, transactionId, endpointId):
    division = toSpcDivisionId.split('.')
    body = (
            '<ASBMessage version="2.0" id="' + transactionId + '">'
            +'<Header><Endpoint>'
            +'<ID value="' + endpointId + '"/>'
            +'</Endpoint><Context id="request"/><Itinerary><Endpoint uri="asb://asb.twcable.com/dsb/channel/idms/account/identities"/></Itinerary><BusinessProcess><ID value="IdentitiesTransfer"/></BusinessProcess>'
            +'</Header><Body><Account>'
            +'<ID ns="DSB" value="' + DSBId + '"/>'
            +'<Account meta="operation;update">'
            +'<ID ns="ESB" value="' + makeIt9Digit(accountNumber=toAccountNumber) + '"/>'
            +'<Division id="' + division[0] + '"/>'
            +'<Billing id="' + division[1] + '"/>'
            +'</Account></Account></Body></ASBMessage>'
            )
    return body;

def makeIt9Digit(accountNumber):
    if len(accountNumber) <9:
        accountNumber = accountNumber.zfill(9)
        return accountNumber
    else:
        return accountNumber
        


def getXmlString(ANSWER):
    xmlstr=''
    if logDMIDSB:
        xmlstr = ET.tostring(element=ET.fromstring(ANSWER), encoding='utf-8', method='xml')
        xmlstr =str(xmlstr,'utf-8').replace('\n', '').replace('\r', '').replace('\t',' ')
#     print(xmlstr)
    return xmlstr

def clearScreen():
    if name == 'nt':
        _=system('cls')
    else:
        _=system('clear')
    
def printStatus():
    clearScreen()
    print("\nprocessed : " + str(total))
    print("\nsuccess : " + str(sucess))
    print("\nfailed : " + str(failure))
    print("\n-----------------------")
    print("\nTime elapsed : "+ "{:.{}f}".format( (time.time()-d1), 2 )+" S" )
    

printStatus()
with open(inputFile, "r") as inputDataFile, open(outputFile, "w+") as outputData:
    outputData.write("from_catalystacctnumber,from_solo_acct_id,from_xdw2_acct_key,from_spc_div_id,from_acct_num,from_acct_clse_dt,UCAN,to_catalystacctnumber,to_solo_acct_id,to_xdw2_acct_key,to_spc_div_id,to_acct_num,transactionId,status,reason,queryAccountResponse,transferIdentityResponse\n")
#     userAndPass = b64encode(bytes(username + ":" + password, "utf-8")).decode("ascii")
    headers = {} 
    for line in inputDataFile:
        line = line.replace('\n', '').replace('\r', '')
        inputData = line.split(',')
        total = total + 1
        flushCounter = flushCounter + 1
        queryAccountResponseData=''
        transferIdentityResponseData=''
        transactionId = reason + "-" + str(uuid.uuid4())
        endpointId = 'MOBILE-IDNT-TRAN-' + reason
        headers = {'content-type': 'application/xml'}
        if(inputData[0].strip() != ''):
            outputData.write(line + "," + transactionId + ",failed,from_catalystacctnumber is not blank"+",,"+"\n")
            failure = failure + 1
        elif(inputData[4].strip() == ''):
            outputData.write(line + "," + transactionId + ",failed,from_account_number is blank"+",,"+"\n")
            failure = failure + 1
        elif(inputData[3].strip() == ''):
            outputData.write(line + "," + transactionId + ",failed,from_spc_div_id is blank"+",,"+"\n")
            failure = failure + 1
        elif(inputData[7].strip() == ''):
            outputData.write(line + "," + transactionId + ",failed,to_catalystacctnumber is blank"+",,"+"\n")
            failure = failure + 1
        elif(inputData[11].strip() == ''):
            outputData.write(line + "," + transactionId + ",failed,to_account_number is blank"+",,"+"\n")
            failure = failure + 1
        elif(inputData[10].strip() == ''):
            outputData.write(line + "," + transactionId + ",failed,to_spc_div_id is blank"+",,"+"\n")
            failure = failure + 1
        else:
#             print(inputData[0]+","+inputData[4]+","+inputData[3]+","+inputData[7]+","+inputData[11]+","+inputData[10])
            queryAccountRequest = prepareQueryAccountRequest(fromAccountNumber=inputData[4].strip(), fromSpcDivisionId=inputData[3].strip(), transactionId=transactionId, endpointId=endpointId)
            try:
                queryAccountResponse = requests.post(url, data=queryAccountRequest, headers=headers, verify=False)
                queryAccountResponseData = getXmlString(ANSWER=queryAccountResponse.content)
                resultData = parseQueryAccount(queryAccountResponse.content)
                if resultData[0] == 'SUCCESS':
                    transferIdentityRequest = prepareTransferIdentityRequest(DSBId=resultData[1], toAccountNumber=inputData[11], toSpcDivisionId=inputData[10], transactionId=transactionId, endpointId=endpointId)
                    transferIdentityResponse = requests.post(url, data=transferIdentityRequest, headers=headers, verify=False)
                    transferIdentityResponseData=getXmlString(ANSWER=transferIdentityResponse.content)
                    transferIdentityResultData = parseTransferIdentity(transferIdentityResponse.content)
                    if transferIdentityResultData[0] == 'SUCCESS':
                        sucess = sucess + 1
                        outputData.write(line + "," + transactionId + ",success"+",,"+queryAccountResponseData +","+transferIdentityResponseData +"\n")
                    else:
                        failure = failure + 1
                        outputData.write(line + "," + transactionId + ",failed," + transferIdentityResultData[1] +","+queryAccountResponseData+","+transferIdentityResponseData+"\n")
                else:
                    failure = failure + 1
                    outputData.write(line + "," + transactionId + ",failed," + resultData[1] +","+queryAccountResponseData+","+transferIdentityResponseData+"\n")
            except Exception as ex:
                print(ex)
                failure = failure + 1
                outputData.write(line + "," + transactionId + ",failed", ex +","+queryAccountResponseData+","+transferIdentityResponseData+"\n")
        if total == 10 and total == failure:
            print("Seems some issue here. Total processed : " + str(total) + " Total failed : " + str(failure))
            failureCheck = input("Do you want to continue Y/N :")
            if "Y" != failureCheck.upper():
                print("\nExiting the process ")
                inputDataFile.close()
                outputData.close()
                exit(1)
        if flushCounter == 10:
            printStatus()
            outputData.flush()
            flushCounter = 0

printStatus()
print("\nExiting the process ")
exit(1)