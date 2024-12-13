import base64
import os
import pickle
from email.mime.text import MIMEText
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from requests import HTTPError

class GmailSender:
    SCOPES = [
        "https://www.googleapis.com/auth/gmail.send"
    ]

    def __init__(self):
        creds = None
        if os.path.exists("token.pickle"):
            with open("token.pickle", "rb") as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', GmailSender.SCOPES)
                creds = flow.run_local_server(port=0)

            with open("token.pickle", "wb") as token:
                pickle.dump(creds, token)

        self.service = build('gmail', 'v1', credentials=creds)
        
    
    def send(self, dest: str, topic: str, msg: str):

        message = MIMEText(msg)
        message['to'] = dest
        message['subject'] = topic
        create_message = {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}
        try:
            message = (self.service.users().messages().send(userId="me", body=create_message).execute())
            print(F'sent message to {message} Message Id: {message["id"]}')
        except HTTPError as error:
            print(F'An error occurred: {error}')
            message = None


gmail = GmailSender()
gmail.send('nicolas.monsel@gmx.fr', "test authenticated", "test message")