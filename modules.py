from sqlite3 import Error
import random, string, time, urllib.request, urllib.error, json
from db import get_db_connection

def generate_token(length=32):
    """Generate a random token string"""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def validate_token(token, tokens_list):
    """Validate a token and return its scopes if valid"""
    current_time = int(time.time())
    
    for t in tokens_list:
        if t['token'] == token:
            # Check if token has expired
            if t['expired_at'] and current_time > t['expired_at']:
                return False, []
            
            # Token is valid, return scopes
            scopes = t['scope'].split(':')
            return True, scopes
    
    return False, []

def proxy_request(url, data, method='POST'):
    """Proxy a request to the target URL and return the response"""
    try:
        headers = {'Content-Type': 'application/json'}
        
        # Remove token from data before forwarding
        if 'token' in data:
            data = {k: v for k, v in data.items() if k != 'token'}
        
        data_json = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(url, data=data_json, headers=headers, method=method)
        
        with urllib.request.urlopen(req) as response:
            response_data = response.read().decode('utf-8')
            return json.loads(response_data)
    
    except urllib.error.URLError as e:
        return {"error": f"Failed to connect to LLM server: {str(e)}"}
    except json.JSONDecodeError:
        return {"error": "Failed to parse response from LLM server"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

def log_request(token, endpoint, method, status_code):
    """Log request logs to the database"""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            timestamp = int(time.time())
            cursor.execute('''
                INSERT INTO usage_logs (timestamp, token, endpoint, method, status_code)
                VALUES (?, ?, ?, ?, ?)
            ''', (timestamp, token, endpoint, method, status_code))
            conn.commit()
        except Error as e:
            print(f"Error logging request: {e}")
        finally:
            conn.close()
