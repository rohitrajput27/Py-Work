from base64 import b64encode
from getpass import getpass
import re
import urllib
import uuid
import cx_Oracle
import requests

import xml.etree.ElementTree as ET

import os
import platform

LOCATION = r"C:\Users\rrajput\Desktop\SoloAccountID\instantclient-basic-win64-10.2.0.5\instantclient_10_2"
print("ARCH:", platform.architecture())
print("FILES AT LOCATION:")
for name in os.listdir(LOCATION):
    print(name)
os.environ["PATH"] = LOCATION + ";" + os.environ["PATH"]

# reason = input("Reason for resend message(INC, JIRA or ALM number) : ")
# url = input("Enter URL : ")
# username = input("Enter username : ")
# password = getpass("Enter password : ", stream=None)
# inputFile = input("Enter input file location(with file name) : ")    
# outputFile = input("Enter output file location(with fine name) : ")        

inputFile=r"C:\Users\rrajput\Desktop\SoloAccountID\soloAccountIdsToSelectTEST.txt"
outputFile=r"C:\Users\rrajput\Desktop\SoloAccountID\soloAccountIdsToSelectTEST-OUT.txt"

total = 0
sucess = 0
failure = 0

dsn_tns = cx_Oracle.makedsn('ora-prod55.twcable.com', '1521', service_name='zlds01p_nce02_svc_ro.corp.chartercom.com')  # if needed, place an 'r' before any parameter in order to address special characters such as '\'.
conn = cx_Oracle.connect(user='XAVIENT_READONLY', password='Mar#12020XavProdPass', dsn=dsn_tns)  # if needed, place an 'r' before any parameter in order to address special characters such as '\'. For example, if your user name contains '\', you'll need to place 'r' before the user name: user=r'User Name'

c = conn.cursor()

with open(inputFile, "r") as inputData, open(outputFile, "w+") as outputData:
    outputData.write("SoloOrderID,UCAN\n")
    for line in inputData:
        line = line.replace('\n', '').replace('\r', '')
        total = total + 1
        try:
            c.execute('''
            select aa.account_id,cc.ucan from chtr.t_account aa
            inner join chtr.t_customer_account ca on ca.account_id  = aa.account_id 
            inner join chtr.t_customer cc on cc.customer_id = ca.customer_id 
            where 
            aa.record_stat ='A'
            and
            fca.record_stat ='A'
            and
            cc.record_stat ='A'
            and
            aa.account_id   ='''
            +
            line
            )
            for row in c:
#                 print (row[0], '-', row[1])  # this only shows the first two columns. To add an additional column you'll need to add , '-', row[2], etc.
                outputData.write(row[0]+","+row[1]+"\n")
        except Exception:
            failure = failure + 1
        outputData.flush()
        
conn.close()
print("\nTotal processed : " + str(total))
print("\nTotal success : " + str(sucess))
print("\nTotal failed : " + str(failure))
print("\nExiting the process ")
exit(1)
