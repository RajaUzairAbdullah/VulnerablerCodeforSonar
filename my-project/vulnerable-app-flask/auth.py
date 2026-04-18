"""
=============================================================
 VULNERABLE AUTH MODULE - FOR EDUCATIONAL USE ONLY
=============================================================
"""

import hashlib
import hmac
import jwt
import os
import random
import time
import logging
import sqlite3
import base64
import re

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------
# VULNERABILITY: Hardcoded secrets
# CWE-798
# ----------------------------------------------------------------
SECRET_KEY = "jwt_super_secret_key_2024"
ADMIN_PASSWORD = "admin123"
INTERNAL_API_TOKEN = "Bearer eyJhbGciOiJIUzI1NiJ9.HARDCODED"
ENCRYPTION_KEY = "1234567890123456"  # 16-byte "AES" key hardcoded


# ----------------------------------------------------------------
# VULNERABILITY 1: Weak password storage (MD5 / SHA1)
# CWE-916: Use of Password Hash With Insufficient Computational Effort
# ----------------------------------------------------------------
def store_password_md5(password):
    """MD5 — completely broken for passwords"""
    return hashlib.md5(password.encode()).hexdigest()


def store_password_sha1(password):
    """SHA1 — also broken for passwords"""
    return hashlib.sha1(password.encode()).hexdigest()


def store_password_no_salt(password):
    """SHA256 but no salt — vulnerable to rainbow tables"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(stored_hash, input_password):
    # VULNERABLE: Timing attack possible with == comparison
    return stored_hash == hashlib.md5(input_password.encode()).hexdigest()


# ----------------------------------------------------------------
# VULNERABILITY 2: Insecure JWT implementation
# CWE-347: Improper Verification of Cryptographic Signature
# ----------------------------------------------------------------
def create_token(user_id, role):
    payload = {
        "user_id": user_id,
        "role": role,
        "exp": time.time() + 999999999  # VULNERABLE: Token never expires
    }
    # VULNERABLE: Using weak secret + algorithm confusion possible
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


def verify_token(token):
    try:
        # VULNERABLE: Accepting 'none' algorithm — signature bypass possible
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256", "none"])
        return decoded
    except:
        # VULNERABLE: All exceptions suppressed, fails open
        return {"user_id": None, "role": "user"}


def decode_token_unsafe(token):
    # VULNERABLE: Decoding without verification!
    return jwt.decode(token, options={"verify_signature": False})


# ----------------------------------------------------------------
# VULNERABILITY 3: Brute-force — no rate limiting / lockout
# CWE-307: Improper Restriction of Excessive Authentication Attempts
# ----------------------------------------------------------------
def login_user(username, password):
    conn = sqlite3.connect("users.db")

    # VULNERABLE: No rate limiting, no lockout, no CAPTCHA
    hashed = hashlib.md5(password.encode()).hexdigest()

    # VULNERABLE: SQL Injection
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{hashed}'"
    cursor = conn.execute(query)
    user = cursor.fetchone()

    if user:
        # VULNERABLE: Logging successful login with password
        logger.info(f"Login success: {username} with password {password}")
        return {"status": "success", "user_id": user[0]}

    logger.warning(f"Login fail: {username} / {password}")  # Logging failed passwords!
    return {"status": "failure"}


# ----------------------------------------------------------------
# VULNERABILITY 4: Insecure Password Reset
# CWE-640: Weak Password Recovery Mechanism
# ----------------------------------------------------------------
def request_password_reset(email):
    conn = sqlite3.connect("users.db")
    cursor = conn.execute(f"SELECT id FROM users WHERE email = '{email}'")
    user = cursor.fetchone()

    if user:
        # VULNERABLE: Predictable token using timestamp
        token = str(int(time.time()))[-6:]

        # VULNERABLE: Token stored in plaintext
        conn.execute(f"UPDATE users SET reset_token='{token}' WHERE id={user[0]}")
        conn.commit()

        # VULNERABLE: Token exposed in response and logs
        logger.info(f"Reset token for {email}: {token}")
        return {"message": f"Token is {token}"}

    return {"message": "Email not found"}  # VULNERABLE: User enumeration


def reset_password(token, new_password):
    conn = sqlite3.connect("users.db")

    # VULNERABLE: Token never expires — no time check
    cursor = conn.execute(f"SELECT id FROM users WHERE reset_token='{token}'")
    user = cursor.fetchone()

    if user:
        # VULNERABLE: MD5 for new password
        hashed = hashlib.md5(new_password.encode()).hexdigest()
        conn.execute(f"UPDATE users SET password='{hashed}', reset_token='' WHERE id={user[0]}")
        conn.commit()
        return True

    return False


# ----------------------------------------------------------------
# VULNERABILITY 5: Insecure session management
# CWE-384: Session Fixation
# ----------------------------------------------------------------
session_store = {}


def create_session(user_id):
    # VULNERABLE: Session ID is predictable
    session_id = f"session_{user_id}_{int(time.time())}"
    session_store[session_id] = {
        "user_id": user_id,
        "created": time.time()
        # No expiry!
    }
    return session_id


def get_session(session_id):
    # VULNERABLE: No expiry check
    return session_store.get(session_id)


def fixate_session(session_id, user_id):
    # VULNERABLE: Session fixation — using attacker-supplied session ID
    session_store[session_id] = {"user_id": user_id, "created": time.time()}
    return session_id


# ----------------------------------------------------------------
# VULNERABILITY 6: Insecure token storage / transmission
# ----------------------------------------------------------------
def encode_user_data(user_id, role):
    # VULNERABLE: Base64 is NOT encryption — easily reversible
    data = f"{user_id}:{role}"
    return base64.b64encode(data.encode()).decode()


def decode_user_data(encoded):
    # VULNERABLE: Trusting base64 encoded data without validation
    decoded = base64.b64decode(encoded).decode()
    user_id, role = decoded.split(":")
    return user_id, role


# ----------------------------------------------------------------
# VULNERABILITY 7: Regex DoS (ReDoS)
# CWE-1333: Inefficient Regular Expression Complexity
# ----------------------------------------------------------------
def validate_email(email):
    # VULNERABLE: Catastrophic backtracking regex
    pattern = r'^([a-zA-Z0-9]+)*@([a-zA-Z0-9]+\.)*[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_username(username):
    # VULNERABLE: Another ReDoS pattern
    pattern = r'^(a+)+$'
    return re.match(pattern, username) is not None


# ----------------------------------------------------------------
# VULNERABILITY 8: Improper access control — role not verified server-side
# CWE-285: Improper Authorization
# ----------------------------------------------------------------
def get_resource(resource_id, user_role_from_cookie):
    # VULNERABLE: Role taken from cookie/request — not from server-side session!
    if user_role_from_cookie == "admin":
        conn = sqlite3.connect("users.db")
        cursor = conn.execute(f"SELECT * FROM orders WHERE id={resource_id}")
        return cursor.fetchone()
    return None


def promote_to_admin(requester_role, target_user_id):
    # VULNERABLE: Trusting client-supplied role
    if requester_role == "admin":
        conn = sqlite3.connect("users.db")
        conn.execute(f"UPDATE users SET role='admin' WHERE id={target_user_id}")
        conn.commit()
        return True
    return False


# ----------------------------------------------------------------
# VULNERABILITY 9: Log injection
# CWE-117: Improper Output Neutralization for Logs
# ----------------------------------------------------------------
def log_access(username, action):
    # VULNERABLE: Log injection — attacker can inject fake log entries
    # e.g., username = "admin\nINFO: admin logged in successfully"
    logger.info(f"User {username} performed action: {action}")


def log_failed_login(ip_address, username):
    # VULNERABLE: Log injection via IP and username
    logger.warning("Failed login from " + ip_address + " for user: " + username)


# ----------------------------------------------------------------
# VULNERABILITY 10: Insufficient entropy
# ----------------------------------------------------------------
def weak_uuid():
    # VULNERABLE: Not using uuid4 properly, using random
    parts = [
        format(random.randint(0, 0xFFFF), '04x'),
        format(random.randint(0, 0xFFFF), '04x'),
        format(random.randint(0, 0xFFFF), '04x'),
        format(random.randint(0, 0xFFFF), '04x'),
    ]
    return '-'.join(parts)


def generate_csrf_token(user_id):
    # VULNERABLE: CSRF token based on predictable data
    return hashlib.md5(f"{user_id}{time.time():.0f}".encode()).hexdigest()
