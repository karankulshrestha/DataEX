
# DataEX

A project for extracting structure information about the entities from the specific column of the excel sheet with automation using llm.



# Google Service Account Configuration

This configuration JSON is used to authenticate a Google service account to access Google APIs, specifically with permissions to manage Google Sheets and Google Drive. Ensure that sensitive fields like `private_key` are securely stored and never exposed publicly.

## Required Scopes

To grant the service account access to Google Sheets and Google Drive, include the following scopes:

```json
"scope": [
  "https://www.googleapis.com/auth/spreadsheets",  // Allows full access to Google Sheets.
  "https://www.googleapis.com/auth/drive"          // Allows full access to Google Drive.
]

```
## Google Credentials.json

This configuration JSON is used to authenticate a Google service account for accessing Google APIs. Ensure that sensitive fields like `private_key` are securely stored and never exposed publicly, **placed credentials.json in the same folder.**

```json
{
  "type": "service_account",
  "project_id": "your-project-id",  // The Google Cloud project ID associated with this service account.
  
  "private_key_id": "dummy-private-key-id",  // The private key ID associated with the service account key.
  
  "private_key": "-----BEGIN PRIVATE KEY-----\nDUMMY_PRIVATE_KEY\n-----END PRIVATE KEY-----\n",  
  // The private key for the service account. **Do not share this key publicly**.
  
  "client_email": "dummy-email@your-project-id.iam.gserviceaccount.com",  
  // The service account email address.
  
  "client_id": "dummy-client-id",  // The client ID associated with the service account.
  
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",  
  // The OAuth 2.0 authorization endpoint for Google APIs.
  
  "token_uri": "https://oauth2.googleapis.com/token",  
  // The token endpoint used to retrieve access tokens.
  
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",  
  // The URL to Google’s public certs for token verification.
  
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/dummy-email%40your-project-id.iam.gserviceaccount.com",  
  // The URL to the service account's public cert for verification.
  
  "universe_domain": "googleapis.com"  
  // The domain for Google APIs.
}
```
## Enviroment Variables

To run this project, you will need to set up the following environment variables in your environment or in an `.env` file. **Ensure you keep these variables secure and never expose them publicly.**

## Required Environment Variables

- `TAVILY_API_KEY`: The API key for accessing the Tavily API.
- `OPENAI_API_KEY`: The API key for accessing the OpenAI API.
- `SERP_API_KEY`: The API key for the SERP API.
- `SCARPI_API_KEY`: The API key for the Scarpi API.
## Installation

Install DataEX

```bash
    git clone https://github.com/karankulshrestha/DataEX
    cd DataEX
    pip install -r requirements.txt
    streamlit run app.py
```



    