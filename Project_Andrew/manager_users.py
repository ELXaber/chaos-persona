#V05282026
#!/usr/bin/env python3
"""
CAIOS User Password Manager
Add, change, or remove passwords from users.json without re-running master_init.
"""

import json
import hashlib
import getpass
import os
from datetime import datetime, timezone

USERS_FILE = "users.json"

def load_users() -> dict:
    if not os.path.exists(USERS_FILE):
        print(f"[ERROR] {USERS_FILE} not found. Run master_init.py first.")
        exit(1)
    with open(USERS_FILE, 'r') as f:
        return json.load(f)

def save_users(data: dict) -> None:
    data['last_updated'] = datetime.now(timezone.utc).strftime(
        '%Y-%m-%dT%H:%M:%S.%f') + "Z"
    with open(USERS_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"✓ {USERS_FILE} updated.")

def list_users(data: dict) -> None:
    print("\nCurrent users:")
    print("-" * 40)
    for i, user in enumerate(data['users'], 1):
        has_pw = "🔒 password set" if 'password_hash' in user else "🔓 no password"
        print(f"  {i}. {user['id']} ({user['type']}) — {has_pw}")
    print("-" * 40)

def set_password(data: dict, user_id: str) -> None:
    users = {u['id']: u for u in data['users']}
    if user_id not in users:
        print(f"[ERROR] User '{user_id}' not found.")
        return
    while True:
        pw = getpass.getpass(f"New password for '{user_id}': ")
        pw2 = getpass.getpass("Confirm password: ")
        if pw == pw2:
            break
        print("Passwords don't match, try again.")
    users[user_id]['password_hash'] = hashlib.sha256(pw.encode()).hexdigest()
    data['users'] = list(users.values())
    save_users(data)
    print(f"✓ Password set for {user_id}")

def remove_password(data: dict, user_id: str) -> None:
    users = {u['id']: u for u in data['users']}
    if user_id not in users:
        print(f"[ERROR] User '{user_id}' not found.")
        return
    if 'password_hash' not in users[user_id]:
        print(f"[INFO] {user_id} has no password set.")
        return
    confirm = input(f"Remove password for '{user_id}'? (y/n): ").strip().lower()
    if confirm == 'y':
        del users[user_id]['password_hash']
        data['users'] = list(users.values())
        save_users(data)
        print(f"✓ Password removed for {user_id}")

def main():
    print("="*50)
    print("CAIOS User Password Manager")
    print("="*50)

    data = load_users()

    while True:
        list_users(data)
        print("\nOptions:")
        print("  1. Set/change password for a user")
        print("  2. Remove password for a user")
        print("  3. Exit")

        choice = input("\nSelect option (1-3): ").strip()

        if choice == '1':
            user_id = input("Enter user ID exactly as shown: ").strip()
            set_password(data, user_id)
        elif choice == '2':
            user_id = input("Enter user ID exactly as shown: ").strip()
            remove_password(data, user_id)
        elif choice == '3':
            print("Done.")
            break
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    main()