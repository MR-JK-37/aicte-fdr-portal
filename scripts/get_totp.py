#!/usr/bin/env python3
import sys, json, time, hmac, hashlib, struct, base64
from pathlib import Path

def get_totp(secret):
    key = base64.b32decode(secret, True)
    counter = int(time.time() // 30)
    msg = struct.pack(">Q", counter)
    h = hmac.new(key, msg, hashlib.sha1).digest()
    o = h[19] & 15
    h_int = (struct.unpack(">I", h[o:o+4])[0] & 0x7fffffff) % 1000000
    return f"{h_int:06d}"

users_file = Path(__file__).resolve().parent.parent / ".local" / "staging-users.json"
if not users_file.exists():
    print(f"File not found: {users_file}")
    sys.exit(1)

with open(users_file) as f:
    users = json.load(f)

query = sys.argv[1].lower() if len(sys.argv) > 1 else ""
remaining = 30 - (int(time.time()) % 30)

matched = [u for u in users if query in u["role"].lower() or query in u["email"].lower()] if query else users

print(f"Codes valid for next {remaining}s:")
print(f"{'Role':<22} | {'Email':<38} | {'Current TOTP':<12} | {'Recovery Code'}")
print("-" * 92)
for u in matched:
    code = get_totp(u["totp_secret"])
    recovery = u["recovery_codes"][0] if u.get("recovery_codes") else "N/A"
    print(f"{u['role']:<22} | {u['email']:<38} | {code:<12} | {recovery}")
