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
    os.makedirs(Config.PROBLEM_UPLOAD_FOLDER, exist_ok=True)
    
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
        latitude REAL DEFAULT 16.3486,
        longitude REAL DEFAULT 81.0442,
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
        latitude REAL DEFAULT 16.3486,
        longitude REAL DEFAULT 81.0442,
        address TEXT,
        bio TEXT,
        rating REAL DEFAULT 5.0,
        rating_count INTEGER DEFAULT 0,
        completed_jobs_count INTEGER DEFAULT 0,
        years_on_platform INTEGER DEFAULT 1,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    );
    """)

    # 4. Bookings table (with problem_image for 'Show the Problem')
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
        problem_image TEXT,
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
        latitude REAL DEFAULT 16.3486,
        longitude REAL DEFAULT 81.0442,
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

    # ==================== SKILLSHARE & COMMUNITY EXTENSIONS ====================

    # 13. Skill Categories
    cur.execute("""
    CREATE TABLE IF NOT EXISTS skill_categories (
        skill_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        category_code TEXT NOT NULL UNIQUE,
        icon TEXT NOT NULL,
        telugu_name TEXT,
        hindi_name TEXT,
        description TEXT
    );
    """)

    # 14. Mentor Profiles (Service Providers who also teach)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS mentor_profiles (
        mentor_id INTEGER PRIMARY KEY AUTOINCREMENT,
        provider_id INTEGER NOT NULL UNIQUE,
        bio TEXT,
        experience_years INTEGER DEFAULT 2,
        teaching_mode TEXT DEFAULT 'In-Person',
        languages TEXT DEFAULT 'Telugu, English',
        is_community_free INTEGER DEFAULT 0,
        verification_status TEXT DEFAULT 'Verified' CHECK(verification_status IN ('Pending', 'Verified', 'Suspended')),
        total_learners INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (provider_id) REFERENCES providers(provider_id) ON DELETE CASCADE
    );
    """)

    # 15. Courses
    cur.execute("""
    CREATE TABLE IF NOT EXISTS courses (
        course_id INTEGER PRIMARY KEY AUTOINCREMENT,
        mentor_id INTEGER NOT NULL,
        skill_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        level TEXT DEFAULT 'Beginner' CHECK(level IN ('Beginner', 'Intermediate', 'Advanced')),
        duration TEXT DEFAULT '3 Days',
        fee REAL DEFAULT 0.0,
        mode TEXT DEFAULT 'In-Person',
        location TEXT,
        safety_instructions TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (mentor_id) REFERENCES mentor_profiles(mentor_id) ON DELETE CASCADE,
        FOREIGN KEY (skill_id) REFERENCES skill_categories(skill_id) ON DELETE CASCADE
    );
    """)

    # 16. Course Lessons
    cur.execute("""
    CREATE TABLE IF NOT EXISTS course_lessons (
        lesson_id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        content TEXT,
        video_url TEXT,
        image_url TEXT,
        safety_warning TEXT,
        lesson_order INTEGER DEFAULT 1,
        FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE
    );
    """)

    # 17. Enrollments
    cur.execute("""
    CREATE TABLE IF NOT EXISTS enrollments (
        enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        status TEXT DEFAULT 'Enrolled' CHECK(status IN ('Enrolled', 'In Progress', 'Completed', 'Dropped')),
        progress INTEGER DEFAULT 0,
        enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP,
        FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
        UNIQUE(course_id, user_id)
    );
    """)

    # 18. Lesson Completions Tracker
    cur.execute("""
    CREATE TABLE IF NOT EXISTS lesson_completions (
        completion_id INTEGER PRIMARY KEY AUTOINCREMENT,
        enrollment_id INTEGER NOT NULL,
        lesson_id INTEGER NOT NULL,
        completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (enrollment_id) REFERENCES enrollments(enrollment_id) ON DELETE CASCADE,
        FOREIGN KEY (lesson_id) REFERENCES course_lessons(lesson_id) ON DELETE CASCADE,
        UNIQUE(enrollment_id, lesson_id)
    );
    """)

    # 19. Skill Certificates (Official SevaSetu Course-Completion Certificate)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS skill_certificates (
        certificate_id INTEGER PRIMARY KEY AUTOINCREMENT,
        enrollment_id INTEGER NOT NULL UNIQUE,
        certificate_number TEXT NOT NULL UNIQUE,
        verification_code TEXT NOT NULL UNIQUE,
        issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (enrollment_id) REFERENCES enrollments(enrollment_id) ON DELETE CASCADE
    );
    """)

    # 20. Training Sessions (Community Group Workshops)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS training_sessions (
        session_id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_id INTEGER,
        mentor_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        date TEXT NOT NULL,
        time TEXT NOT NULL,
        location TEXT NOT NULL,
        capacity INTEGER DEFAULT 20,
        available_seats INTEGER DEFAULT 20,
        fee REAL DEFAULT 0.0,
        status TEXT DEFAULT 'Scheduled' CHECK(status IN ('Scheduled', 'Completed', 'Cancelled')),
        FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE SET NULL,
        FOREIGN KEY (mentor_id) REFERENCES mentor_profiles(mentor_id) ON DELETE CASCADE
    );
    """)

    # 21. Session Registrations
    cur.execute("""
    CREATE TABLE IF NOT EXISTS session_registrations (
        registration_id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        status TEXT DEFAULT 'Confirmed',
        registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (session_id) REFERENCES training_sessions(session_id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
        UNIQUE(session_id, user_id)
    );
    """)

    # 22. Skill Exchanges (Peer-to-Peer Barter: Teach A, Learn B)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS skill_exchanges (
        exchange_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        teach_skill TEXT NOT NULL,
        learn_skill TEXT NOT NULL,
        notes TEXT,
        status TEXT DEFAULT 'Active' CHECK(status IN ('Active', 'Matched', 'Closed')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    );
    """)

    # 23. Community Notices (Panchayat / Local Announcements)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS community_notices (
        notice_id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        category TEXT NOT NULL,
        content TEXT NOT NULL,
        date_effective TEXT,
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 24. Community Volunteers (Helpers for elderly / non-literate residents)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS volunteers (
        volunteer_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL UNIQUE,
        area TEXT NOT NULL,
        phone TEXT NOT NULL,
        skills_assisted TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    );
    """)

    # 25. User Skill Profiles (Learner to Local Work Pathway)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_skill_profiles (
        profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        skill_name TEXT NOT NULL,
        certificate_id INTEGER,
        is_available_for_work INTEGER DEFAULT 1,
        hourly_rate REAL DEFAULT 120.0,
        bio TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
        FOREIGN KEY (certificate_id) REFERENCES skill_certificates(certificate_id) ON DELETE SET NULL
    );
    """)

    conn.commit()
    conn.close()
    print("Database tables & SkillShare extensions initialized successfully.")

if __name__ == '__main__':
    init_db()
