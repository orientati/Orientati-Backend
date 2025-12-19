
import urllib.request
import urllib.parse
import json
import time
import ssl

# Hack to ignore SSL if generic (though localhost usually http)
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

GATEWAY_URL = "http://localhost:8000"
KMS_URL = "http://localhost:8001"
USERS_URL = "http://localhost:8002"
SCHOOLS_URL = "http://localhost:8003"
EMAIL_URL = "http://localhost:8004"

def log(msg, status="INFO"):
    print(f"[{status}] {msg}")

def truncate(text, length=500):
    if len(text) > length:
        return text[:length] + "..."
    return text

def do_request(url, method="GET", data=None, headers={}, json_body=False):
    try:
        final_data = None
        if data:
            if json_body:
                final_data = json.dumps(data).encode('utf-8')
                headers['Content-Type'] = 'application/json'
            else:
                final_data = urllib.parse.urlencode(data).encode('utf-8')
        
        req = urllib.request.Request(url, data=final_data, headers=headers, method=method)
        with urllib.request.urlopen(req, context=ctx) as response:
            return response.status, response.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8')
    except Exception as e:
        return 0, str(e)

def check_service(url, name):
    status, _ = do_request(f"{url}/docs")
    if status == 200:
        log(f"{name} is UP ({url})", "PASS")
    else:
        log(f"{name} returned {status}", "FAIL")

def test_auth_flow():
    log("Testing Auth Flow via Gateway...")
    email = f"test_{int(time.time())}@example.com"
    password = "password123"
    
    # 1. Register
    payload = {
        "name": "Test",
        "surname": "User",
        "email": email,
        "password": password
    }
    status, body = do_request(f"{GATEWAY_URL}/api/v1/auth/register", method="POST", data=payload, json_body=True)
    
    if status in [200, 201, 202]:
        log(f"Registration successful: {status}", "PASS")
    else:
        log(f"Registration failed: {status} - {truncate(body)}", "FAIL")
        return None

    # 2. Login
    login_data = {
        "username": email,
        "password": password
    }
    # OAuth2 specifies form data
    status, body = do_request(f"{GATEWAY_URL}/api/v1/auth/login", method="POST", data=login_data, json_body=False)
    
    if status == 200:
        token = json.loads(body).get("access_token")
        log(f"Login successful. Token: {token[:10]}...", "PASS")
        return token
    else:
        log(f"Login failed: {status} - {truncate(body)}", "FAIL")
        return None

def test_schools_flow(token):
    log("Testing Schools Flow via Gateway...")
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    status, body = do_request(f"{GATEWAY_URL}/api/v1/schools/", headers=headers)
    if status == 200:
        try:
            data = json.loads(body)
            scuole = data.get('scuole', [])
            log(f"List Schools successful: {len(scuole)} schools found", "PASS")
        except:
             log(f"List Schools successful but parsing failed", "PASS")
    else:
        log(f"List Schools failed: {status} - {truncate(body)}", "FAIL")

def main():
    log("Starting System Check...")
    
    # Check services
    check_service(GATEWAY_URL, "Gateway")
    check_service(KMS_URL, "KMS Service")
    check_service(USERS_URL, "Users Service")
    check_service(SCHOOLS_URL, "Schools Service")
    check_service(EMAIL_URL, "Email Service")
    
    token = test_auth_flow()
    
    if token:
        test_schools_flow(token)
    else:
        log("Skipping authenticated tests due to login failure", "WARN")

if __name__ == "__main__":
    main()
