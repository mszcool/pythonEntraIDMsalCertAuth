import binascii
import os
import sys
import json
import logging
import requests
import msal
from azure.identity import DefaultAzureCredential
from azure.keyvault.certificates import CertificateClient
from azure.keyvault.secrets import SecretClient
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

# A few constants
AUTHORITY = "https://login.microsoftonline.com/{tenantIdOrName}"
GRAPH_API_SCOPE = "https://graph.microsoft.com/.default"
GRAPH_ENDPOINT = "https://graph.microsoft.com/v1.0/users"

#
# Read the certificate files
#
def getPrivateKey(privateKeyFileOrCertName, fromKeyVault=None):
    print ("reading certificate file: " + privateKeyFile)
    try:
        if fromKeyVault:
            # Read from Azure Key Vault, the file is now the name of the certificate in Key Vault
            credential = DefaultAzureCredential()
            secretClient = SecretClient(vault_url=fromKeyVault, credential=credential)
            certSecret = secretClient.get_secret(privateKeyFileOrCertName)
            privateKey = serialization.load_pem_private_key(certSecret.value.encode(), password=None)
            privateKeyStr = privateKey.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.TraditionalOpenSSL, serialization.NoEncryption())
            return privateKeyStr
        else:
            # Read from file
            with open(privateKeyFileOrCertName, 'r') as file:
                privateKey = file.read()
                return privateKey
    except Exception as e:
        print ("could not read certificate file: " + str(e))
        sys.exit(1)

#
# Read the public key certificate file
#
def getPublicKey(publicKeyFileOrCertName, fromKeyVault=None):
    print ("reading public key certificate file: " + publicKeyFile)
    try:
        if fromKeyVault:
            # Read from Azure Key Vault, the file is now the name of the certificate in Key Vault
            credential = DefaultAzureCredential()
            certClient = CertificateClient(vault_url=fromKeyVault, credential=credential)
            cert = certClient.get_certificate(publicKeyFileOrCertName)
            certBytes = bytes(cert.cer)
            convertCert = x509.load_der_x509_certificate(certBytes, default_backend())
            convertPemCert = convertCert.public_bytes(serialization.Encoding.PEM)
            certStr = convertPemCert.decode('utf-8')
            thumbprintStr = binascii.hexlify(cert.properties.x509_thumbprint).decode('utf-8')
            return certStr, thumbprintStr
        else:
            # Read from file
            with open(publicKeyFile, 'r') as file:
                publicKey = file.read()
                return publicKey, os.getenv("THUMBPRINT")
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
    if not tenantId or not clientId:
        print("Please provide TENANT_ID, CLIENT_ID environment variables!!")
        sys.exit(1)

    privateKeyPassword = os.getenv("PRIV_PASSWORD")
    
    keyVault = os.getenv("KEY_VAULT")
    if keyVault:
        privateKeyFile = os.getenv("KEY_VAULT_CERT_NAME")
        publicKeyFile = privateKeyFile
        if not keyVault or not privateKeyFile:
            print("Please provide KEY_VAULT and KEY_VAULT_CERT_NAME environment variables!!")
            sys.exit(1)
    else:
        thumbprint = os.getenv("THUMBPRINT")
        publicKeyFile = os.getenv("PUB_FILE")
        privateKeyFile = os.getenv("PRIV_FILE")
        if not thumbprint or not publicKeyFile or not privateKeyFile:
            print("Please provide THUMBPRINT, PUB_FILE, PRIV_FILE, and if password-protected also PRIV_PASSWORD environment variables!!")
            sys.exit(1)
    

    # Next, create the authority URL
    authority = AUTHORITY.format(tenantIdOrName=tenantId)

    # First, you need to read the certificate data
    publicKey, thumbprint = getPublicKey(publicKeyFile, keyVault)
    privateKey = getPrivateKey(privateKeyFile, keyVault)

    # First, acquire the token
    tokenString = acquireToken(authority, clientId, thumbprint, privateKey, privateKeyPassword)
    
    # Then call the token to retrieve users from Graph API
    callGraphApi(tokenString)

    # Done with everything
    print("done")