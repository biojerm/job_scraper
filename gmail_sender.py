# This code is mostly from the gmail quickstart
# https://developers.google.com/gmail/api/quickstart/python
from __future__ import print_function
import httplib2
from urllib.error import HTTPError
import os

from email.mime.text import MIMEText
import base64

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

import private  # private.py has dictionary with emails

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/gmail-python-quickstart.json

dir_path = os.path.dirname(os.path.abspath(__file__))

SCOPES = 'https://www.googleapis.com/auth/gmail.send'
CLIENT_SECRET_FILE = os.path.join(dir_path, 'client_secret_2.json')
APPLICATION_NAME = 'Gmail API Python Quickstart'


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'gmail-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else:  # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials


def create_message(sender, to, subject, message_text):
    """Create a message for an email.

    Args:
        sender: Email address of the sender.
        to: Email address of the receiver.
        subject: The subject of the email message.
        message_text: The text of the email message.

    Returns:
        An object containing a base64url encoded email object.
    """
    message = MIMEText(message_text, 'html')
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    # return {'raw': base64.urlsafe_b64encode(message.as_string())}
    return {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}


def send_message(service, user_id, message):
    """Send an email message.

    Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    message: Message to be sent.

    Returns:
    Sent Message.
  """
    try:
        message = (service.users().messages().send(userId=user_id, body=message)
                   .execute())
        print('Message Id: %s' % message['id'])
        return message
    except HTTPError as error:
        print('An error occurred: %s' % error)


def create_and_send_message(sender, reciever, subject, message):
    email_message = create_message(sender, reciever, subject, message)
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('gmail', 'v1', http=http)

    send_message(service, 'me', email_message)

if __name__ == '__main__':
    message = create_message(private.email['J'], private.email['J'], 'test subject', 'test body')
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('gmail', 'v1', http=http)
    send_message(service, 'me', message)
