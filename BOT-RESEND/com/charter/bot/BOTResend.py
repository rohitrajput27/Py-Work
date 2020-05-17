from base64 import b64encode
from getpass import getpass
import re
import urllib
import uuid

import requests

import xml.etree.ElementTree as ET

reason = input("Reason for resend message(INC, JIRA or ALM number) : ")
url = input("Enter URL : ")
username = input("Enter username : ")
password = getpass("Enter password : ", stream=None)
inputFile = input("Enter input file location(with file name) : ")    
outputFile = input("Enter output file location(with fine name) : ")        

total = 0
sucess = 0
failure = 0


def parse(ANSWER):
    returnVal = '0'
    try:
        tree = ET.fromstring(ANSWER)
        result={}
        for item in tree.getiterator():
#             print(item.tag)
#             print(item.text)
            if item.tag == 'return':
                returnVal = item.text
#             result[item.tag] = item.text
        return returnVal
    except Exception:
        return returnVal;    


def prepareRequest(orderid, transactionId):
    body = ('<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:syn="http://www.charter.com/biller/order/translator/synch">'
            +'<soapenv:Header>'
            +'<syn:charterHeaderInputInfo>'
            +'<clientCallingService>BOTRESEND</clientCallingService>'
            +'<auditUser>' + reason + '</auditUser>'
            +'<transactionId>' + transactionId + '</transactionId>'
            +'</syn:charterHeaderInputInfo>'
            +'</soapenv:Header>'
            +'<soapenv:Body>'
            +'<syn:triggerBillerOrderTranslatorSynchRequest>'
            +'<soloOrderId>' + orderid + '</soloOrderId>'
            +'</syn:triggerBillerOrderTranslatorSynchRequest>'
            +'</soapenv:Body>'
            +'</soapenv:Envelope>')
    return body;


with open(inputFile, "r") as inputData, open(outputFile, "w+") as outputData:
    outputData.write("SoloOrderID,TransactionId,Status\n")
    userAndPass = b64encode(bytes(username + ":" + password, "utf-8")).decode("ascii")
    headers = {'content-type': 'text/xml', 'Authorization' : 'Basic %s' % userAndPass}
    for line in inputData:
        line = line.replace('\n','').replace('\r','')
        total = total + 1
        transactionId = reason+"-" + str(uuid.uuid4())
        body = prepareRequest(orderid=line, transactionId=transactionId)
        try:
            response = requests.post(url, data=body, headers=headers, verify=False)
#             print(response.content)
            if parse(response.content) == '1':
                sucess = sucess + 1
                outputData.write(line+","+transactionId+",success\n")
            else:
                failure = failure + 1
                outputData.write(line+","+transactionId+",failed\n")
        except Exception:
            failure = failure + 1
            outputData.write(line+","+transactionId+",failed\n")
            
        if total == 10 and total == failure:
            print("Seems some issue here. Total processed : " + str(total) + " Total failed : " + str(failure))
            failureCheck = input("Do you want to continue Y/N :")
            if "Y" != failureCheck.upper():
                print("\nExiting the process ")
                inputData.close()
                outputData.close()
                exit(1)
        
        

print("\nTotal processed : "+str(total))
print("\nTotal success : "+str(sucess))
print("\nTotal failed : "+str(failure))
print("\nExiting the process ")
exit(1)
