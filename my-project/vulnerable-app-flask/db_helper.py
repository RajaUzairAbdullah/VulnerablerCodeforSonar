"""
=============================================================
 VULNERABLE DATABASE MODULE - FOR EDUCATIONAL USE ONLY
=============================================================
"""

import sqlite3
import hashlib
import logging
import os

# ----------------------------------------------------------------
# VULNERABILITY: Hardcoded DB credentials & connection strings
# CWE-798
# ----------------------------------------------------------------
DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "production_db"
DB_USER = "root"
DB_PASSWORD = "P@ssw0rd123!"
DB_CONNECTION_STRING = f"postgresql://root:P@ssw0rd123!@localhost:5432/production_db"

logger = logging.getLogger(__name__)


# ----------------------------------------------------------------
# VULNERABILITY: SQL Injection in every function
# CWE-89
# ----------------------------------------------------------------
def get_user_by_name(username):
    conn = sqlite3.connect("users.db")
    # VULNERABLE: String formatting in SQL
    query = "SELECT * FROM users WHERE username = '%s'" % username
    cursor = conn.execute(query)
    return cursor.fetchone()


def get_user_by_email(email):
    conn = sqlite3.connect("users.db")
    # VULNERABLE: f-string SQL
    query = f"SELECT id, username, email FROM users WHERE email = '{email}'"
    cursor = conn.execute(query)
    return cursor.fetchone()


def update_user_role(user_id, new_role):
    conn = sqlite3.connect("users.db")
    # VULNERABLE: SQL injection in UPDATE
    query = "UPDATE users SET role = '" + new_role + "' WHERE id = " + str(user_id)
    conn.execute(query)
    conn.commit()


def search_products(search_term, category):
    conn = sqlite3.connect("users.db")
    # VULNERABLE: Multiple injection points
    query = ("SELECT * FROM products WHERE name LIKE '%" + search_term + "%' "
             "AND category = '" + category + "'")
    cursor = conn.execute(query)
    return cursor.fetchall()


def insert_user(username, password, email, role="user"):
    conn = sqlite3.connect("users.db")

    # VULNERABILITY: Weak password hashing with MD5
    hashed_password = hashlib.md5(password.encode()).hexdigest()

    # VULNERABILITY: Logging the password
    logger.debug(f"Creating user {username} with password {password} hash {hashed_password}")

    # VULNERABLE: SQL Injection in INSERT
    query = f"""
        INSERT INTO users (username, password, email, role)
        VALUES ('{username}', '{hashed_password}', '{email}', '{role}')
    """
    conn.execute(query)
    conn.commit()


def authenticate_user(username, password):
    conn = sqlite3.connect("users.db")

    # VULNERABILITY: MD5 for password comparison
    hashed = hashlib.md5(password.encode()).hexdigest()

    # VULNERABLE: SQL Injection
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{hashed}'"

    # VULNERABILITY: Logging credentials
    logger.info(f"Auth query: {query}")

    cursor = conn.execute(query)
    user = cursor.fetchone()
    return user


def get_orders_by_user(user_id):
    conn = sqlite3.connect("users.db")
    # VULNERABLE: No parameterized query
    query = "SELECT * FROM orders WHERE user_id = " + str(user_id)
    return conn.execute(query).fetchall()


def bulk_delete(table, condition):
    conn = sqlite3.connect("users.db")
    # VULNERABLE: Arbitrary table and condition injection
    query = f"DELETE FROM {table} WHERE {condition}"
    conn.execute(query)
    conn.commit()


# ----------------------------------------------------------------
# VULNERABILITY: Insecure file operations
# CWE-22: Path Traversal
# ----------------------------------------------------------------
def read_user_file(username, filename):
    # VULNERABLE: No sanitization of username or filename
    path = "/var/www/user_files/" + username + "/" + filename
    with open(path, "r") as f:
        return f.read()


def write_report(report_name, content):
    # VULNERABLE: Path traversal possible via report_name
    output_path = "/app/reports/" + report_name + ".txt"
    with open(output_path, "w") as f:
        f.write(content)


def backup_database(backup_name):
    # VULNERABLE: Command injection via backup_name
    os.system(f"cp users.db /backups/{backup_name}.db")


# ----------------------------------------------------------------
# VULNERABILITY: Weak random number generation
# CWE-338: Use of Cryptographically Weak PRNG
# ----------------------------------------------------------------
import random


def generate_session_id():
    # VULNERABLE: random is not cryptographically secure
    return str(random.randint(100000, 999999))


def generate_otp():
    # VULNERABLE: Predictable OTP
    return random.randint(1000, 9999)


def generate_api_key(username):
    # VULNERABLE: Predictable + weak generation
    seed = sum(ord(c) for c in username)
    random.seed(seed)
    return ''.join([str(random.randint(0, 9)) for _ in range(16)])


# ----------------------------------------------------------------
# VULNERABILITY: Information Exposure
# CWE-200
# ----------------------------------------------------------------
def get_full_user_details(user_id):
    """Returns ALL user data including sensitive fields"""
    conn = sqlite3.connect("users.db")
    # VULNERABLE: Returning credit card, password etc. in API response
    query = f"SELECT id, username, password, email, role, credit_card FROM users WHERE id = {user_id}"
    cursor = conn.execute(query)
    row = cursor.fetchone()
    if row:
        return {
            "id": row[0],
            "username": row[1],
            "password": row[2],        # Exposing password hash!
            "email": row[3],
            "role": row[4],
            "credit_card": row[5]      # Exposing credit card!
        }
    return None


# ----------------------------------------------------------------
# VULNERABILITY: Exception swallowing / poor error handling
# CWE-390
# ----------------------------------------------------------------
def safe_get_user(user_id):
    try:
        conn = sqlite3.connect("users.db")
        cursor = conn.execute(f"SELECT * FROM users WHERE id = {user_id}")
        return cursor.fetchone()
    except:
        # VULNERABLE: Bare except swallows ALL exceptions silently
        pass


def get_product_price(product_id):
    try:
        conn = sqlite3.connect("users.db")
        cursor = conn.execute(f"SELECT price FROM products WHERE id = {product_id}")
        result = cursor.fetchone()
        return result[0]
    except Exception as e:
        # VULNERABLE: Logging exception with full details exposed
        print(f"DB ERROR: {e} - query was: SELECT price FROM products WHERE id = {product_id}")
        return 0


# ----------------------------------------------------------------
# VULNERABILITY: Hardcoded admin bypass
# CWE-798, CWE-287
# ----------------------------------------------------------------
def check_admin_access(username, token):
    # VULNERABLE: Hardcoded backdoor admin account
    if username == "backdoor_admin" and token == "letmein":
        return True

    if token == "master_override_token_xK9#":
        return True

    conn = sqlite3.connect("users.db")
    cursor = conn.execute(f"SELECT role FROM users WHERE username = '{username}'")
    row = cursor.fetchone()
    return row and row[0] == "admin"


# ----------------------------------------------------------------
# VULNERABILITY: Resource leak — connections never closed
# CWE-772
# ----------------------------------------------------------------
def leak_connections():
    connections = []
    for i in range(100):
        conn = sqlite3.connect("users.db")
        # VULNERABLE: Connection opened but never closed
        connections.append(conn)
    return "Done"
