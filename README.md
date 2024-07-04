# Simple example calling Graph API with MSAL for Python

This example is a simple example which acquires a token using a certificate private key against
Microsoft Entra ID. It subsequently executes a simple request to Microsoft Graph API. The steps
required for executing this are the following, below.

**Important note:** It is always better to use managed identities whenever possible for accessing
services and APIs. This example was created for a use case that leverages a different security token services
than EntraID that lives outside of Azure, and therefore cannot use managed identities.

## Create a certificate

The certificate for testing purposes can easily be created using the openssl command line tool.

```bash
# Generate a private key
openssl genrsa -out server.pem 2048
# Generate a certificate request from the private key
openssl req -new -key server.pem -out server.csr
# Generate a self-signed certificate from the certificate request
openssl x509 -req -days 365 -in server.csr -signkey server.pem -out server.crt
# Export the thumbprint of the certificate
openssl x509 -in server.crt -fingerprint -noout
``` 

## Create an app registration, create a certificate credential, upload the private key certificate file

Next, in Microsoft Entra ID navigate to the `App Registrations` portal section, and create a new app registration.
In the app registration, navigate to the `Certificates & secrets` section, and upload the private key certificate file.
Ensure the app registration has the API permission `User.Read` and `User.ReadBasic.All` for the Microsoft Graph API.
You will need to grant admin consent for the permissions after you have assigned them to the app.

Finally, copy the following values for later use from the overview section:

* The Directory (tenant) ID
* The Application (client) ID

## Configure environment variables to run the application

From all of the above, you now need to set the following environment variables before running this example:

* TENANT_ID="<previously copied directory tenant ID>"
* CLIENT_ID="<previously copied application client ID>"
* THUMBPRINT="<thumbprint, the code removes the ':' from 'xx:xx:xx:xx...' if you do not do it>"
* PUB_FILE="server.crt"
* PRIV_FILE="<path to the *.pem file, i.e., server.pem>"
* PRIV_PASSWORD="<if the private key is password protected, enter the password here>"

## Run the application, debug, observe

Once you have set the environment variables, you can run the application using the following command:

```bash
python testApp.py
```

It should output a JSON document with the users of the directory if everything was setup, correctly!
