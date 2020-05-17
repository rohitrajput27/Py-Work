from base64 import b64encode
from getpass import getpass
import re
import urllib
import uuid
import json
import requests
import urllib3
from os import system, name
import time

import xml.etree.ElementTree as ET
from _overlapped import NULL

d1 = time.time();
reason = input("Reason for resend message(INC, JIRA or ALM number) : ")
url = input("Enter URL : ")
username = input("Enter username : ")
password = getpass("Enter password : ", stream=None)
inputFile = input("Enter input file location(with file name) : ")    
outputFile = input("Enter output file location(with fine name) : ")        

urllib3.disable_warnings()
total = 0
sucess = 0
failure = 0
flushCounter=0

### parse xml
# def parse(ANSWER):
#     returnVal = '0'
#     try:
#         tree = ET.fromstring(ANSWER)
#         result = {}
#         for item in tree.getiterator():
# #             print(item.tag)
# #             print(item.text)
#             if item.tag == 'transactionId':
#                 returnVal = item.text
# #             result[item.tag] = item.text
#         return returnVal
#     except Exception:
#         return returnVal;    


### parse json
def parse(ANSWER):
    errorMessage=''
    try:
        responseData = json.loads(ANSWER)
        if "errorResponse" in responseData:
            errorResponse  = responseData["errorResponse"]
            if errorResponse is not None and "errorMessage" in errorResponse:
                errorMessage = errorResponse["errorMessage"]
                
        return errorMessage
    except Exception:
        return 'UNKNOWN ERROR';  

def prepareRequest(fromAccountNumber,fromSpcDivisionId,toAccountNumber,toSpcDivisionId):
    body = (
            '{'
            +'"fromAccountNumber":"'+fromAccountNumber+'",'
            +'"fromSPCDivisionId":"'+fromSpcDivisionId+'",'
            +'"toAccountNumber":"'+toAccountNumber+'",'
            +'"toSPCDivisionId":"'+toSpcDivisionId+'"'
            +'}'
            )
    return body;

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

with open(inputFile, "r") as inputDataFile, open(outputFile, "w+") as outputData:
    outputData.write("from_catalystacctnumber,from_solo_acct_id,from_xdw2_acct_key,from_spc_div_id,from_acct_num,from_acct_clse_dt,UCAN,to_catalystacctnumber,to_solo_acct_id,to_xdw2_acct_key,to_spc_div_id,to_acct_num,transactionId,status,reason\n")
    userAndPass = b64encode(bytes(username + ":" + password, "utf-8")).decode("ascii")
    headers ={} 
    for line in inputDataFile:
        line = line.replace('\n', '').replace('\r', '')
        inputData = line.split(',')
        total = total + 1
        flushCounter =flushCounter+1
        transactionId = reason + "-" + str(uuid.uuid4())
        headers = {'content-type': 'application/json', 'Authorization' : 'Basic %s' % userAndPass,'transaction-Id':transactionId,'transaction-id':transactionId,'TxRoot':transactionId}
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
            body = prepareRequest(fromAccountNumber=inputData[1].strip(), fromSpcDivisionId=inputData[2].strip(), toAccountNumber=inputData[4].strip(), toSpcDivisionId=inputData[5].strip())
            try:
                response = requests.post(url, data=body, headers=headers, verify=False)
#                 print(response.content)
                resultData = parse(response.content)
                if resultData == '':
                    sucess = sucess + 1
                    outputData.write(line + "," + transactionId + ",success\n")
                else:
                    failure = failure + 1
                    outputData.write(line + "," + transactionId + ",failed,"+resultData+"\n")
            except Exception:
                failure = failure + 1
                outputData.write(line + "," + transactionId + ",failed\n")
                
        if total == 10 and total == failure:
            print("Seems some issue here. Total processed : " + str(total) + " Total failed : " + str(failure))
            failureCheck = input("Do you want to continue Y/N :")
            if "Y" != failureCheck.upper():
                print("\nExiting the process ")
                inputDataFile.close()
                outputData.close()
                exit(1)
        
        if flushCounter == 10:
            clearScreen()
            print("\nprocessed : " + str(total))
            print("\nsuccess : " + str(sucess))
            print("\nfailed : " + str(failure))
            print("\n-----------------------")
            outputData.flush()
            flushCounter=0

clearScreen()
print("\nTotal processed : " + str(total))
print("\nTotal success : " + str(sucess))
print("\nTotal failed : " + str(failure))
print("\nExiting the process ")
exit(1)
