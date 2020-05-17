from base64 import b64encode
import re
import urllib
from uuid import UUID

import requests

import xml.etree.ElementTree as ET
from getpass import getpass

env=input("Enter the environment(SIT,QA,UAT or PROD) : ")
env = env.upper()
if env == "PROD":
    verify = input("\nYou entered PROD Y/N : ")
    if verify != "Y":
        print("Process is exiting as environment is not verified. \n")
        exit(1)

reason=input("Reason for resend message(INC, JIRA or ALM) : ")
url=input("Enter URL : ")
username=input("Enter username : ")
password=getpass.getpass(prompt='Password: ', stream=None)

print("Process is starting for "+env +"\n")            


def parse(ANSWER):
    print("\nANSWER ", ANSWER)
    try:
        tree = ET.fromstring(ANSWER)
        result = {}
        for item in tree.getiterator():
            result[item.tag] = item.text
        
        resp1 = result
        print("\nRESPONSE ", resp1)
    except Exception:
        print("\nException ", str("ERR"))
        return -1;    


# url = "http://vm0unbillca0012.twcable.com:8114/biller-order-translator-synch-service/services/solo/order"
url="https://cissolosynchncw-qa.corp.chartercom.com/biller-order-translator-synch-service/services/solo/order"
# userAndPass = b64encode(b"jesisolouser:jesisolouserpassword").decode("ascii")
userAndPass = b64encode(b"username:password").decode("ascii")
# headers={}
# headers[0] = { 'Authorization' : 'Basic %s' %  userAndPass }
headers = {'content-type': 'text/xml', 'Authorization' : 'Basic %s' % userAndPass}
body = '''<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:syn="http://www.charter.com/biller/order/translator/synch">
   <soapenv:Header>
      <syn:charterHeaderInputInfo>
         <clientIp>?</clientIp>
         <clientHostName>?</clientHostName>
         <clientCallingService>?</clientCallingService>
         <auditUser>?</auditUser>
         <transactionId>testasdfasfdfdasfdafadsfsdfasdf</transactionId>
         <!--Optional:-->
         <overrideCache>?</overrideCache>
      </syn:charterHeaderInputInfo>
   </soapenv:Header>
   <soapenv:Body>
      <syn:triggerBillerOrderTranslatorSynchRequest>
         <soloOrderId>112856738</soloOrderId>
      </syn:triggerBillerOrderTranslatorSynchRequest>
   </soapenv:Body>
</soapenv:Envelope>''' 

response =requests.post(url, data=body, headers=headers,verify=False)

print (response.content)
parse(response.content)

exit(1)