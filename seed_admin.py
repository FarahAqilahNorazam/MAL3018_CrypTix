"""
CrypTix Admin Seeding Script
============================
Preconfigures the official System Administrator account in the MySQL database.
Per requirement:
- Admin accounts CANNOT register via the public registration form.
- Admin accounts are strictly seeded into the database directly with role 'Admin'.
"""
import sys
from config import Config
from database.db import init_db, seed_admin_user, get_user_by_email
from utils.auth_utils import hash_password

def run_seed():
    print("[CrypTix] Initializing database schema...")
    init_db()

    admin_name = Config.ADMIN_DEFAULT_NAME
    admin_email = Config.ADMIN_DEFAULT_EMAIL
    admin_password = Config.ADMIN_DEFAULT_PASSWORD

    existing = get_user_by_email(admin_email)
    if existing:
        print(f"[CrypTix] Admin account already exists: {admin_email} (Role: {existing.get('role')})")
        return

    print(f"[CrypTix] Hashing admin password with BCrypt...")
    hashed_pw = hash_password(admin_password)

    print(f"[CrypTix] Seeding Admin into MySQL table `users`...")
    seeded = seed_admin_user(name=admin_name, email=admin_email, password_hash=hashed_pw)

    if seeded:
        print("---------------------------------------------------------------")
        print(" [SUCCESS] Admin Account Seeded Successfully!")
        print(f" Name:     {admin_name}")
        print(f" Email:    {admin_email}")
        print(f" Password: {admin_password}")
        print(f" Role:     Admin")
        print("---------------------------------------------------------------")
    else:
        print("[CrypTix] Admin user seed skipped (already exists).")

if __name__ == '__main__':
    run_seed()
