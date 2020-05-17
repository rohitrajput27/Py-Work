from base64 import b64encode
from getpass import getpass
import re
import urllib
import uuid
import json
import requests

import xml.etree.ElementTree as ET
from _overlapped import NULL

# reason = input("Reason for resend message(INC, JIRA or ALM number) : ")
# url = input("Query Account URL : ")
# username = input("Enter username : ")
# password = getpass("Enter password : ", stream=None)
# inputFile = input("Enter input file location(with file name) : ")    
# outputFile = input("Enter output file location(with fine name) : ")        

# reason = 'TEST'
# url = 'https://qa03-dsb-app.eng.rr.com'
# inputFile = 'D:/Mobile/test.csv'
# outputFile = 'D:/Mobile/test-out.csv'

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


def makeIt9Digit(accountNumber):
    if len(accountNumber) <9:
        accountNumber = accountNumber.zfill(9)
        return accountNumber
    else:
        return accountNumber

responseSuccessWhenTargetAccountDoesNotExists ='''<ASBMessage timestamp="2019-08-15T19:27:26.022" version="2.0" id="[GUID]">
   <Header>
      <Endpoint>
         <ID value="DSB"/>
      </Endpoint>
      <Context id="response"/>
      <PropertyList id="asb">
         <Property id="thread" value="F260E712-2738-95A5-C880-9F71AC9770DF"/>
      </PropertyList>
   </Header>
   <Body items="8">
      <Account status="ok">
         <ID ns="DSB" value="AC5D10F1-27B8-100E-0C86-5F424A81B316"/>
         <Account meta="operation;update">
            <ID ns="ESB" value="123445794"/>
            <Division id="CHTR"/>
            <Billing id="8245"/>
         </Account>
      </Account>
      <Account status="ok" operation="CREATE">
         <ID ns="DSB" value="B6803E99-F11E-EF3C-4DCC-7A765306E30C"/>
         <ID ns="ESB" value="123445794"/>
         <Type id="Residential"/>
         <Name value="Test Account"/>
         <Division id="CHTR"/>
         <Billing id="8245"/>
         <Status id="Active"/>
         <Address id="ServiceAddress">
            <Street value="1234 Main St"/>
            <City value="Houston"/>
            <State value="TX"/>
            <Zip value="10601"/>
         </Address>
         <PropertyList>
            <Property id="NoEmailReason" value="unknown"/>
         </PropertyList>
         <Audit creator="{Endpoint-Identifier}" timeCreated="190815192718267Z"/>
      </Account>
      <Customer status="ok" operation="update">
         <ID ns="DSB" value="01DEF8C4-3633-78A4-77E0-BE483E80F586"/>
         <Account meta="operation;update">
            <ID ns="ESB" value="123445794"/>
            <Division id="CHTR"/>
            <Billing id="8245"/>
            <ID ns="DSB" value="B6803E99-F11E-EF3C-4DCC-7A765306E30C"/>
         </Account>
         <Role id="PRIMARY"/>
      </Customer>
      <Customer status="ok" operation="update">
         <ID ns="DSB" value="F8D2A284-A549-66FB-7095-0D4EE4D20D96"/>
         <Account meta="operation;update">
            <ID ns="ESB" value="123445794"/>
            <Division id="CHTR"/>
            <Billing id="8245"/>
            <ID ns="DSB" value="B6803E99-F11E-EF3C-4DCC-7A765306E30C"/>
         </Account>
      </Customer>
      <Customer status="ok" operation="update">
         <ID ns="DSB" value="E509F0A7-A2F1-D4FD-8DFB-D8790945CCB7"/>
         <Account meta="operation;update">
            <ID ns="ESB" value="123445794"/>
            <Division id="CHTR"/>
            <Billing id="8245"/>
            <ID ns="DSB" value="B6803E99-F11E-EF3C-4DCC-7A765306E30C"/>
         </Account>
         <Role id="ADMIN"/>
      </Customer>
      <Customer status="ok" operation="update" txLocal="1">
         <ID ns="DSB" value="E509F0A7-A2F1-D4FD-8DFB-D8790945CCB7"/>
         <Role id="PRIMARY"/>
      </Customer>
      <Customer status="ok" operation="update" txLocal="1">
         <ID ns="DSB" value="01DEF8C4-3633-78A4-77E0-BE483E80F586"/>
         <Role id="ADMIN"/>
      </Customer>
      <Customer status="ok" operation="update">
         <ID ns="DSB" value="01DEF8C4-3633-78A4-77E0-BE483E80F586"/>
         <Role id="STANDARD"/>
      </Customer>
   </Body>
</ASBMessage>'''
   
   
   
responseSuccessWhenTargetAccountDoesExists='''<ASBMessage timestamp="2019-08-15T19:38:10.876" version="2.0" id="[GUID]">
   <Header>
      <Endpoint>
         <ID value="DSB"/>
      </Endpoint>
      <Context id="response"/>
      <PropertyList id="asb">
         <Property id="thread" value="F826CFF1-CE33-7289-EB97-C0FEC920D173"/>
      </PropertyList>
   </Header>
   <Body items="7">
      <Account status="ok">
         <ID ns="DSB" value="B6803E99-F11E-EF3C-4DCC-7A765306E30C"/>
         <Account meta="operation;update">
            <ID ns="ESB" value="123445792"/>
            <Division id="CHTR"/>
            <Billing id="8245"/>
         </Account>
      </Account>
      <Customer status="ok" operation="update">
         <ID ns="DSB" value="01DEF8C4-3633-78A4-77E0-BE483E80F586"/>
         <Account meta="operation;update">
            <ID ns="ESB" value="123445792"/>
            <Division id="CHTR"/>
            <Billing id="8245"/>
            <ID ns="DSB" value="AC5D10F1-27B8-100E-0C86-5F424A81B316"/>
         </Account>
         <Role id="PRIMARY"/>
      </Customer>
      <Customer status="ok" operation="update">
         <ID ns="DSB" value="F8D2A284-A549-66FB-7095-0D4EE4D20D96"/>
         <Account meta="operation;update">
            <ID ns="ESB" value="123445792"/>
            <Division id="CHTR"/>
            <Billing id="8245"/>
            <ID ns="DSB" value="AC5D10F1-27B8-100E-0C86-5F424A81B316"/>
         </Account>
      </Customer>
      <Customer status="ok" operation="update">
         <ID ns="DSB" value="E509F0A7-A2F1-D4FD-8DFB-D8790945CCB7"/>
         <Account meta="operation;update">
            <ID ns="ESB" value="123445792"/>
            <Division id="CHTR"/>
            <Billing id="8245"/>
            <ID ns="DSB" value="AC5D10F1-27B8-100E-0C86-5F424A81B316"/>
         </Account>
         <Role id="ADMIN"/>
      </Customer>
      <Customer status="ok" operation="update" txLocal="1">
         <ID ns="DSB" value="E509F0A7-A2F1-D4FD-8DFB-D8790945CCB7"/>
         <Role id="PRIMARY"/>
      </Customer>
      <Customer status="ok" operation="update" txLocal="1">
         <ID ns="DSB" value="01DEF8C4-3633-78A4-77E0-BE483E80F586"/>
         <Role id="ADMIN"/>
      </Customer>
      <Customer status="ok" operation="update">
         <ID ns="DSB" value="01DEF8C4-3633-78A4-77E0-BE483E80F586"/>
         <Role id="STANDARD"/>
      </Customer>
   </Body>
</ASBMessage>'''


responseSuccessWhenTargetAccountDoesExistsWithPI ='''<ASBMessage timestamp="2019-08-15T20:30:16.947" version="2.0" id="[GUID]">
   <Header>
      <Endpoint>
         <ID value="DSB"/>
      </Endpoint>
      <Context id="response"/>
      <PropertyList id="asb">
         <Property id="thread" value="13114A80-31C4-6D96-E62E-861A0019B600"/>
      </PropertyList>
   </Header>
   <Body items="4">
      <Account status="ok">
         <ID ns="DSB" value="620BAF6E-C9A4-C13C-4128-2026FC56D7EF"/>
         <Account meta="operation;update">
            <ID ns="ESB" value="123456793"/>
            <Division id="HOU"/>
            <Billing id="8011"/>
         </Account>
      </Account>
      <Customer status="ok" operation="update">
         <ID ns="DSB" value="15B12CC9-AB11-77A3-A195-E50EE1622EE5"/>
         <Account meta="operation;update">
            <ID ns="ESB" value="123456793"/>
            <Division id="HOU"/>
            <Billing id="8011"/>
            <ID ns="DSB" value="000BDE4C-F8E0-BFA3-A2F5-A2E542649951"/>
         </Account>
      </Customer>
      <Customer status="ok" operation="update">
         <ID ns="DSB" value="43357BE9-B1EC-08FC-D6D0-BAA6D747585D"/>
         <Account meta="operation;update">
            <ID ns="ESB" value="123456793"/>
            <Division id="HOU"/>
            <Billing id="8011"/>
            <ID ns="DSB" value="000BDE4C-F8E0-BFA3-A2F5-A2E542649951"/>
         </Account>
      </Customer>
      <Customer status="ok" operation="update">
         <ID ns="DSB" value="22B6CD00-661D-EAE3-40CE-1C92632AB7B8"/>
         <Account meta="operation;update">
            <ID ns="ESB" value="123456793"/>
            <Division id="HOU"/>
            <Billing id="8011"/>
            <ID ns="DSB" value="000BDE4C-F8E0-BFA3-A2F5-A2E542649951"/>
         </Account>
         <Role id="ADMIN"/>
      </Customer>
   </Body>
</ASBMessage>'''


failureResponse ='''<ASBMessage timestamp="2019-08-16T14:12:42.338" version="2.0" id="[GUID]">
   <Header>
      <Endpoint>
         <ID value="DSB"/>
      </Endpoint>
      <Context id="response"/>
      <Itinerary/>
      <BusinessProcess>
         <ID value="IdentitiesTransfer"/>
      </BusinessProcess>
      <PropertyList id="asb">
         <Property id="thread" value="F37F2F89-1DAA-9F1C-3AF6-18DFAB767009"/>
         <Property id="ExitStatus.CallPersistor" value="ERROR"/>
      </PropertyList>
      <Status id="ERROR"/>
   </Header>
   <Body>
      <Account status="ERROR">
         <ID ns="DSB" value="620BAF6E-C9A4-C13C-4128-2026FC56D7EA"/>
         <Account meta="operation;update">
            <ID ns="ESB" value="123456793"/>
            <Division id="HOU"/>
            <Billing id="8011"/>
         </Account>
         <Exception>
            <ID ns="TWC" value="DataNotFound"/>
            <Message value="No matching Data!"/>
            <Details>No Accounts Found!</Details>
         </Exception>
      </Account>
   </Body>
</ASBMessage>'''


partialSuccess ='''<ASBMessage timestamp="2019-09-03T14:49:37.244" version="2.0" id="[GUID]">
   <Header>
      <Endpoint>
         <ID value="DSB"/>
      </Endpoint>
      <Context id="response"/>
      <PropertyList id="asb">
         <Property id="thread" value="29B51FF4-0B21-9D61-5302-68A9475DC770"/>
      </PropertyList>
      <Status id="error"/>
   </Header>
   <Body items="8">
      <Account status="ok">
         <ID ns="DSB" value="D8E6F7C4-2616-8BD6-C4F9-05985C8616BB"/>
         <Account meta="operation;update">
            <ID ns="ESB" value="123445797"/>
            <Division id="CHTR"/>
            <Billing id="8245"/>
         </Account>
      </Account>
      <Customer status="ok" operation="update">
         <ID ns="DSB" value="D62E9F5B-E769-1217-F096-EE31AABDD680"/>
         <Account meta="operation;update">
            <ID ns="ESB" value="123445797"/>
            <Division id="CHTR"/>
            <Billing id="8245"/>
            <ID ns="DSB" value="9537403E-A649-074A-9583-54A29252C95A"/>
         </Account>
      </Customer>
      <Customer status="ok" operation="update">
         <ID ns="DSB" value="1AB6A654-4067-1C93-2CB7-695A1025BD30"/>
         <Account meta="operation;update">
            <ID ns="ESB" value="123445797"/>
            <Division id="CHTR"/>
            <Billing id="8245"/>
            <ID ns="DSB" value="9537403E-A649-074A-9583-54A29252C95A"/>
         </Account>
      </Customer>
      <Customer status="ok" operation="update">
         <ID ns="DSB" value="8E14DEC2-1FCC-B252-5101-B3DA5B5FD053"/>
         <Account meta="operation;update">
            <ID ns="ESB" value="123445797"/>
            <Division id="CHTR"/>
            <Billing id="8245"/>
            <ID ns="DSB" value="9537403E-A649-074A-9583-54A29252C95A"/>
         </Account>
      </Customer>
      <Customer status="ok" operation="update">
         <ID ns="DSB" value="0BAC2F18-7821-E259-E8B7-BC5A7B79A4E2"/>
         <Account meta="operation;update">
            <ID ns="ESB" value="123445797"/>
            <Division id="CHTR"/>
            <Billing id="8245"/>
            <ID ns="DSB" value="9537403E-A649-074A-9583-54A29252C95A"/>
         </Account>
      </Customer>
      <Customer status="ok" operation="update">
         <ID ns="DSB" value="A348DA5E-5C57-926F-3FA8-94E96514C69E"/>
         <Account meta="operation;update">
            <ID ns="ESB" value="123445797"/>
            <Division id="CHTR"/>
            <Billing id="8245"/>
            <ID ns="DSB" value="9537403E-A649-074A-9583-54A29252C95A"/>
         </Account>
      </Customer>
      <Customer status="ok" operation="update">
         <ID ns="DSB" value="0F96807F-BB83-B619-E918-4F24C444E367"/>
         <Account meta="operation;update">
            <ID ns="ESB" value="123445797"/>
            <Division id="CHTR"/>
            <Billing id="8245"/>
            <ID ns="DSB" value="9537403E-A649-074A-9583-54A29252C95A"/>
         </Account>
      </Customer>
      <Customer status="error" operation="update">
         <ID ns="DSB" value="F34E07C6-7A73-E732-9132-BF519F879D23"/>
         <Account meta="operation;update">
            <ID ns="ESB" value="123445797"/>
            <Division id="CHTR"/>
            <Billing id="8245"/>
         </Account>
         <Role id="ADMIN"/>
         <Exception>
            <ID ns="TWC" value="IdentityCountExceeded"/>
            <Message value="Identity Count Exceeded MAX Identities Allowed on this Account!"/>
            <Details>Active and Unverified Identity Count Exceeded Max Identities Allowed in Account!</Details>
         </Exception>
      </Customer>
   </Body>
</ASBMessage>'''


allFailureResponse ='''<ASBMessage timestamp="2019-09-03T14:49:37.244" version="2.0" id="[GUID]">
   <Header>
      <Endpoint>
         <ID value="DSB"/>
      </Endpoint>
      <Context id="response"/>
      <PropertyList id="asb">
         <Property id="thread" value="29B51FF4-0B21-9D61-5302-68A9475DC770"/>
      </PropertyList>
      <Status id="error"/>
   </Header>
   <Body items="8">
      <Account status="ok">
         <ID ns="DSB" value="D8E6F7C4-2616-8BD6-C4F9-05985C8616BB"/>
         <Account meta="operation;update">
            <ID ns="ESB" value="123445797"/>
            <Division id="CHTR"/>
            <Billing id="8245"/>
         </Account>
      </Account>
      <Customer status="error" operation="update">
         <ID ns="DSB" value="D62E9F5B-E769-1217-F096-EE31AABDD680"/>
         <Account meta="operation;update">
            <ID ns="ESB" value="123445797"/>
            <Division id="CHTR"/>
            <Billing id="8245"/>
            <ID ns="DSB" value="9537403E-A649-074A-9583-54A29252C95A"/>
         </Account>
      </Customer>
      <Customer status="error" operation="update">
         <ID ns="DSB" value="1AB6A654-4067-1C93-2CB7-695A1025BD30"/>
         <Account meta="operation;update">
            <ID ns="ESB" value="123445797"/>
            <Division id="CHTR"/>
            <Billing id="8245"/>
            <ID ns="DSB" value="9537403E-A649-074A-9583-54A29252C95A"/>
         </Account>
      </Customer>
      <Customer status="error" operation="update">
         <ID ns="DSB" value="8E14DEC2-1FCC-B252-5101-B3DA5B5FD053"/>
         <Account meta="operation;update">
            <ID ns="ESB" value="123445797"/>
            <Division id="CHTR"/>
            <Billing id="8245"/>
            <ID ns="DSB" value="9537403E-A649-074A-9583-54A29252C95A"/>
         </Account>
      </Customer>
      <Customer status="error" operation="update">
         <ID ns="DSB" value="0BAC2F18-7821-E259-E8B7-BC5A7B79A4E2"/>
         <Account meta="operation;update">
            <ID ns="ESB" value="123445797"/>
            <Division id="CHTR"/>
            <Billing id="8245"/>
            <ID ns="DSB" value="9537403E-A649-074A-9583-54A29252C95A"/>
         </Account>
      </Customer>
      <Customer status="error" operation="update">
         <ID ns="DSB" value="A348DA5E-5C57-926F-3FA8-94E96514C69E"/>
         <Account meta="operation;update">
            <ID ns="ESB" value="123445797"/>
            <Division id="CHTR"/>
            <Billing id="8245"/>
            <ID ns="DSB" value="9537403E-A649-074A-9583-54A29252C95A"/>
         </Account>
      </Customer>
      <Customer status="error" operation="update">
         <ID ns="DSB" value="0F96807F-BB83-B619-E918-4F24C444E367"/>
         <Account meta="operation;update">
            <ID ns="ESB" value="123445797"/>
            <Division id="CHTR"/>
            <Billing id="8245"/>
            <ID ns="DSB" value="9537403E-A649-074A-9583-54A29252C95A"/>
         </Account>
      </Customer>
      <Customer status="error" operation="update">
         <ID ns="DSB" value="F34E07C6-7A73-E732-9132-BF519F879D23"/>
         <Account meta="operation;update">
            <ID ns="ESB" value="123445797"/>
            <Division id="CHTR"/>
            <Billing id="8245"/>
         </Account>
         <Role id="ADMIN"/>
         <Exception>
            <ID ns="TWC" value="IdentityCountExceeded"/>
            <Message value="Identity Count Exceeded MAX Identities Allowed on this Account!"/>
            <Details>Active and Unverified Identity Count Exceeded Max Identities Allowed in Account!</Details>
         </Exception>
      </Customer>
   </Body>
</ASBMessage>'''


if parseTransferIdentity(ANSWER=partialSuccess)[0] =='SUCCESS':
    print('partialSuccess')
    print(parseTransferIdentity(ANSWER=partialSuccess))
    print(True)
else:
    print(parseTransferIdentity(ANSWER=partialSuccess))
    print(False)


if parseTransferIdentity(ANSWER=allFailureResponse)[0] =='ERROR':
    print('allFailureResponse')
    print(parseTransferIdentity(ANSWER=allFailureResponse))
    print(True)
else:
    print(parseTransferIdentity(ANSWER=allFailureResponse))
    print(False)
    

if parseTransferIdentity(ANSWER=failureResponse)[0] =='ERROR':
    print('failureResponse')
    print(parseTransferIdentity(ANSWER=failureResponse))
    print(True)
else:
    print(parseTransferIdentity(ANSWER=failureResponse))
    print(False)
    
    
if parseTransferIdentity(ANSWER=responseSuccessWhenTargetAccountDoesExists)[0] =='SUCCESS':
    print('responseSuccessWhenTargetAccountDoesExists')
    print(parseTransferIdentity(ANSWER=responseSuccessWhenTargetAccountDoesExists))
    print(True)
else:
    print(parseTransferIdentity(ANSWER=responseSuccessWhenTargetAccountDoesExists))
    print(False)
    
    
if parseTransferIdentity(ANSWER=responseSuccessWhenTargetAccountDoesExistsWithPI)[0] =='SUCCESS':
    print('responseSuccessWhenTargetAccountDoesExistsWithPI')
    print(parseTransferIdentity(ANSWER=responseSuccessWhenTargetAccountDoesExistsWithPI))
    print(True)
else:
    print(parseTransferIdentity(ANSWER=responseSuccessWhenTargetAccountDoesExistsWithPI))
    print(False)
    
    
    
    
if parseTransferIdentity(ANSWER=responseSuccessWhenTargetAccountDoesNotExists)[0] =='SUCCESS':
    print('responseSuccessWhenTargetAccountDoesNotExists')
    print(parseTransferIdentity(ANSWER=responseSuccessWhenTargetAccountDoesNotExists))
    print(True)
else:
    print(parseTransferIdentity(ANSWER=responseSuccessWhenTargetAccountDoesNotExists))
    print(False)
    

print(makeIt9Digit('2345'))
print(makeIt9Digit('2345asdgtasdfasdf'))
print(makeIt9Digit('123456789'))
print(makeIt9Digit('1'))
print(makeIt9Digit('12'))
print(makeIt9Digit('123'))
print(makeIt9Digit('1234'))
print(makeIt9Digit('12345'))
print(makeIt9Digit('123456'))
print(makeIt9Digit('1234567'))
print(makeIt9Digit('12345678'))