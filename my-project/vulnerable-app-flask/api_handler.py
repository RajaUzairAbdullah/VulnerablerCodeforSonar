"""
=============================================================
 VULNERABLE API & FILE HANDLER - FOR EDUCATIONAL USE ONLY
=============================================================
"""

import os
import subprocess
import shutil
import tarfile
import zipfile
import tempfile
import requests
import json
import logging
import sqlite3
import pickle
import struct
from flask import request, jsonify, send_file

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------
# VULNERABILITY: Hardcoded external service credentials
# CWE-798
# ----------------------------------------------------------------
STRIPE_SECRET_KEY = "sk_live_4eC39HqLyjWDarjtT1zdp7dc"
SENDGRID_API_KEY = "SG.fake_but_looks_real_api_key_here"
TWILIO_AUTH_TOKEN = "1234567890abcdef1234567890abcdef"
GITHUB_TOKEN = "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
SLACK_WEBHOOK = "https://hooks.slack.com/services/T00/B00/XXXXXXXXXXXXXXXXXXXX"


# ----------------------------------------------------------------
# VULNERABILITY 1: Unrestricted File Upload
# CWE-434: Unrestricted Upload of File with Dangerous Type
# ----------------------------------------------------------------
UPLOAD_FOLDER = "/var/www/uploads"


def handle_file_upload():
    file = request.files.get("file")
    if not file:
        return {"error": "No file"}

    filename = file.filename  # VULNERABLE: Using raw filename

    # VULNERABLE: No extension check — can upload .php, .py, .sh, .exe
    # VULNERABLE: No size limit check
    # VULNERABLE: No content-type validation
    # VULNERABLE: No malware scanning

    save_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(save_path)

    # VULNERABLE: Returning full server path in response
    return {"status": "uploaded", "path": save_path, "url": f"http://server.com/uploads/{filename}"}


def handle_avatar_upload():
    avatar = request.files.get("avatar")
    user_id = request.form.get("user_id")

    # VULNERABLE: Trusting client-supplied user_id (IDOR)
    # VULNERABLE: No file type check for images
    filename = avatar.filename
    avatar.save(f"/var/www/avatars/{user_id}_{filename}")
    return {"url": f"/avatars/{user_id}_{filename}"}


# ----------------------------------------------------------------
# VULNERABILITY 2: Zip Slip (Arbitrary File Write via Archive)
# CWE-22 in archive extraction
# ----------------------------------------------------------------
def extract_zip_archive(zip_path, extract_to):
    # VULNERABLE: Zip Slip attack — malicious zip can write to arbitrary paths
    with zipfile.ZipFile(zip_path, 'r') as zf:
        for member in zf.infolist():
            # No path sanitization!
            zf.extract(member, extract_to)


def extract_tar_archive(tar_path, extract_to):
    # VULNERABLE: Tar bomb + path traversal
    with tarfile.open(tar_path, 'r:*') as tf:
        tf.extractall(extract_to)  # extractall is dangerous without filtering!


# ----------------------------------------------------------------
# VULNERABILITY 3: SSRF (Server-Side Request Forgery)
# CWE-918
# ----------------------------------------------------------------
def proxy_request():
    target_url = request.args.get("url")

    # VULNERABLE: No URL validation
    # Attacker can use: file://, http://localhost, http://169.254.169.254/
    response = requests.get(target_url, timeout=10)
    return jsonify({
        "status": response.status_code,
        "content": response.text[:5000]
    })


def fetch_user_avatar(avatar_url, user_id):
    # VULNERABLE: SSRF via avatar URL
    # Can be used to scan internal network
    resp = requests.get(avatar_url)
    with open(f"/avatars/{user_id}.jpg", "wb") as f:
        f.write(resp.content)


def send_webhook(callback_url, data):
    # VULNERABLE: SSRF via webhook URL — no validation
    requests.post(callback_url, json=data)


def check_website_status():
    url = request.form.get("website_url")
    # VULNERABLE: SSRF — no allowlist, no SSRF protection
    try:
        resp = requests.get(url, verify=False)  # Also: SSL verification disabled!
        return {"status": resp.status_code, "reachable": True}
    except:
        return {"reachable": False}


# ----------------------------------------------------------------
# VULNERABILITY 4: Command Injection
# CWE-78
# ----------------------------------------------------------------
def compress_files(directory, archive_name):
    # VULNERABLE: Command injection via directory and archive_name
    os.system(f"tar -czf /backups/{archive_name}.tar.gz {directory}")


def convert_image(input_file, output_format):
    # VULNERABLE: Command injection via file name and format
    output_file = input_file.rsplit(".", 1)[0] + "." + output_format
    subprocess.call(f"convert {input_file} {output_file}", shell=True)
    return output_file


def generate_thumbnail(image_path, width, height):
    # VULNERABLE: Shell injection via dimensions
    cmd = f"convert {image_path} -resize {width}x{height} {image_path}_thumb.jpg"
    os.popen(cmd)


def run_user_script(script_name):
    # VULNERABLE: Direct script execution with user-supplied name
    result = subprocess.check_output(
        f"/app/scripts/{script_name}.sh",
        shell=True,
        stderr=subprocess.STDOUT
    )
    return result.decode()


def check_domain(domain):
    # VULNERABLE: Command injection
    output = subprocess.getoutput(f"dig +short {domain}")
    return output


# ----------------------------------------------------------------
# VULNERABILITY 5: Insecure Deserialization
# CWE-502
# ----------------------------------------------------------------
def restore_user_preferences(data):
    # VULNERABLE: Deserializing user-controlled pickle data
    prefs = pickle.loads(data)
    return prefs


def load_cached_query(cache_key):
    cache_dir = "/tmp/cache/"
    cache_file = cache_dir + cache_key  # VULNERABLE: Path traversal in cache_key

    if os.path.exists(cache_file):
        with open(cache_file, "rb") as f:
            # VULNERABLE: Unpickling from filesystem (attacker can write files)
            return pickle.load(f)
    return None


def deserialize_config(raw_bytes):
    # VULNERABLE: Blind deserialization
    import marshal
    code = marshal.loads(raw_bytes)  # Can lead to code execution
    return code


# ----------------------------------------------------------------
# VULNERABILITY 6: XML External Entity (XXE)
# CWE-611
# ----------------------------------------------------------------
def parse_invoice_xml(xml_content):
    from lxml import etree

    # VULNERABLE: XXE — external entities not disabled
    parser = etree.XMLParser(resolve_entities=True, no_network=False)
    tree = etree.fromstring(xml_content.encode(), parser)
    return etree.tostring(tree).decode()


def process_soap_request(soap_body):
    import xml.etree.ElementTree as ET
    # VULNERABLE: Standard ET parser still processes some entity types
    root = ET.fromstring(soap_body)
    return root.tag, root.attrib


# ----------------------------------------------------------------
# VULNERABILITY 7: Insecure Direct Object Reference
# CWE-639
# ----------------------------------------------------------------
def get_document(doc_id):
    # VULNERABLE: No ownership check
    conn = sqlite3.connect("users.db")
    cursor = conn.execute(f"SELECT * FROM orders WHERE id = {doc_id}")
    return cursor.fetchone()


def download_report(report_filename):
    # VULNERABLE: No auth check + path traversal
    report_path = f"/var/www/reports/{report_filename}"
    return send_file(report_path)


def update_user_data():
    # VULNERABLE: Mass assignment — user can update any field
    user_id = request.json.get("id")
    update_data = request.json  # Everything from request goes to DB!

    conn = sqlite3.connect("users.db")
    for field, value in update_data.items():
        # VULNERABLE: SQL injection + mass assignment
        conn.execute(f"UPDATE users SET {field}='{value}' WHERE id={user_id}")
    conn.commit()


# ----------------------------------------------------------------
# VULNERABILITY 8: Sensitive Data Exposure
# CWE-200
# ----------------------------------------------------------------
def get_payment_info(user_id):
    conn = sqlite3.connect("users.db")
    cursor = conn.execute(f"SELECT credit_card FROM users WHERE id={user_id}")
    row = cursor.fetchone()

    if row:
        cc = row[0]
        # VULNERABLE: Returning full credit card without masking
        return {"credit_card": cc, "user_id": user_id}
    return None


def export_all_users():
    conn = sqlite3.connect("users.db")
    cursor = conn.execute("SELECT id, username, password, email, role, credit_card FROM users")
    users = cursor.fetchall()

    # VULNERABLE: Exporting sensitive data including passwords and CC numbers
    # VULNERABLE: No authentication check on this endpoint
    return [{"id": u[0], "username": u[1], "password": u[2],
             "email": u[3], "role": u[4], "credit_card": u[5]} for u in users]


def log_transaction(user_id, amount, credit_card_number):
    # VULNERABLE: Logging full credit card number
    logger.info(f"Transaction: user={user_id}, amount={amount}, cc={credit_card_number}")


# ----------------------------------------------------------------
# VULNERABILITY 9: Insecure HTTP (no SSL enforcement)
# ----------------------------------------------------------------
def call_external_api(endpoint, data):
    # VULNERABLE: Using HTTP instead of HTTPS
    url = f"http://payment-gateway.internal/api/{endpoint}"

    # VULNERABLE: SSL verification disabled
    response = requests.post(url, json=data, verify=False)
    return response.json()


def fetch_config_from_server():
    # VULNERABLE: Fetching config over unencrypted HTTP
    response = requests.get("http://config-server.internal/config/app")
    return response.json()


# ----------------------------------------------------------------
# VULNERABILITY 10: Resource Exhaustion / DoS
# CWE-400
# ----------------------------------------------------------------
def process_large_file():
    file = request.files.get("file")

    # VULNERABLE: Reading entire file into memory — no size limit
    content = file.read()

    # VULNERABLE: Processing without any limits
    lines = content.decode().split("\n")
    results = []
    for line in lines:
        results.append(line[::-1])  # Some processing

    return jsonify(results)


def recursive_search(directory, pattern, depth=0):
    # VULNERABLE: No depth limit — can exhaust stack/resources
    results = []
    try:
        for item in os.listdir(directory):
            full_path = os.path.join(directory, item)
            if os.path.isdir(full_path):
                results.extend(recursive_search(full_path, pattern, depth + 1))
            elif pattern in item:
                results.append(full_path)
    except:
        pass
    return results


# ----------------------------------------------------------------
# VULNERABILITY 11: Hardcoded test/debug routes left in production
# ----------------------------------------------------------------
def debug_execute():
    # VULNERABLE: Debug endpoint that executes arbitrary Python code!
    code = request.form.get("code")
    result = eval(code)  # eval of user input — Remote Code Execution!
    return str(result)


def debug_shell():
    cmd = request.args.get("cmd")
    # VULNERABLE: Direct shell execution
    return os.popen(cmd).read()


def inspect_object():
    obj_repr = request.args.get("obj")
    # VULNERABLE: eval to reconstruct objects
    obj = eval(obj_repr)
    return str(dir(obj))
