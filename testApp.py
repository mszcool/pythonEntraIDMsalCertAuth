import os
import sys
import json
import logging
import requests
import msal

# A few constants
AUTHORITY = "https://login.microsoftonline.com/{tenantIdOrName}"
GRAPH_API_SCOPE = "https://graph.microsoft.com/.default"
GRAPH_ENDPOINT = "https://graph.microsoft.com/v1.0/users"

#
# Read the certificate files
#
def getPrivateKey(privateKeyFile):
    print ("reading certificate file: " + privateKeyFile)
    try:
        with open(privateKeyFile, 'r') as file:
            privateKey = file.read()
            return privateKey
    except Exception as e:
        print ("could not read certificate file: " + str(e))
        sys.exit(1)

#
# Read the public key certificate file
#
def getPublicKey(publicKeyFile):
    print ("reading public key certificate file: " + publicKeyFile)
    try:
        with open(publicKeyFile, 'r') as file:
            publicKey = file.read()
            return publicKey
    except Exception as e:
        print ("could not read public key certificate file: " + str(e))
        sys.exit(1)

#
# This is a simple sample for using certificate to authenticate against an App Registration in Microsoft Entra ID
#
def acquireToken(authority, clientId, thumbprint, privateKey,privateKeyPassword):
    print ("acquiring token with certificate...")
    app = msal.ConfidentialClientApplication(
        clientId,
        authority=authority,
        client_credential={
            "thumbprint": thumbprint.replace(":", "").lower(),
            "private_key": privateKey,
            "public_certificate": publicKey,
            "passphrase": privateKeyPassword,
        }
    )

    result = app.acquire_token_for_client([GRAPH_API_SCOPE])
    
    if "access_token" in result:
        print ("token acquired...")
        return result['access_token']
    else:
        print ("could not acquire token")
        print (result.get("error"))
        print (result.get("error_description"))
        print (result.get("correlation_id"))
        sys.exit(1)

#
# Calls the Microsoft Graph API with a previously acquired token
#
def callGraphApi(tokenString):
    print ("calling Graph API with token...")
    graph_data = requests.get(
        GRAPH_ENDPOINT,
        headers={'Authorization': 'Bearer ' + tokenString}, ).json()
    print("Graph API call result: ")
    print(json.dumps(graph_data, indent=2))

#
# Main Application flow
#
if __name__ == "__main__":

    # First, we need the authority, the client ID, the private key file, and the password for the private key file
    tenantId = os.getenv("TENANT_ID")
    clientId = os.getenv("CLIENT_ID")
    thumbprint = os.getenv("THUMBPRINT")
    publicKeyFile = os.getenv("PUB_FILE")
    privateKeyFile = os.getenv("PRIV_FILE")
    privateKeyPassword = os.getenv("PRIV_PASSWORD")

    if not tenantId or not clientId or not thumbprint or not privateKeyFile:
        print("Please provide TENANT_ID, CLIENT_ID, THUMBPRINT, PK_FILE, and PK_PASSWORD environment variables")
        sys.exit(1)

    # Next, create the authority URL
    authority = AUTHORITY.format(tenantIdOrName=tenantId)

    # First, you need to read the certificate data
    publicKey = getPublicKey(publicKeyFile)
    privateKey = getPrivateKey(privateKeyFile)

    # First, acquire the token
    tokenString = acquireToken(authority, clientId, thumbprint, privateKey, privateKeyPassword)
    
    # Then call the token to retrieve users from Graph API
    callGraphApi(tokenString)

    # Done with everything
    print("done")