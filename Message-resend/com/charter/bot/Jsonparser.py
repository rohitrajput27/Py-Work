import json

responseData = json.loads("""
{
    "errorResponse": {
        "source": "REQUEST",
       
        "errorCode": "400"
    },
    "transaction-Id": "2463ae89-0705-49cd-8613-c13ff42e63e5",
    "TxRoot": "2463ae89-0705-49cd-8613-c13ff42e63e5"
}
""")



errorMessage=''

if "errorResponse" in responseData:
    errorResponse  = responseData["errorResponse"]
    print(errorResponse)
    if errorResponse is not None and "errorMessage" in errorResponse:
        errorMessage = errorResponse["errorMessage"]
        print(errorMessage)


print(errorMessage)