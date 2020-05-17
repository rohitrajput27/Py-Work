import cx_Oracle
import time
import os
import platform
from getpass import getpass

os.chdir(os.path.dirname(__file__))
LOCATION = os.getcwd() + "/dll"
print("ARCH:", platform.architecture())
# print("FILES AT LOCATION:")
# for name in os.listdir(LOCATION):
#     print(name)
os.environ["PATH"] = LOCATION + ";" + os.environ["PATH"]

sql = '''   select aa.account_id,cc.ucan from chtr.t_account aa
            inner join chtr.t_customer_account ca on ca.account_id  = aa.account_id 
            inner join chtr.t_customer cc on cc.customer_id = ca.customer_id 
            where 
            aa.record_stat ='A'
            and
            ca.record_stat ='A'
            and
            cc.record_stat ='A'
            and
            aa.account_id   =:accountId'''


inputFile = input("Enter input file location(with file name) : ")  
outputFile = input("Enter output file location(with file name) : ")  
# inputFile = r"C:\Users\rrajput\Desktop\SoloAccountID\soloAccountIdsToSelect-tst.txt"
# outputFile = r"C:\Users\rrajput\Desktop\SoloAccountID\soloAccountIdsToSelect-tst-out.csv"

dbhost= input("Enter DB host : ")
dbport= input("Enter DB port : ")
bdServiceName= input("Enter DB service name : ")
dbUserName=input("Enter DB user name : ")
dbPassword = getpass("Enter DB password : ", stream=None)  

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

    
print("Preparing the connection")
dsn_tns = cx_Oracle.makedsn(dbhost, dbport, service_name=bdServiceName)  # if needed, place an 'r' before any parameter in order to address special characters such as '\'.
conn = cx_Oracle.connect(user=dbUserName, password=dbPassword, dsn=dsn_tns)  # if needed, place an 'r' before any parameter in order to address special characters such as '\'. For example, if your user name contains '\', you'll need to place 'r' before the user name: user=r'User Name'

c = conn.cursor()
print("Starting the process")
with open(inputFile, "r") as inputData, open(outputFile, "w+") as outputData:
    outputData.write("SoloAccountID,UCAN\n")
    for line in inputData:
#         print(line)
        line = line.replace('\n', '').replace('\r', '')
        total = total + 1
        flushCounter = flushCounter + 1
        try:
            c.execute(sql, accountId=line)
            row = c.fetchone()
            if row is None:
                failure = failure + 1
#                 print (line, '-', row)  # this only shows the first two columns. To add an additional column you'll need to add , '-', row[2], etc.
                outputData.write(line + ",\n")
            else:
                sucess = sucess + 1
#                 print (line, '-', row[1])  # this only shows the first two columns. To add an additional column you'll need to add , '-', row[2], etc.
                outputData.write(line + "," + str(row[1]) + "\n")
        except Exception as exce:
            print(exce)
            failure = failure + 1
            outputData.write(line + ",\n")
        
        if flushCounter == 10:
            printStatus()
            outputData.flush()
            flushCounter = 0
        
conn.close()
printStatus()
print("\nExiting the process ")
exit(1)
