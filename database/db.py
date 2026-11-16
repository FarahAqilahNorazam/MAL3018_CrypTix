import os
import sqlite3
import hashlib
from config import Config

# Try importing pymysql for MySQL connectivity
try:
    import pymysql
    import pymysql.cursors
    PYMYSQL_AVAILABLE = True
except ImportError:
    PYMYSQL_AVAILABLE = False

_use_sqlite_fallback = False

def get_db_connection():
    """
    Returns an active database connection.
    Attempts connection to MySQL (PyMySQL) first.
    If MySQL server is offline or unavailable, automatically falls back to SQLite
    to ensure immediate development and test readiness.
    """
    global _use_sqlite_fallback

    if not _use_sqlite_fallback and PYMYSQL_AVAILABLE:
        try:
            conn_init = pymysql.connect(
                host=Config.MYSQL_HOST,
                port=Config.MYSQL_PORT,
                user=Config.MYSQL_USER,
                password=Config.MYSQL_PASSWORD,
                cursorclass=pymysql.cursors.DictCursor,
                connect_timeout=3
            )
            with conn_init.cursor() as cursor:
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{Config.MYSQL_DB}` CHARACTER SET utf8mb4;")
            conn_init.commit()
            conn_init.close()

            connection = pymysql.connect(
                host=Config.MYSQL_HOST,
                port=Config.MYSQL_PORT,
                user=Config.MYSQL_USER,
                password=Config.MYSQL_PASSWORD,
                database=Config.MYSQL_DB,
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=True
            )
            return connection, 'mysql'
        except Exception as e:
            print(f"[Database Notice] MySQL connection failed ({e}). Falling back to local SQLite database.")
            _use_sqlite_fallback = True

    # SQLite fallback mode
    db_path = os.path.join(os.path.dirname(__file__), '..', 'cryptix_local.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn, 'sqlite'


def init_db():
    """Initializes and migrates users, events, and tickets tables on server startup."""
    conn, db_type = get_db_connection()
    try:
        cursor = conn.cursor()
        if db_type == 'mysql':
            # 1. Users Table (with Phase 3 mykad_hash and masked_ic)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(120) NOT NULL UNIQUE,
                    password_hash VARCHAR(255) NOT NULL,
                    mykad_hash VARCHAR(64) NOT NULL COMMENT 'SHA-256 digest',
                    masked_ic VARCHAR(20) NOT NULL COMMENT 'Privacy masked format e.g. ******--1234',
                    pdpa_consent TINYINT(1) NOT NULL DEFAULT 1,
                    role ENUM('Admin', 'Customer') NOT NULL DEFAULT 'Customer',
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_user_email (email),
                    INDEX idx_user_mykad_hash (mykad_hash)
                ) ENGINE=InnoDB;
            """)
            # 2. Events Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    event_id INT AUTO_INCREMENT PRIMARY KEY,
                    event_title VARCHAR(150) NOT NULL,
                    description TEXT NULL,
                    event_date DATETIME NOT NULL,
                    venue VARCHAR(150) NOT NULL,
                    total_capacity INT NOT NULL,
                    available_capacity INT NOT NULL,
                    ticket_price DECIMAL(10, 2) NOT NULL,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_event_date (event_date)
                ) ENGINE=InnoDB;
            """)
            # 3. Tickets Table (with mykad_hash identity binding)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tickets (
                    ticket_id INT AUTO_INCREMENT PRIMARY KEY,
                    event_id INT NOT NULL,
                    user_id INT NOT NULL,
                    mykad_hash VARCHAR(64) NOT NULL,
                    seat_number VARCHAR(50) NOT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'SOLD',
                    purchased_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT fk_tickets_event FOREIGN KEY (event_id) REFERENCES events (event_id) ON DELETE CASCADE,
                    CONSTRAINT fk_tickets_user FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
                    INDEX idx_tickets_user_event (user_id, event_id),
                    INDEX idx_tickets_mykad_hash (mykad_hash),
                    INDEX idx_tickets_status (status)
                ) ENGINE=InnoDB;
            """)
        else:
            # SQLite Mode
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    mykad_hash TEXT NOT NULL DEFAULT '',
                    masked_ic TEXT NOT NULL DEFAULT '',
                    pdpa_consent INTEGER NOT NULL DEFAULT 1,
                    role TEXT NOT NULL DEFAULT 'Customer',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_title TEXT NOT NULL,
                    description TEXT,
                    event_date TEXT NOT NULL,
                    venue TEXT NOT NULL,
                    total_capacity INTEGER NOT NULL,
                    available_capacity INTEGER NOT NULL,
                    ticket_price REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tickets (
                    ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    mykad_hash TEXT NOT NULL DEFAULT '',
                    seat_number TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'SOLD',
                    purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (event_id) REFERENCES events (event_id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
                );
            """)

            # SQLite Column Migrations (in case tables existed before Phase 3)
            cursor.execute("PRAGMA table_info(users)")
            user_cols = [col[1] for col in cursor.fetchall()]
            if 'mykad_hash' not in user_cols:
                cursor.execute("ALTER TABLE users ADD COLUMN mykad_hash TEXT NOT NULL DEFAULT ''")
            if 'masked_ic' not in user_cols:
                cursor.execute("ALTER TABLE users ADD COLUMN masked_ic TEXT NOT NULL DEFAULT ''")

            cursor.execute("PRAGMA table_info(tickets)")
            ticket_cols = [col[1] for col in cursor.fetchall()]
            if 'mykad_hash' not in ticket_cols:
                cursor.execute("ALTER TABLE tickets ADD COLUMN mykad_hash TEXT NOT NULL DEFAULT ''")

            conn.commit()

        _seed_initial_events_if_empty(conn, db_type)
    finally:
        conn.close()


def _seed_initial_events_if_empty(conn, db_type):
    """Populates realistic initial concert events if the events table is empty."""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as cnt FROM events")
    res = cursor.fetchone()
    count = res['cnt'] if isinstance(res, dict) else res[0]
    
    if count == 0:
        sample_events = [
            (
                "Coldplay: Music of the Spheres Tour",
                "Coldplay live in Kuala Lumpur! Experience the record-breaking global tour with sustainable stadium production and an electrifying light experience.",
                "2026-11-22 20:00:00",
                "National Stadium Bukit Jalil, Kuala Lumpur",
                50000,
                50000,
                288.00
            ),
            (
                "Sunset Indie Fest 2026",
                "Featuring 12 independent Southeast Asian artists in an intimate sunset amphitheater showcase with acoustic stages.",
                "2026-12-15 17:30:00",
                "Merdeka Stadium, Kuala Lumpur",
                15000,
                15000,
                160.00
            ),
            (
                "Ed Sheeran: Mathematics + - = ÷ Tour",
                "Immersive 360-degree in-the-round stage setup featuring fan favorites and acoustic masterpieces live in Malaysia.",
                "2027-01-08 20:00:00",
                "Axiata Arena, Bukit Jalil",
                12000,
                12000,
                250.00
            )
        ]
        sql = """
            INSERT INTO events (event_title, description, event_date, venue, total_capacity, available_capacity, ticket_price)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """ if db_type == 'mysql' else """
            INSERT INTO events (event_title, description, event_date, venue, total_capacity, available_capacity, ticket_price)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        for ev in sample_events:
            cursor.execute(sql, ev)
        if db_type == 'sqlite':
            conn.commit()
        print("[Database Notice] Initial concert events seeded successfully.")


# =====================================================================
# USER CRUD FUNCTIONS (Phase 1 & Phase 3)
# =====================================================================

def get_user_by_email(email):
    """Retrieve user dictionary by unique email."""
    conn, db_type = get_db_connection()
    try:
        cursor = conn.cursor()
        query = "SELECT user_id, name, email, password_hash, mykad_hash, masked_ic, pdpa_consent, role, created_at FROM users WHERE email = %s" if db_type == 'mysql' else \
                "SELECT user_id, name, email, password_hash, mykad_hash, masked_ic, pdpa_consent, role, created_at FROM users WHERE email = ?"
        cursor.execute(query, (email.strip().lower(),))
        row = cursor.fetchone()
        if row and db_type == 'sqlite':
            return dict(row)
        return row
    finally:
        conn.close()


def get_user_by_id(user_id):
    """Retrieve user dictionary by primary key user_id."""
    conn, db_type = get_db_connection()
    try:
        cursor = conn.cursor()
        query = "SELECT user_id, name, email, password_hash, mykad_hash, masked_ic, pdpa_consent, role, created_at FROM users WHERE user_id = %s" if db_type == 'mysql' else \
                "SELECT user_id, name, email, password_hash, mykad_hash, masked_ic, pdpa_consent, role, created_at FROM users WHERE user_id = ?"
        cursor.execute(query, (user_id,))
        row = cursor.fetchone()
        if row and db_type == 'sqlite':
            return dict(row)
        return row
    finally:
        conn.close()


def get_user_by_mykad_hash(mykad_hash):
    """Retrieve user by unique SHA-256 MyKad token hash."""
    if not mykad_hash:
        return None
    conn, db_type = get_db_connection()
    try:
        cursor = conn.cursor()
        query = "SELECT user_id, name, email, password_hash, mykad_hash, masked_ic, pdpa_consent, role, created_at FROM users WHERE mykad_hash = %s" if db_type == 'mysql' else \
                "SELECT user_id, name, email, password_hash, mykad_hash, masked_ic, pdpa_consent, role, created_at FROM users WHERE mykad_hash = ?"
        cursor.execute(query, (mykad_hash.strip(),))
        row = cursor.fetchone()
        if row and db_type == 'sqlite':
            return dict(row)
        return row
    finally:
        conn.close()


def create_customer_user(name, email, password_hash, mykad_hash, masked_ic, pdpa_consent=True):
    """
    Creates a new user account with SHA-256 identity tokenization.
    CRITICAL SECURITY RULES:
    1. Raw MyKad is NEVER stored in database.
    2. Only irreversible SHA-256 digest and masked format (******-**-1234) are saved.
    3. Role is strictly forced to 'Customer'.
    """
    conn, db_type = get_db_connection()
    try:
        cursor = conn.cursor()
        consent_val = 1 if pdpa_consent else 0
        role_val = 'Customer'
        if db_type == 'mysql':
            cursor.execute("""
                INSERT INTO users (name, email, password_hash, mykad_hash, masked_ic, pdpa_consent, role)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (name.strip(), email.strip().lower(), password_hash, mykad_hash, masked_ic, consent_val, role_val))
            user_id = cursor.lastrowid
        else:
            cursor.execute("""
                INSERT INTO users (name, email, password_hash, mykad_hash, masked_ic, pdpa_consent, role)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (name.strip(), email.strip().lower(), password_hash, mykad_hash, masked_ic, consent_val, role_val))
            conn.commit()
            user_id = cursor.lastrowid
        return user_id
    finally:
        conn.close()


def seed_admin_user(name, email, password_hash):
    """Seeds the default system administrator account with dummy identity token."""
    conn, db_type = get_db_connection()
    try:
        cursor = conn.cursor()
        query_check = "SELECT user_id FROM users WHERE email = %s" if db_type == 'mysql' else \
                      "SELECT user_id FROM users WHERE email = ?"
        cursor.execute(query_check, (email.strip().lower(),))
        existing = cursor.fetchone()

        if not existing:
            dummy_admin_hash = hashlib.sha256(b"000000000000").hexdigest()
            dummy_admin_mask = "******-**-0000"
            query_insert = """
                INSERT INTO users (name, email, password_hash, mykad_hash, masked_ic, pdpa_consent, role)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """ if db_type == 'mysql' else """
                INSERT INTO users (name, email, password_hash, mykad_hash, masked_ic, pdpa_consent, role)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(query_insert, (name, email.strip().lower(), password_hash, dummy_admin_hash, dummy_admin_mask, 1, 'Admin'))
            if db_type == 'sqlite':
                conn.commit()
            print(f"[Admin Seed] Successfully initialized admin account: {email}")
            return True
        return False
    finally:
        conn.close()


def get_all_users():
    """Retrieve all registered users with masked identity tokens."""
    conn, db_type = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, name, email, role, mykad_hash, masked_ic, pdpa_consent, created_at FROM users ORDER BY user_id DESC")
        rows = cursor.fetchall()
        if db_type == 'sqlite':
            return [dict(r) for r in rows]
        return rows
    finally:
        conn.close()


# =====================================================================
# EVENT CRUD FUNCTIONS (Phase 2)
# =====================================================================

def create_event(event_title, description, event_date, venue, total_capacity, ticket_price):
    """Creates a new concert event."""
    conn, db_type = get_db_connection()
    try:
        cursor = conn.cursor()
        total_cap = int(total_capacity)
        available_cap = total_cap
        price = float(ticket_price)

        if db_type == 'mysql':
            cursor.execute("""
                INSERT INTO events (event_title, description, event_date, venue, total_capacity, available_capacity, ticket_price)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (event_title.strip(), description.strip(), event_date, venue.strip(), total_cap, available_cap, price))
            event_id = cursor.lastrowid
        else:
            cursor.execute("""
                INSERT INTO events (event_title, description, event_date, venue, total_capacity, available_capacity, ticket_price)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (event_title.strip(), description.strip(), str(event_date), venue.strip(), total_cap, available_cap, price))
            conn.commit()
            event_id = cursor.lastrowid
        return event_id
    finally:
        conn.close()


def get_all_events():
    """Retrieves all concert events ordered by date."""
    conn, db_type = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT event_id, event_title, description, event_date, venue, total_capacity, available_capacity, ticket_price, created_at 
            FROM events 
            ORDER BY event_date ASC
        """)
        rows = cursor.fetchall()
        if db_type == 'sqlite':
            return [dict(r) for r in rows]
        return rows
    finally:
        conn.close()


def get_event_by_id(event_id):
    """Retrieves a single event by ID."""
    conn, db_type = get_db_connection()
    try:
        cursor = conn.cursor()
        query = "SELECT * FROM events WHERE event_id = %s" if db_type == 'mysql' else "SELECT * FROM events WHERE event_id = ?"
        cursor.execute(query, (event_id,))
        row = cursor.fetchone()
        if row and db_type == 'sqlite':
            return dict(row)
        return row
    finally:
        conn.close()


def update_event(event_id, event_title, description, event_date, venue, total_capacity, ticket_price):
    """Updates an existing concert event."""
    conn, db_type = get_db_connection()
    try:
        cursor = conn.cursor()
        current_event = get_event_by_id(event_id)
        if not current_event:
            return False

        tickets_sold = int(current_event['total_capacity']) - int(current_event['available_capacity'])
        new_total_cap = int(total_capacity)
        new_avail_cap = max(0, new_total_cap - tickets_sold)
        price = float(ticket_price)

        if db_type == 'mysql':
            cursor.execute("""
                UPDATE events 
                SET event_title = %s, description = %s, event_date = %s, venue = %s, 
                    total_capacity = %s, available_capacity = %s, ticket_price = %s
                WHERE event_id = %s
            """, (event_title.strip(), description.strip(), event_date, venue.strip(), new_total_cap, new_avail_cap, price, event_id))
        else:
            cursor.execute("""
                UPDATE events 
                SET event_title = ?, description = ?, event_date = ?, venue = ?, 
                    total_capacity = ?, available_capacity = ?, ticket_price = ?
                WHERE event_id = ?
            """, (event_title.strip(), description.strip(), str(event_date), venue.strip(), new_total_cap, new_avail_cap, price, event_id))
            conn.commit()
        return True
    finally:
        conn.close()


def delete_event(event_id):
    """Deletes an event and its associated tickets."""
    conn, db_type = get_db_connection()
    try:
        cursor = conn.cursor()
        query = "DELETE FROM events WHERE event_id = %s" if db_type == 'mysql' else "DELETE FROM events WHERE event_id = ?"
        cursor.execute(query, (event_id,))
        if db_type == 'sqlite':
            conn.commit()
        return True
    finally:
        conn.close()


# =====================================================================
# TICKET PURCHASING & IDENTITY BINDING (Phase 2 & Phase 3)
# =====================================================================

def get_user_ticket_count_for_event(user_id, event_id):
    """Enforces Rule: Maximum 4 tickets per user per event."""
    conn, db_type = get_db_connection()
    try:
        cursor = conn.cursor()
        query = "SELECT COUNT(*) as count FROM tickets WHERE user_id = %s AND event_id = %s AND status != 'REVOKED'" if db_type == 'mysql' else \
                "SELECT COUNT(*) as count FROM tickets WHERE user_id = ? AND event_id = ? AND status != 'REVOKED'"
        cursor.execute(query, (user_id, event_id))
        row = cursor.fetchone()
        return row['count'] if isinstance(row, dict) else row[0]
    finally:
        conn.close()


def purchase_tickets(event_id, user_id, quantity):
    """
    Simulates ticket checkout and identity binding.
    Phase 3: Binds ticket ownership to purchaser's user_id AND irreversible mykad_hash.
    """
    quantity = int(quantity)
    if quantity <= 0:
        return False, "Quantity must be at least 1."

    conn, db_type = get_db_connection()
    try:
        cursor = conn.cursor()

        # 1. Fetch current event details
        query_event = "SELECT * FROM events WHERE event_id = %s" if db_type == 'mysql' else "SELECT * FROM events WHERE event_id = ?"
        cursor.execute(query_event, (event_id,))
        event = cursor.fetchone()
        if not event:
            return False, "Concert event not found."
        if db_type == 'sqlite':
            event = dict(event)

        avail = int(event['available_capacity'])
        total = int(event['total_capacity'])

        if avail < quantity:
            return False, f"Sorry, only {avail} tickets are remaining for this concert."

        # 2. Check User Limit: Max 4 tickets per event per user
        query_user_count = "SELECT COUNT(*) as cnt FROM tickets WHERE user_id = %s AND event_id = %s AND status != 'REVOKED'" if db_type == 'mysql' else \
                           "SELECT COUNT(*) as cnt FROM tickets WHERE user_id = ? AND event_id = ? AND status != 'REVOKED'"
        cursor.execute(query_user_count, (user_id, event_id))
        res = cursor.fetchone()
        current_user_tickets = res['cnt'] if isinstance(res, dict) else res[0]

        if current_user_tickets + quantity > 4:
            allowed = max(0, 4 - current_user_tickets)
            return False, f"Anti-Scalping Rule Violation: Maximum 4 tickets per user. You already hold {current_user_tickets} ticket(s) and can only buy up to {allowed} more."

        # 3. Fetch user's mykad_hash for cryptographic identity binding
        query_user = "SELECT mykad_hash FROM users WHERE user_id = %s" if db_type == 'mysql' else "SELECT mykad_hash FROM users WHERE user_id = ?"
        cursor.execute(query_user, (user_id,))
        user_row = cursor.fetchone()
        mykad_hash = user_row['mykad_hash'] if isinstance(user_row, dict) else (user_row[0] if user_row else "")

        # 4. Generate sequential seat numbers and bind mykad_hash
        tickets_already_sold = total - avail
        created_tickets = []

        for i in range(quantity):
            seat_seq = tickets_already_sold + i + 1
            seat_number = f"CAT1-A{seat_seq:04d}"

            if db_type == 'mysql':
                cursor.execute("""
                    INSERT INTO tickets (event_id, user_id, mykad_hash, seat_number, status)
                    VALUES (%s, %s, %s, %s, 'SOLD')
                """, (event_id, user_id, mykad_hash, seat_number))
                t_id = cursor.lastrowid
            else:
                cursor.execute("""
                    INSERT INTO tickets (event_id, user_id, mykad_hash, seat_number, status)
                    VALUES (?, ?, ?, ?, 'SOLD')
                """, (event_id, user_id, mykad_hash, seat_number))
                t_id = cursor.lastrowid
            created_tickets.append({"ticket_id": t_id, "seat_number": seat_number, "mykad_hash": mykad_hash})

        # 5. Reduce available capacity
        new_avail = avail - quantity
        update_cap_sql = "UPDATE events SET available_capacity = %s WHERE event_id = %s" if db_type == 'mysql' else \
                         "UPDATE events SET available_capacity = ? WHERE event_id = ?"
        cursor.execute(update_cap_sql, (new_avail, event_id))

        if db_type == 'sqlite':
            conn.commit()

        return True, created_tickets
    except Exception as e:
        if db_type == 'sqlite':
            conn.rollback()
        return False, f"Database transaction failed: {str(e)}"
    finally:
        conn.close()


def get_tickets_by_user_id(user_id):
    """
    Retrieves all tickets owned by a user, joined with event details and user's masked_ic.
    Never exposes raw MyKad.
    """
    conn, db_type = get_db_connection()
    try:
        cursor = conn.cursor()
        query = """
            SELECT t.ticket_id, t.event_id, t.user_id, t.mykad_hash, t.seat_number, t.status, t.purchased_at,
                   e.event_title, e.event_date, e.venue, e.ticket_price,
                   u.masked_ic
            FROM tickets t
            JOIN events e ON t.event_id = e.event_id
            JOIN users u ON t.user_id = u.user_id
            WHERE t.user_id = %s
            ORDER BY t.purchased_at DESC
        """ if db_type == 'mysql' else """
            SELECT t.ticket_id, t.event_id, t.user_id, t.mykad_hash, t.seat_number, t.status, t.purchased_at,
                   e.event_title, e.event_date, e.venue, e.ticket_price,
                   u.masked_ic
            FROM tickets t
            JOIN events e ON t.event_id = e.event_id
            JOIN users u ON t.user_id = u.user_id
            WHERE t.user_id = ?
            ORDER BY t.purchased_at DESC
        """
        cursor.execute(query, (user_id,))
        rows = cursor.fetchall()
        if db_type == 'sqlite':
            return [dict(r) for r in rows]
        return rows
    finally:
        conn.close()


def get_all_tickets():
    """Retrieves all tickets across all events with masked attendee identities."""
    conn, db_type = get_db_connection()
    try:
        cursor = conn.cursor()
        query = """
            SELECT t.ticket_id, t.mykad_hash, t.seat_number, t.status, t.purchased_at,
                   e.event_title, e.venue, e.ticket_price,
                   u.name as buyer_name, u.email as buyer_email, u.masked_ic
            FROM tickets t
            JOIN events e ON t.event_id = e.event_id
            JOIN users u ON t.user_id = u.user_id
            ORDER BY t.purchased_at DESC
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        if db_type == 'sqlite':
            return [dict(r) for r in rows]
        return rows
    finally:
        conn.close()


def get_ticket_statistics():
    """Calculates overall box office statistics."""
    conn, db_type = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as total_events, SUM(total_capacity) as total_cap, SUM(available_capacity) as avail_cap FROM events")
        ev_stats = cursor.fetchone()
        if db_type == 'sqlite' and ev_stats:
            ev_stats = dict(ev_stats)

        cursor.execute("SELECT COUNT(*) as total_sold FROM tickets WHERE status = 'SOLD'")
        t_stats = cursor.fetchone()
        if db_type == 'sqlite' and t_stats:
            t_stats = dict(t_stats)

        cursor.execute("SELECT COUNT(*) as total_users FROM users WHERE role = 'Customer'")
        u_stats = cursor.fetchone()
        if db_type == 'sqlite' and u_stats:
            u_stats = dict(u_stats)

        total_events = ev_stats['total_events'] or 0 if ev_stats else 0
        total_capacity = ev_stats['total_cap'] or 0 if ev_stats else 0
        avail_capacity = ev_stats['avail_cap'] or 0 if ev_stats else 0
        tickets_sold = t_stats['total_sold'] or 0 if t_stats else 0
        total_fans = u_stats['total_users'] or 0 if u_stats else 0

        return {
            "total_events": total_events,
            "total_capacity": total_capacity,
            "available_capacity": avail_capacity,
            "tickets_sold": tickets_sold,
            "total_fans": total_fans
        }
    finally:
        conn.close()
