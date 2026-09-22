import sqlite3
import math
import os
from flask import g
from config import Config

def haversine(lat1, lon1, lat2, lon2):
    """Calculate distance in kilometers between two sets of GPS coordinates using the Haversine formula."""
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return 9999.0
    try:
        lat1, lon1, lat2, lon2 = float(lat1), float(lon1), float(lat2), float(lon2)
        r = 6371.0  # Earth's radius in kilometers
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2.0) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon / 2.0) ** 2)
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return round(r * c, 2)
    except Exception:
        return 9999.0

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(Config.DATABASE_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
        # Register custom Haversine distance function in SQLite
        g.db.create_function("haversine", 4, haversine)
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def query_db(query, args=(), one=False):
    db = get_db()
    cur = db.execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def execute_db(query, args=(), commit=True):
    db = get_db()
    cur = db.execute(query, args)
    if commit:
        db.commit()
    last_id = cur.lastrowid
    cur.close()
    return last_id

def init_db():
    os.makedirs(os.path.dirname(Config.DATABASE_PATH), exist_ok=True)
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    
    conn = sqlite3.connect(Config.DATABASE_PATH)
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON")

    # 1. Users table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('customer', 'provider', 'pharmacy', 'admin')),
        latitude REAL DEFAULT 17.3850,
        longitude REAL DEFAULT 78.4867,
        address TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Services category catalog
    cur.execute("""
    CREATE TABLE IF NOT EXISTS services (
        service_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT NOT NULL UNIQUE,
        icon TEXT NOT NULL,
        telugu_name TEXT,
        hindi_name TEXT,
        base_price REAL DEFAULT 150.0,
        description TEXT
    );
    """)

    # 3. Providers table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS providers (
        provider_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL UNIQUE,
        category TEXT NOT NULL,
        experience_years INTEGER DEFAULT 2,
        charges_per_hr REAL DEFAULT 200.0,
        availability TEXT DEFAULT 'Available' CHECK(availability IN ('Available', 'Busy', 'Offline')),
        verification_status TEXT DEFAULT 'Pending' CHECK(verification_status IN ('Pending', 'Verified', 'Rejected', 'Suspended')),
        latitude REAL DEFAULT 17.3850,
        longitude REAL DEFAULT 78.4867,
        address TEXT,
        bio TEXT,
        rating REAL DEFAULT 5.0,
        rating_count INTEGER DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    );
    """)

    # 4. Bookings table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS bookings (
        booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        provider_id INTEGER NOT NULL,
        service_id INTEGER,
        booking_date TEXT NOT NULL,
        booking_time TEXT NOT NULL,
        status TEXT DEFAULT 'Requested' CHECK(status IN ('Requested', 'Accepted', 'Provider Assigned', 'On the Way', 'Service Started', 'Completed', 'Rejected')),
        description TEXT,
        customer_name TEXT,
        customer_phone TEXT,
        address TEXT,
        latitude REAL,
        longitude REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
        FOREIGN KEY (provider_id) REFERENCES providers(provider_id) ON DELETE CASCADE,
        FOREIGN KEY (service_id) REFERENCES services(service_id)
    );
    """)

    # 5. Pharmacies table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS pharmacies (
        pharmacy_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL UNIQUE,
        name TEXT NOT NULL,
        phone TEXT NOT NULL,
        address TEXT NOT NULL,
        latitude REAL DEFAULT 17.3850,
        longitude REAL DEFAULT 78.4867,
        verification_status TEXT DEFAULT 'Verified' CHECK(verification_status IN ('Pending', 'Verified', 'Rejected', 'Suspended')),
        timings TEXT DEFAULT '8:00 AM - 10:00 PM',
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    );
    """)

    # 6. Medicines catalog
    cur.execute("""
    CREATE TABLE IF NOT EXISTS medicines (
        medicine_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        telugu_name TEXT,
        hindi_name TEXT,
        strength TEXT NOT NULL,
        category TEXT NOT NULL,
        description TEXT,
        icon TEXT DEFAULT 'fa-pills'
    );
    """)

    # 7. Medicine Inventory (Pharmacy reported availability)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS medicine_inventory (
        inventory_id INTEGER PRIMARY KEY AUTOINCREMENT,
        pharmacy_id INTEGER NOT NULL,
        medicine_id INTEGER NOT NULL,
        availability TEXT DEFAULT 'Available' CHECK(availability IN ('Available', 'Low Stock', 'Unavailable')),
        price REAL DEFAULT 25.0,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        notes TEXT,
        FOREIGN KEY (pharmacy_id) REFERENCES pharmacies(pharmacy_id) ON DELETE CASCADE,
        FOREIGN KEY (medicine_id) REFERENCES medicines(medicine_id) ON DELETE CASCADE,
        UNIQUE(pharmacy_id, medicine_id)
    );
    """)

    # 8. Medicine Requests (Community broadcast)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS medicine_requests (
        request_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        medicine_name TEXT NOT NULL,
        strength TEXT,
        quantity TEXT DEFAULT '1 strip',
        prescription_image TEXT,
        customer_phone TEXT,
        address TEXT,
        latitude REAL,
        longitude REAL,
        status TEXT DEFAULT 'Broadcasted' CHECK(status IN ('Broadcasted', 'Responded', 'Fulfilled', 'Closed')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    );
    """)

    # 9. Pharmacy Responses to Requests
    cur.execute("""
    CREATE TABLE IF NOT EXISTS pharmacy_responses (
        response_id INTEGER PRIMARY KEY AUTOINCREMENT,
        request_id INTEGER NOT NULL,
        pharmacy_id INTEGER NOT NULL,
        response_status TEXT NOT NULL CHECK(response_status IN ('Available', 'Not Available', 'Expected Later')),
        notes TEXT,
        responded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (request_id) REFERENCES medicine_requests(request_id) ON DELETE CASCADE,
        FOREIGN KEY (pharmacy_id) REFERENCES pharmacies(pharmacy_id) ON DELETE CASCADE,
        UNIQUE(request_id, pharmacy_id)
    );
    """)

    # 10. Reviews table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS reviews (
        review_id INTEGER PRIMARY KEY AUTOINCREMENT,
        booking_id INTEGER NOT NULL UNIQUE,
        user_id INTEGER NOT NULL,
        provider_id INTEGER NOT NULL,
        rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
        comment TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (booking_id) REFERENCES bookings(booking_id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
        FOREIGN KEY (provider_id) REFERENCES providers(provider_id) ON DELETE CASCADE
    );
    """)

    # 11. Complaints table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS complaints (
        complaint_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        target_type TEXT NOT NULL CHECK(target_type IN ('Provider', 'Pharmacy', 'Platform')),
        target_id INTEGER,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        status TEXT DEFAULT 'Submitted' CHECK(status IN ('Submitted', 'Investigating', 'Resolved', 'Dismissed')),
        admin_notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    );
    """)

    # 12. Notifications table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        message TEXT NOT NULL,
        is_read INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    );
    """)

    conn.commit()
    conn.close()
    print("Database initialized successfully.")

if __name__ == '__main__':
    init_db()
