# CrypTix - Phase 1: Authentication & Identity Management

CrypTix is a cryptographically secured e-ticketing prototype designed for concert scalping mitigation.
This directory contains **Phase 1: Identity and Access Management (IAM)**.

## Implemented Phase 1 Features
- **User Registration**:
  - Role selection is completely disabled from registration. All new users are strictly created as **Customer**.
  - **Mandatory PDPA 2010 Consent Checkbox**: Accounts cannot be created unless the user explicitly acknowledges the data protection policy.
- **BCrypt Password Hashing**: Passwords are salted and hashed (12 rounds) before database storage.
- **JWT Session Authentication**: Upon successful login, a signed JSON Web Token is issued and stored in an HTTP-only secure cookie (`cryptix_token`).
- **Role-Based Access Control (RBAC)**:
  - `@login_required`: Restricts protected pages (`/dashboard`).
  - `@admin_required`: Restricts privileged routes (`/admin`).
- **Seeded System Administrator**: Admin accounts cannot register publicly; they are seeded manually via database script.
- **MySQL Database Support with Auto-Fallback**:
  - Connects to MySQL (`cryptix_db`) via `PyMySQL`.
  - If your MySQL/XAMPP service is not running during initial development, it automatically falls back to local SQLite (`cryptix_local.db`) so testing is never blocked.

---

## Default Seeded Admin Credentials
- **Email**: `admin@cryptix.com`
- **Password**: `AdminPassword123!`
- **Role**: `Admin`

---

## How to Run

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. (Optional) Run with MySQL
If using MySQL (e.g. XAMPP):
1. Start MySQL on `localhost:3306`.
2. Configure credentials in `config.py` or `.env` if different from root/empty password.
3. Import `database/schema.sql`:
   ```bash
   mysql -u root < database/schema.sql
   ```

### 3. Seed the Admin Account (Manual Seeding)
```bash
python seed_admin.py
```

### 4. Start the Web Application
```bash
python app.py
```
Open your browser at **http://127.0.0.1:5000**.

### 5. Run Automated Tests
```bash
python -m unittest tests/test_phase1.py -v
```
