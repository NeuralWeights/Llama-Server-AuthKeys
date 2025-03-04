import sqlite3, datetime, time, os
from sqlite3 import Error
from config import config

DB_FILE = config['DB']['db_name']

def get_db_connection():
    """Create a database connection"""
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
    except Error as e:
        print(f"Database error: {e}")
    return conn

def init_db():
    """Initialize the database with required tables"""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tokens (
                    token TEXT PRIMARY KEY,
                    scope TEXT NOT NULL,
                    created_at INTEGER NOT NULL,
                    expired_at INTEGER
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS usage_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    token TEXT,
                    endpoint TEXT NOT NULL,
                    method TEXT NOT NULL,
                    status_code INTEGER NOT NULL
                )
            ''')

            conn.commit()
        except Error as e:
            print(f"Database initialization error: {e}")
        finally:
            conn.close()



def log_request(token, endpoint, method, status_code):
    """Log request usage_logs to the database"""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()  # ISO 8601 format
            cursor.execute('''
                INSERT INTO usage_logs (timestamp, token, endpoint, method, status_code)
                VALUES (?, ?, ?, ?, ?)
            ''', (timestamp, token, endpoint, method, status_code))
            conn.commit()
        except Error as e:
            print(f"Error logging request: {e}")
        finally:
            conn.close()


def log_request(token, endpoint, method, status_code):
    """Log request usage_logs to the database"""
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


def save_token(token, scope, expired_at=None):
    """Save a token to the database"""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            created_at = int(time.time())
            
            # Convert expired_at to integer timestamp if provided
            expired_at_int = None
            if expired_at:
                expired_at_int = int(expired_at)
            
            cursor.execute(
                "INSERT INTO tokens (token, scope, created_at, expired_at) VALUES (?, ?, ?, ?)",
                (token, scope, created_at, expired_at_int)
            )
            conn.commit()
            return True
        except Error as e:
            print(f"Error saving token: {e}")
            return False
        finally:
            conn.close()
    return False

def delete_token(token):
    """Delete a token from the database"""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tokens WHERE token = ?", (token,))
            conn.commit()
            return cursor.rowcount > 0
        except Error as e:
            print(f"Error deleting token: {e}")
            return False
        finally:
            conn.close()
    return False

def get_all_tokens():
    """Get all tokens from the database"""
    conn = get_db_connection()
    tokens = []
    
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT token, scope, expired_at FROM tokens")
            
            for row in cursor.fetchall():
                # Check if token has expired
                if row['expired_at'] and int(time.time()) > row['expired_at']:
                    # Skip expired tokens
                    continue
                
                tokens.append({
                    "token": row['token'],
                    "scope": row['scope'],
                    "expired_at": row['expired_at']
                })
            
        except Error as e:
            print(f"Error retrieving tokens: {e}")
        finally:
            conn.close()
    
    return tokens