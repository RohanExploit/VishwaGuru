import hashlib
import sqlite3
import os
from datetime import datetime

# Setup test DB
DB_FILE = "test_blockchain_enhanced.db"
if os.path.exists(DB_FILE):
    os.remove(DB_FILE)

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

# Create table
cursor.execute("""
CREATE TABLE issues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    description TEXT,
    category TEXT,
    integrity_hash TEXT,
    previous_integrity_hash TEXT
)
""")
conn.commit()

def create_issue(desc, cat):
    cursor.execute("SELECT integrity_hash FROM issues ORDER BY id DESC LIMIT 1")
    last_row = cursor.fetchone()
    prev_hash = last_row[0] if last_row else ""

    hash_content = f"{desc}|{cat}|{prev_hash}"
    integrity_hash = hashlib.sha256(hash_content.encode()).hexdigest()

    cursor.execute("INSERT INTO issues (description, category, integrity_hash, previous_integrity_hash) VALUES (?, ?, ?, ?)",
                   (desc, cat, integrity_hash, prev_hash))
    conn.commit()
    return cursor.lastrowid

def verify_issue(issue_id):
    cursor.execute("SELECT description, category, integrity_hash, previous_integrity_hash FROM issues WHERE id = ?", (issue_id,))
    current = cursor.fetchone()
    if not current:
        return False, "Issue not found"
    desc, cat, stored_hash, stored_prev_hash = current

    prev_hash = stored_prev_hash or ""
    hash_content = f"{desc}|{cat}|{prev_hash}"
    computed = hashlib.sha256(hash_content.encode()).hexdigest()

    # Step 1: Internal Consistency
    internal_valid = (computed == stored_hash)

    # Step 2: Chain Link
    cursor.execute("SELECT integrity_hash FROM issues WHERE id < ? ORDER BY id DESC LIMIT 1", (issue_id,))
    predecessor = cursor.fetchone()

    chain_status = "Intact"
    if predecessor:
        if predecessor[0] != prev_hash:
            chain_status = "Broken (Link Mismatch)"
    elif prev_hash:
        chain_status = "Broken (Predecessor Missing)"

    return internal_valid, chain_status

print("1. Creating issues...")
id_a = create_issue("Issue A", "Road")
id_b = create_issue("Issue B", "Water")
id_c = create_issue("Issue C", "Fire")

print("\n4. Verifying Issue C (Expect: Valid, Intact)...")
valid, status = verify_issue(id_c)
print(f"   Valid: {valid}, Status: {status}")
assert valid == True
assert status == "Intact"

print("\n5. Deleting Issue B...")
cursor.execute("DELETE FROM issues WHERE id = ?", (id_b,))
conn.commit()

print("\n6. Verifying Issue C again (Expect: Valid, Broken (Predecessor Missing))...")
valid, status = verify_issue(id_c)
print(f"   Valid: {valid}, Status: {status}")
assert valid == True
assert status == "Broken (Predecessor Missing)"

print("\nTest PASSED")

conn.close()
if os.path.exists(DB_FILE):
    os.remove(DB_FILE)
