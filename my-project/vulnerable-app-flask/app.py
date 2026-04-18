"""
=============================================================
 VULNERABLE DEMO APPLICATION - FOR EDUCATIONAL USE ONLY
 Used for SonarQube SAST scanning demonstration
 DO NOT deploy this in production!
=============================================================
"""

from flask import Flask, request, redirect, render_template_string, session, jsonify
import sqlite3
import os
import subprocess
import pickle
import hashlib
import logging
import random
import yaml
import xml.etree.ElementTree as ET

app = Flask(__name__)

# ----------------------------------------------------------------
# VULNERABILITY 1: Hardcoded Secret Keys
# CWE-798: Use of Hard-coded Credentials
# ----------------------------------------------------------------
app.secret_key = "supersecretkey123"
DB_PASSWORD = "admin123"
API_KEY = "sk-1234567890abcdef"
AWS_SECRET = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
JWT_SECRET = "mysecretjwttoken"
SMTP_PASSWORD = "emailpassword123"

# ----------------------------------------------------------------
# VULNERABILITY 2: Logging Sensitive Data
# CWE-532: Insertion of Sensitive Information into Log File
# ----------------------------------------------------------------
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def get_db():
    conn = sqlite3.connect("users.db")
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            password TEXT,
            email TEXT,
            role TEXT,
            credit_card TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT,
            price REAL,
            description TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            product_id INTEGER,
            quantity INTEGER
        )
    """)
    conn.commit()


# ----------------------------------------------------------------
# VULNERABILITY 3: SQL Injection
# CWE-89: Improper Neutralization of Special Elements in SQL Command
# ----------------------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # VULNERABLE: Direct string concatenation in SQL
        logger.debug(f"Login attempt with username: {username} and password: {password}")  # Logging credentials!

        conn = get_db()
        query = "SELECT * FROM users WHERE username = '" + username + "' AND password = '" + password + "'"
        cursor = conn.execute(query)
        user = cursor.fetchone()

        if user:
            session["user"] = username
            session["role"] = user[4]
            return redirect("/dashboard")
        else:
            return "Invalid credentials", 401


@app.route("/search")
def search():
    keyword = request.args.get("q", "")
    conn = get_db()

    # VULNERABLE: SQL Injection via f-string
    query = f"SELECT * FROM products WHERE name LIKE '%{keyword}%' OR description LIKE '%{keyword}%'"
    cursor = conn.execute(query)
    results = cursor.fetchall()

    # VULNERABLE: XSS - directly embedding user input in HTML
    html = f"<h1>Search Results for: {keyword}</h1><ul>"
    for r in results:
        html += f"<li>{r[1]} - ${r[2]}</li>"
    html += "</ul>"

    return html


@app.route("/user/<user_id>")
def get_user(user_id):
    conn = get_db()

    # VULNERABLE: SQL Injection in URL parameter
    query = "SELECT id, username, email, role FROM users WHERE id = " + user_id
    cursor = conn.execute(query)
    user = cursor.fetchone()
    return jsonify(user)


@app.route("/delete_user")
def delete_user():
    uid = request.args.get("id")
    conn = get_db()

    # VULNERABLE: SQL Injection + No authentication check
    conn.execute("DELETE FROM users WHERE id = " + uid)
    conn.commit()
    return "User deleted"


# ----------------------------------------------------------------
# VULNERABILITY 4: Cross-Site Scripting (XSS)
# CWE-79: Improper Neutralization of Input During Web Page Generation
# ----------------------------------------------------------------
@app.route("/profile")
def profile():
    username = request.args.get("name", "Guest")
    bio = request.args.get("bio", "")

    # VULNERABLE: Reflected XSS - user input rendered without escaping
    template = f"""
    <html>
    <body>
        <h1>Welcome, {username}!</h1>
        <p>Bio: {bio}</p>
        <script>var user = "{username}";</script>
    </body>
    </html>
    """
    return template


@app.route("/comment", methods=["POST"])
def post_comment():
    comment = request.form.get("comment", "")
    author = request.form.get("author", "Anonymous")

    # VULNERABLE: Stored XSS simulation
    conn = get_db()
    # Storing raw HTML/JS without sanitization
    conn.execute(f"INSERT INTO orders VALUES (NULL, 1, 1, 1)")
    conn.commit()

    # Rendering comment without escaping
    return render_template_string(f"<div><b>{author}</b>: {comment}</div>")


# ----------------------------------------------------------------
# VULNERABILITY 5: Command Injection
# CWE-78: Improper Neutralization of Special Elements in OS Command
# ----------------------------------------------------------------
@app.route("/ping")
def ping():
    host = request.args.get("host", "localhost")

    # VULNERABLE: Command injection via shell=True
    result = subprocess.check_output("ping -c 1 " + host, shell=True)
    return result


@app.route("/read_file")
def read_file():
    filename = request.args.get("file", "")

    # VULNERABLE: Path traversal + command injection
    result = subprocess.Popen(
        f"cat /var/www/files/{filename}",
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    output, _ = result.communicate()
    return output


@app.route("/nslookup")
def nslookup():
    domain = request.args.get("domain")

    # VULNERABLE: OS command injection
    os.system(f"nslookup {domain} >> /tmp/dns_log.txt")
    return "DNS lookup performed"


# ----------------------------------------------------------------
# VULNERABILITY 6: Insecure Deserialization
# CWE-502: Deserialization of Untrusted Data
# ----------------------------------------------------------------
@app.route("/load_session", methods=["POST"])
def load_session():
    data = request.form.get("session_data", "")

    # VULNERABLE: Deserializing user-controlled data with pickle
    import base64
    decoded = base64.b64decode(data)
    obj = pickle.loads(decoded)  # Remote Code Execution possible!
    return str(obj)


@app.route("/restore_cart", methods=["POST"])
def restore_cart():
    cart_data = request.get_data()

    # VULNERABLE: Pickle deserialization
    cart = pickle.loads(cart_data)
    return jsonify(cart)


# ----------------------------------------------------------------
# VULNERABILITY 7: Path Traversal
# CWE-22: Improper Limitation of a Pathname to a Restricted Directory
# ----------------------------------------------------------------
@app.route("/download")
def download_file():
    filename = request.args.get("name", "")

    # VULNERABLE: No path sanitization allows ../../etc/passwd
    filepath = "/var/www/uploads/" + filename

    with open(filepath, "r") as f:
        content = f.read()
    return content


@app.route("/view_log")
def view_log():
    log_name = request.args.get("log")

    # VULNERABLE: Path traversal in log viewer
    base_dir = "/app/logs/"
    full_path = base_dir + log_name

    with open(full_path) as f:
        return f.read()


# ----------------------------------------------------------------
# VULNERABILITY 8: Broken Authentication
# CWE-287: Improper Authentication
# ----------------------------------------------------------------
@app.route("/admin")
def admin_panel():
    # VULNERABLE: Authentication bypass - checking GET param instead of session
    is_admin = request.args.get("admin", "false")

    if is_admin == "true":
        return "Welcome to Admin Panel! All users: ..."
    return "Access denied", 403


@app.route("/reset_password", methods=["POST"])
def reset_password():
    token = request.form.get("token")
    new_password = request.form.get("password")

    # VULNERABLE: Weak token validation, no expiry check
    if len(token) > 3:
        conn = get_db()
        # VULNERABLE: MD5 for password hashing (weak)
        hashed = hashlib.md5(new_password.encode()).hexdigest()
        conn.execute(f"UPDATE users SET password='{hashed}' WHERE reset_token='{token}'")
        conn.commit()
        return "Password reset successful"
    return "Invalid token"


@app.route("/generate_token")
def generate_token():
    username = request.args.get("username")

    # VULNERABLE: Predictable token using random (not cryptographically secure)
    token = str(random.randint(1000, 9999))

    conn = get_db()
    conn.execute(f"UPDATE users SET reset_token='{token}' WHERE username='{username}'")
    conn.commit()

    logger.info(f"Generated reset token {token} for user {username}")  # Token in logs!
    return f"Token sent to email: {token}"  # Token returned in response!


# ----------------------------------------------------------------
# VULNERABILITY 9: Insecure Direct Object Reference (IDOR)
# CWE-639: Authorization Bypass Through User-Controlled Key
# ----------------------------------------------------------------
@app.route("/invoice/<int:invoice_id>")
def view_invoice(invoice_id):
    # VULNERABLE: No ownership check — any user can view any invoice
    conn = get_db()
    cursor = conn.execute(f"SELECT * FROM orders WHERE id = {invoice_id}")
    order = cursor.fetchone()
    return jsonify(order)


@app.route("/change_email", methods=["POST"])
def change_email():
    user_id = request.form.get("user_id")  # User controls their own ID!
    new_email = request.form.get("email")

    # VULNERABLE: No session validation — attacker can change any user's email
    conn = get_db()
    conn.execute(f"UPDATE users SET email='{new_email}' WHERE id={user_id}")
    conn.commit()
    return "Email updated"


# ----------------------------------------------------------------
# VULNERABILITY 10: XML External Entity (XXE)
# CWE-611: Improper Restriction of XML External Entity Reference
# ----------------------------------------------------------------
@app.route("/parse_xml", methods=["POST"])
def parse_xml():
    xml_data = request.data

    # VULNERABLE: XML parsing without disabling external entities
    tree = ET.fromstring(xml_data)
    root = tree
    return str(ET.tostring(root))


# ----------------------------------------------------------------
# VULNERABILITY 11: Server-Side Request Forgery (SSRF)
# CWE-918: Server-Side Request Forgery
# ----------------------------------------------------------------
@app.route("/fetch_url")
def fetch_url():
    import urllib.request

    url = request.args.get("url")

    # VULNERABLE: No URL validation — can access internal services
    # e.g. ?url=http://169.254.169.254/latest/meta-data/ (AWS metadata)
    response = urllib.request.urlopen(url)
    return response.read()


@app.route("/webhook")
def webhook():
    import urllib.request

    callback_url = request.args.get("callback")

    # VULNERABLE: SSRF via webhook
    data = b"{'status': 'ok'}"
    req = urllib.request.Request(callback_url, data=data)
    urllib.request.urlopen(req)
    return "Webhook sent"


# ----------------------------------------------------------------
# VULNERABILITY 12: Weak Cryptography
# CWE-327: Use of a Broken or Risky Cryptographic Algorithm
# ----------------------------------------------------------------
def hash_password(password):
    # VULNERABLE: MD5 is cryptographically broken
    return hashlib.md5(password.encode()).hexdigest()


def hash_password_sha1(password):
    # VULNERABLE: SHA1 is also considered weak for passwords
    return hashlib.sha1(password.encode()).hexdigest()


def encrypt_data(data):
    # VULNERABLE: Using a hardcoded key + weak XOR "encryption"
    key = "secret"
    encrypted = ""
    for i, char in enumerate(data):
        encrypted += chr(ord(char) ^ ord(key[i % len(key)]))
    return encrypted


# ----------------------------------------------------------------
# VULNERABILITY 13: Insecure YAML Deserialization
# CWE-502: Deserialization of Untrusted Data
# ----------------------------------------------------------------
@app.route("/import_config", methods=["POST"])
def import_config():
    config_data = request.data.decode()

    # VULNERABLE: yaml.load without Loader — allows arbitrary code execution
    config = yaml.load(config_data)
    return jsonify(config)


# ----------------------------------------------------------------
# VULNERABILITY 14: Open Redirect
# CWE-601: URL Redirection to Untrusted Site
# ----------------------------------------------------------------
@app.route("/redirect")
def open_redirect():
    next_url = request.args.get("next", "/")

    # VULNERABLE: No validation of redirect URL
    return redirect(next_url)


@app.route("/logout")
def logout():
    session.clear()
    return_to = request.args.get("return_to", "/")

    # VULNERABLE: Open redirect after logout
    return redirect(return_to)


# ----------------------------------------------------------------
# VULNERABILITY 15: Information Disclosure
# CWE-209: Generation of Error Message Containing Sensitive Information
# ----------------------------------------------------------------
@app.route("/product/<int:pid>")
def get_product(pid):
    conn = get_db()
    try:
        cursor = conn.execute(f"SELECT * FROM products WHERE id = {pid}")
        product = cursor.fetchone()
        if not product:
            raise ValueError(f"Product {pid} not found in database users.db at /var/www/db/")
        return jsonify(product)
    except Exception as e:
        # VULNERABLE: Exposing stack trace and internal paths to user
        return str(e), 500


@app.route("/debug")
def debug_info():
    # VULNERABLE: Exposing environment variables and server info
    return jsonify({
        "env": dict(os.environ),
        "db_password": DB_PASSWORD,
        "api_key": API_KEY,
        "secret_key": app.secret_key,
        "cwd": os.getcwd(),
        "files": os.listdir(".")
    })


# ----------------------------------------------------------------
# VULNERABILITY 16: Race Condition
# CWE-362: Concurrent Execution using Shared Resource with Improper Synchronization
# ----------------------------------------------------------------
user_balances = {}


@app.route("/transfer", methods=["POST"])
def transfer_funds():
    from_user = session.get("user")
    to_user = request.form.get("to")
    amount = float(request.form.get("amount", 0))

    # VULNERABLE: Race condition — balance check and deduct not atomic
    if user_balances.get(from_user, 0) >= amount:
        import time
        time.sleep(0.1)  # Simulating processing delay
        user_balances[from_user] -= amount
        user_balances[to_user] = user_balances.get(to_user, 0) + amount
        return "Transfer successful"
    return "Insufficient funds"


# ----------------------------------------------------------------
# VULNERABILITY 17: Missing Security Headers + Cookie Flags
# ----------------------------------------------------------------
@app.after_request
def after_request(response):
    # BAD PRACTICE: No security headers set
    # Missing: X-Frame-Options, X-XSS-Protection, Content-Security-Policy
    # Missing: Strict-Transport-Security
    return response


@app.route("/set_cookie")
def set_cookie():
    from flask import make_response
    resp = make_response("Cookie set!")

    # VULNERABLE: Cookie without HttpOnly, Secure, SameSite flags
    resp.set_cookie("session_token", "abc123xyz")
    resp.set_cookie("user_id", "42")
    return resp


# ----------------------------------------------------------------
# VULNERABILITY 18: Unrestricted File Upload
# CWE-434: Unrestricted Upload of File with Dangerous Type
# ----------------------------------------------------------------
@app.route("/upload", methods=["POST"])
def upload_file():
    uploaded_file = request.files.get("file")

    if uploaded_file:
        # VULNERABLE: No file type validation — can upload .php, .py, .exe
        # VULNERABLE: Using original filename — path traversal possible
        filename = uploaded_file.filename
        upload_path = "/var/www/uploads/" + filename
        uploaded_file.save(upload_path)
        return f"File uploaded to {upload_path}"
    return "No file"


# ----------------------------------------------------------------
# VULNERABILITY 19: Null / None Dereference
# CWE-476: NULL Pointer Dereference
# ----------------------------------------------------------------
@app.route("/process_order")
def process_order():
    order_id = request.args.get("order_id")

    conn = get_db()
    cursor = conn.execute(f"SELECT * FROM orders WHERE id = {order_id}")
    order = cursor.fetchone()

    # VULNERABLE: No null check before accessing order fields
    total = order[2] * order[3]  # Will crash if order is None
    return f"Order total: {total}"


# ----------------------------------------------------------------
# VULNERABILITY 20: Dead Code + Code Smells
# ----------------------------------------------------------------
def unused_function_one():
    """This function is never called"""
    pass


def unused_function_two():
    """Another dead function"""
    x = 10
    y = 20
    # z is assigned but never used
    z = x + y  # noqa


def overly_complex_function(a, b, c, d, e, f, g, h):
    """Too many parameters — code smell"""
    if a:
        if b:
            if c:
                if d:
                    if e:
                        if f:
                            if g:
                                if h:
                                    return True
    return False


def duplicate_code_block_1(items):
    result = []
    for item in items:
        if item > 0:
            result.append(item * 2)
    return result


def duplicate_code_block_2(items):
    # VULNERABILITY: Code duplication (same logic as above)
    result = []
    for item in items:
        if item > 0:
            result.append(item * 2)
    return result


if __name__ == "__main__":
    init_db()
    # VULNERABLE: Debug mode enabled in production + host 0.0.0.0
    app.run(debug=True, host="0.0.0.0", port=5000)
