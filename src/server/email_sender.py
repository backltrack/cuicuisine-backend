import smtplib
import ssl
from email.mime.text import MIMEText
from os import getenv


class GmailSender:
    SMTP_HOST = "smtp.gmail.com"
    SMTP_PORT = 465

    def __init__(self):
        self.address = getenv("GMAIL_ADDRESS")
        self.app_password = getenv("GMAIL_APP_PASSWORD")

    def send(self, dest: str, topic: str, msg: str):
        message = MIMEText(msg)
        message["to"] = dest
        message["from"] = self.address
        message["subject"] = topic

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(self.SMTP_HOST, self.SMTP_PORT, context=context) as server:
            server.login(self.address, self.app_password)
            server.sendmail(self.address, dest, message.as_string())
