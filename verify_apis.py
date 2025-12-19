import urllib.request
import urllib.parse
import json
import ssl
import sys

# Constants
BASE_URL = "http://localhost:8000/api/v1"
USERNAME = "federico@zorgnotto.it"
PASSWORD = "gaga"

def login():
    print(f"[*] Logging in as {USERNAME}...")
    url = f"{BASE_URL}/auth/login"
    data = urllib.parse.urlencode({'username': USERNAME, 'password': PASSWORD}).encode('utf-8')
    try:
        req = urllib.request.Request(url, data=data, method='POST')
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                body = json.loads(response.read().decode())
                print("[+] Login Successful")
                return body['access_token']
            else:
                print(f"[-] Login Failed: {response.status}")
                return None
    except Exception as e:
        print(f"[-] Login Exception: {e}")
        return None

def test_endpoint(token, method, endpoint, data=None):
    print(f"\n[*] Testing {method} {endpoint}...")
    url = f"{BASE_URL}{endpoint}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    encoded_data = None
    if data:
        encoded_data = json.dumps(data).encode('utf-8')

    try:
        req = urllib.request.Request(url, data=encoded_data, headers=headers, method=method)
        with urllib.request.urlopen(req) as response:
            body = response.read().decode()
            print(f"[+] Success ({response.status}): {body[:100]}...") # Truncate output
            return True
    except urllib.error.HTTPError as e:
        print(f"[-] HTTP Error {e.code}: {e.read().decode()[:200]}...")
        return False
    except Exception as e:
        print(f"[-] Exception: {e}")
        return False

def main():
    token = login()
    if not token:
        sys.exit(1)

    # 1. Test User Info (Check email status as /me doesn't exist)
    test_endpoint(token, "GET", "/users/email_status")

    # 2. Test Cities (Public check? usually dictionaries are public or protected)
    # Assuming standard standard paginated response structure
    test_endpoint(token, "GET", "/citta/?limit=5")

    # 3. Test Schools
    test_endpoint(token, "GET", "/school/?limit=5")
    
    # 4. Test Create School (Requires valid Citta ID usually)
    # Check if we can list citta first to get an ID
    # This is a bit complex for a simple check, skipping creation unless listing works.

    # 5. Test Indirizzi
    test_endpoint(token, "GET", "/indirizzi/?limit=5")

    # 6. Test Materie
    test_endpoint(token, "GET", "/materie/?limit=5")

if __name__ == "__main__":
    main()
