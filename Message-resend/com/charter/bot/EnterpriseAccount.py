from base64 import b64encode
from getpass import getpass
import re
import urllib3
import uuid
import json
import time
import os

import requests

# 
# reason = input("Reason for resend message(INC, JIRA or ALM number) : ")
# url = input("Enter URL : ")
# username = input("Enter username : ")
# password = getpass("Enter password : ", stream=None)
# inputFile = input("Enter input file location(with file name) : ")    
# outputFile = input("Enter output file location(with fine name) : ")        

reason = "TEST"
url = "https://eisbisoncw-uat.corp.chartercom.com/enterprise-account/api/enterprise/service/account"
username = "serviceuser"
password = "servicepassword"
inputFile = "C:/Users/rrajput/Desktop/MobileData/MobileData.csv"    
outputFile = "C:/Users/rrajput/Desktop/MobileData/MobileData-out.csv"       
urllib3.disable_warnings()
total = 0
sucess = 0
failure = 0
flushCounter = 0
d1 = time.time();


def clearScreen():
    if os.name == 'nt':
        _ = os.system('cls')
    else:
        _ = os.system('clear')


def printStatus():
    clearScreen()
    print("\nprocessed : " + str(total))
    print("\nsuccess : " + str(sucess))
    print("\nfailed : " + str(failure))
    print("\n-----------------------")
    print("\nTime elapsed : " + "{:.{}f}".format((time.time() - d1), 2) + " S")

print("Starting the process")

with open(inputFile, "r") as inputData, open(outputFile, "w+") as outputData:
    outputData.write("SoloCableAccountId,CableAccountNumber,SpcDivisionId,ucan,SoloMobileAccountId,MobileAccountNumber,AuthCableAccountId,TransactionId,Status\n")
    userAndPass = b64encode(bytes(username + ":" + password, "utf-8")).decode("ascii")
    for line in inputData:
        line = line.replace('\n', '').replace('\r', '')
        accountNumber = line.split(',')[0]
        spcDivisionId = line.split(',')[1]
        total = total + 1
        transactionId = reason + "-" + str(uuid.uuid4())
        baseHeaders = {'content-type': 'application/json', 'Authorization' : 'Basic %s' % userAndPass,'transaction-id':transactionId }
#                    'transactionId':transactionId ,'billerAccountNumber':accountNumber,'spcDivisionId': spcDivisionId }
        body = None 
        cableAccountId = None
        ucan = None
        mobileAccountId = None
        billerMobileAccountNumber =None
        authorizingAccountId=None
        # prepareGetRequestForCable(accountNumber=accountNumber,spcDivisionId=spcDivisionId, transactionId=transactionId)
        try:
            headersGetCable = {'billerAccountNumber':accountNumber }
            headersGetCable.update(baseHeaders)
            responseGetCable = requests.get(url + "?spcDivisionId=" + spcDivisionId, data=body, headers=headersGetCable, verify=False)
#             print(response.content)
            if responseGetCable.status_code == 200:
                cableAccountData = responseGetCable.json()
                cableAccount = [x for x in cableAccountData["accounts"] if x['accountType'] == 'CABLE']
                if cableAccount is not None and cableAccount != []:
                    cableAccountId = cableAccount[0]["soloAccountId"] 
                    ucan = cableAccount[0]["ucan"]
                    headersGetMobile = {'authorizingAccountId':str(cableAccountId) }
                    headersGetMobile.update(baseHeaders)
                    responseGetMobile = requests.get(url, data=body, headers=headersGetMobile, verify=False)
                    if responseGetMobile.status_code == 200:
                        mobileAccountData = responseGetMobile.json()
                        mobileAccount = [x for x in mobileAccountData["accounts"] if x['accountType'] == 'MOBILE']
                        if mobileAccount is not None and mobileAccount != []:
                            mobileAccountId = mobileAccount[0]["soloAccountId"] 
                            billerMobileAccountNumber = mobileAccount[0]["billerAccountNumber"]
                            authorizingAccountId = mobileAccount[0]["authorizingAccountId"]
                            outputData.write(str(cableAccountId) + "," + accountNumber + "," + spcDivisionId + "," + str(ucan) + "," + str(mobileAccountId) + "," + billerMobileAccountNumber + "," + str(authorizingAccountId) + "," + transactionId + ",success\n")
                            sucess = sucess + 1
                        else:
                            failure = failure + 1
                            outputData.write(str(cableAccountId) + "," + accountNumber + "," + spcDivisionId + "," + str(ucan) + "," + "," + "," + "," + transactionId + ",failed- mobile account not found.\n")
                    else:
                        failure = failure + 1
                        outputData.write(str(cableAccountId) + "," + accountNumber + "," + spcDivisionId + "," + str(ucan) + "," + "," + "," + "," + transactionId + ",failed- get mobile account response status is not 200. status = " + str(responseGetMobile.status_code) + "\n")
                else:
                    failure = failure + 1
                    outputData.write("," + accountNumber + "," + spcDivisionId + "," + "," + "," + "," + "," + transactionId + ",failed- cable account not found.\n")
            else:
                failure = failure + 1
                outputData.write("," + accountNumber + "," + spcDivisionId + "," + "," + "," + "," + "," + transactionId + ",failed- get cable account response status is not 200. status = " + str(responseGetCable.status_code) + "\n")
        except Exception as exe:
            print(exe)
            failure = failure + 1
            outputData.write("," + accountNumber + "," + spcDivisionId + "," + "," + "," + "," + "," + transactionId + ",failed- exception " + str(exe) + "\n")
            
        if flushCounter == 10:
            printStatus()
            outputData.flush()
            flushCounter = 0

printStatus()
print("\nExiting the process ")
exit(1)
