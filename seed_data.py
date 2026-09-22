import sqlite3
import datetime
from werkzeug.security import generate_password_hash
from config import Config
from database import init_db

def seed_database():
    init_db()
    conn = sqlite3.connect(Config.DATABASE_PATH)
    cur = conn.cursor()

    # Clear existing data for clean seed
    tables = [
        "notifications", "complaints", "reviews", "pharmacy_responses",
        "medicine_requests", "medicine_inventory", "medicines",
        "pharmacies", "bookings", "providers", "services", "users"
    ]
    for table in tables:
        cur.execute(f"DELETE FROM {table};")

    print("Seeding Users...")
    users_data = [
        # Admin
        ("Admin Officer", "admin@localserve.com", "+91 9999900000", generate_password_hash("admin123"), "admin", 17.3850, 78.4867, "Panchayat Development Office, Main Road"),
        # Customer
        ("Venkata Rao", "customer@localserve.com", "+91 9876543210", generate_password_hash("pass123"), "customer", 17.3850, 78.4867, "House No. 4-21, Gandhi Nagar, Near Water Tank"),
        # Providers
        ("Ramesh Electrician", "ramesh@provider.com", "+91 9848012345", generate_password_hash("pass123"), "provider", 17.3910, 78.4910, "Plot 12, Substation Road, Shanti Nagar"),
        ("Suresh Plumber", "suresh@provider.com", "+91 9848023456", generate_password_hash("pass123"), "provider", 17.3780, 78.4810, "Shop 3, Bus Stand Complex"),
        ("Anand Carpenter", "anand@provider.com", "+91 9848034567", generate_password_hash("pass123"), "provider", 17.3895, 78.4750, "Wood Works Lane, Market Yard"),
        ("Ravi Mechanic", "ravi@provider.com", "+91 9848045678", generate_password_hash("pass123"), "provider", 17.3950, 78.4980, "National Highway Junction Garage"),
        ("Shiva Tech (Cooler/Fridge)", "shiva@provider.com", "+91 9848056789", generate_password_hash("pass123"), "provider", 17.3800, 78.4930, "Opp. Zilla Parishad High School"),
        # Pharmacies
        ("Balaji Medical & General Store", "balaji@pharmacy.com", "+91 9123456780", generate_password_hash("pass123"), "pharmacy", 17.3860, 78.4880, "Main Bazaar Cross Road, Near Community Hospital"),
        ("Sri Rama Gramin Pharmacy", "srirama@pharmacy.com", "+91 9123456781", generate_password_hash("pass123"), "pharmacy", 17.3790, 78.4790, "Old Post Office Building, Station Road"),
    ]

    cur.executemany("""
    INSERT INTO users (name, email, phone, password_hash, role, latitude, longitude, address)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    """, users_data)

    # Fetch User IDs
    cur.execute("SELECT user_id, email FROM users")
    user_map = {row[1]: row[0] for row in cur.fetchall()}

    print("Seeding Services...")
    services_data = [
        ("Electrician", "Electrician", "fa-bolt", "విద్యుత్ పనులు (ఎలక్ట్రీషియన్)", "बिजली मिस्त्री", 150.0, "Wiring, fan/motor repair, switch replacement, power trips"),
        ("Plumber", "Plumber", "fa-faucet-drip", "ప్లంబర్ (పైపుల మరమ్మత్తు)", "नल मिस्त्री / प्लंबर", 150.0, "Pipe leak, tap replacement, tank cleaning, motor connection"),
        ("Carpenter", "Carpenter", "fa-hammer", "వడ్రంగి (చెక్క పనులు)", "बढ़ई (लकड़ी का काम)", 200.0, "Door lock fixing, furniture repair, wooden frames"),
        ("Mechanic", "Mechanic", "fa-wrench", "మెకానిక్ (బైక్, ట్రాక్టర్, మోటార్)", "मैकेनिक (बाइक/ट्रैक्टर)", 180.0, "Two-wheeler, tractor, puncture, engine start, oil change"),
        ("Appliance Tech", "Appliance Repair", "fa-fan", "కూలర్, ఫ్రిజ్, ఫ్యాన్ రిపేర్", "कूलर, फ्रिज, पंखा मरम्मत", 200.0, "AC servicing, refrigerator gas, cooler fan, washing machine"),
        ("House Cleaner", "Cleaning", "fa-broom", "శుభ్రత పనులు (క్లీనింగ్)", "सफाई कर्मी", 250.0, "Deep home cleaning, water sump washing, yard clean"),
        ("Painter", "Painter", "fa-paint-roller", "పెయింటింగ్ పనులు", "रंगाई पुताई मिस्त्री", 300.0, "Wall whitewashing, weather coat, door polish"),
        ("TV & Mobile Tech", "Electronics", "fa-tv", "టీవీ, మొబైల్ రిపేర్", "टीवी/मोबाइल रिपेयर", 150.0, "LED TV display, DTH setup, mobile charging socket repair")
    ]

    cur.executemany("""
    INSERT INTO services (name, category, icon, telugu_name, hindi_name, base_price, description)
    VALUES (?, ?, ?, ?, ?, ?, ?);
    """, services_data)

    print("Seeding Providers...")
    providers_data = [
        (user_map["ramesh@provider.com"], "Electrician", 8, 150.0, "Available", "Verified", 17.3910, 78.4910, "Plot 12, Substation Road", "Certified electrician with 8 years experience in house wiring and farm pump starters.", 4.9, 38),
        (user_map["suresh@provider.com"], "Plumber", 5, 140.0, "Available", "Verified", 17.3780, 78.4810, "Shop 3, Bus Stand Complex", "Quick plumbing repairs, drainage clearance and submersible motor fitting.", 4.8, 25),
        (user_map["anand@provider.com"], "Carpenter", 10, 200.0, "Available", "Verified", 17.3895, 78.4750, "Wood Works Lane", "Expert wood artisan for door repairs, cot/almirah making and lock fixes.", 4.7, 19),
        (user_map["ravi@provider.com"], "Mechanic", 12, 180.0, "Available", "Verified", 17.3950, 78.4980, "Highway Junction", "On-spot puncture repair, tractor hydraulic checks, bike engine troubleshooting.", 4.9, 52),
        (user_map["shiva@provider.com"], "Appliance Repair", 6, 200.0, "Available", "Verified", 17.3800, 78.4930, "Opp ZP High School", "Refrigerator cooling repair, ceiling fan winding, room cooler setup.", 4.6, 14),
    ]

    cur.executemany("""
    INSERT INTO providers (user_id, category, experience_years, charges_per_hr, availability, verification_status, latitude, longitude, address, bio, rating, rating_count)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, providers_data)

    print("Seeding Pharmacies...")
    pharmacies_data = [
        (user_map["balaji@pharmacy.com"], "Balaji Medical & General Store", "+91 9123456780", "Main Bazaar Cross Road, Near Community Hospital", 17.3860, 78.4880, "Verified", "7:30 AM - 10:30 PM"),
        (user_map["srirama@pharmacy.com"], "Sri Rama Gramin Pharmacy", "+91 9123456781", "Old Post Office Building, Station Road", 17.3790, 78.4790, "Verified", "8:00 AM - 9:30 PM")
    ]

    cur.executemany("""
    INSERT INTO pharmacies (user_id, name, phone, address, latitude, longitude, verification_status, timings)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    """, pharmacies_data)

    print("Seeding Medicines...")
    medicines_data = [
        ("Paracetamol 500mg", "పారాసిటమాల్ 500 మి.గ్రా", "पैरासिटामोल 500 मि.ग्रा", "500mg", "Fever & Pain", "Effective for fever, headache, body aches and joint pain.", "fa-tablets"),
        ("ORS Sachet", "ఓ.ఆర్.ఎస్ ప్యాకెట్", "ओआरएस घोल पैकेट", "21.8g", "Rehydration", "Oral Rehydration Salts for diarrhea, dehydration and fatigue.", "fa-glass-water"),
        ("Cetirizine 10mg", "సెటిరిజైన్ 10 మి.గ్రా", "सिट्रिजिन 10 मि.ग्रा", "10mg", "Cold & Allergy", "Fast relief from runny nose, sneezing, itching and allergies.", "fa-capsules"),
        ("Azithromycin 500mg", "అజిత్రోమైసిన్ 500 మి.గ్రా", "एजिथ्रोमाइसिन 500 मि.ग्रा", "500mg", "Antibiotic", "Prescription antibiotic for respiratory and throat bacterial infections.", "fa-prescription-bottle"),
        ("Cough Syrup DX", "దగ్గు సిరప్ డిఎక్స్", "खांसी की दवाई सिरप", "100ml", "Cough Relief", "Relieves dry cough, allergic throat tickle and chest irritation.", "fa-bottle-droplet"),
        ("Pantoprazole 40mg", "పాంటోప్రజోల్ 40 మి.గ్రా", "पैंटोपेराज़ोल 40 मि.ग्रा", "40mg", "Acidity & Gas", "Relieves stomach burning, acid reflux, heartburn and indigestion.", "fa-pills"),
        ("Metformin 500mg", "మెట్ఫార్మిన్ 500 మి.గ్రా", "मेटफॉर्मिन 500 मि.ग्रा", "500mg", "Diabetes", "Controls blood sugar level for Type 2 Diabetes patients.", "fa-tablets"),
        ("Dettol Antiseptic Liquid", "డెట్టాల్ యాంటిసెప్టిక్", "डेटॉल लिक्विड", "100ml", "First Aid", "Cleans cuts, bruises, abrasions and minor skin infections.", "fa-shield-halved"),
        ("Amoxicillin 500mg", "అమోక్సిసిలిన్ 500 మి.గ్రా", "एमोक्सिसिलिन 500 मि.ग्रा", "500mg", "Antibiotic", "Common antibiotic for dental, ear, chest and skin infections.", "fa-pills"),
        ("Diclofenac Gel", "నొప్పి నివారణ జెల్ (డైక్లోఫెనాక్)", "दर्द निवारक जेल", "30g", "Pain Relief", "Fast pain relief ointment for backache, neck sprain and knee pain.", "fa-hand-dots")
    ]

    cur.executemany("""
    INSERT INTO medicines (name, telugu_name, hindi_name, strength, category, description, icon)
    VALUES (?, ?, ?, ?, ?, ?, ?);
    """, medicines_data)

    # Fetch IDs
    cur.execute("SELECT pharmacy_id, name FROM pharmacies")
    pharm_map = {row[1]: row[0] for row in cur.fetchall()}

    cur.execute("SELECT medicine_id, name FROM medicines")
    med_map = {row[1]: row[0] for row in cur.fetchall()}

    cur.execute("SELECT provider_id, user_id FROM providers")
    prov_map = {row[1]: row[0] for row in cur.fetchall()}

    now = datetime.datetime.now()
    t_10m = (now - datetime.timedelta(minutes=8)).strftime('%Y-%m-%d %H:%M:%S')
    t_25m = (now - datetime.timedelta(minutes=25)).strftime('%Y-%m-%d %H:%M:%S')
    t_1h = (now - datetime.timedelta(hours=1, minutes=10)).strftime('%Y-%m-%d %H:%M:%S')
    t_6h = (now - datetime.timedelta(hours=6)).strftime('%Y-%m-%d %H:%M:%S')
    t_yesterday = (now - datetime.timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')

    print("Seeding Medicine Inventory with periodic timestamps...")
    inventory_data = [
        # Balaji Medicals
        (pharm_map["Balaji Medical & General Store"], med_map["Paracetamol 500mg"], "Available", 20.0, t_10m, "Fresh batch arrived today. Strip of 10."),
        (pharm_map["Balaji Medical & General Store"], med_map["ORS Sachet"], "Available", 22.0, t_25m, "WHO formula orange flavor in stock."),
        (pharm_map["Balaji Medical & General Store"], med_map["Cetirizine 10mg"], "Low Stock", 18.0, t_1h, "Only 3 strips remaining."),
        (pharm_map["Balaji Medical & General Store"], med_map["Cough Syrup DX"], "Available", 85.0, t_10m, "Sugar-free version also available."),
        (pharm_map["Balaji Medical & General Store"], med_map["Pantoprazole 40mg"], "Available", 65.0, t_6h, "Standard strip of 10 tablets."),
        (pharm_map["Balaji Medical & General Store"], med_map["Diclofenac Gel"], "Available", 55.0, t_25m, "Fast-acting topical gel."),

        # Sri Rama Gramin Pharmacy
        (pharm_map["Sri Rama Gramin Pharmacy"], med_map["Paracetamol 500mg"], "Available", 22.0, t_1h, "10-tablet strip."),
        (pharm_map["Sri Rama Gramin Pharmacy"], med_map["Metformin 500mg"], "Available", 42.0, t_6h, "Regular diabetic stock available."),
        (pharm_map["Sri Rama Gramin Pharmacy"], med_map["Dettol Antiseptic Liquid"], "Available", 72.0, t_yesterday, "100ml bottle."),
        (pharm_map["Sri Rama Gramin Pharmacy"], med_map["Amoxicillin 500mg"], "Low Stock", 90.0, t_1h, "Requires valid prescription."),
        (pharm_map["Sri Rama Gramin Pharmacy"], med_map["Azithromycin 500mg"], "Unavailable", 120.0, t_yesterday, "Out of stock, distributor shipment delayed.")
    ]

    cur.executemany("""
    INSERT INTO medicine_inventory (pharmacy_id, medicine_id, availability, price, last_updated, notes)
    VALUES (?, ?, ?, ?, ?, ?);
    """, inventory_data)

    print("Seeding Sample Bookings & Reviews...")
    ramesh_pid = prov_map[user_map["ramesh@provider.com"]]
    suresh_pid = prov_map[user_map["suresh@provider.com"]]
    cust_uid = user_map["customer@localserve.com"]

    # Booking 1: Completed with review
    cur.execute("""
    INSERT INTO bookings (user_id, provider_id, service_id, booking_date, booking_time, status, description, customer_name, customer_phone, address, latitude, longitude, created_at)
    VALUES (?, ?, 1, '2026-09-20', '10:30 AM', 'Completed', 'Motor switch sparking and ceiling fan regulator broken', 'Venkata Rao', '+91 9876543210', 'House No. 4-21, Gandhi Nagar', 17.3850, 78.4867, ?);
    """, (cust_uid, ramesh_pid, t_yesterday))
    b1_id = cur.lastrowid

    cur.execute("""
    INSERT INTO reviews (booking_id, user_id, provider_id, rating, comment, created_at)
    VALUES (?, ?, ?, 5, 'Ramesh arrived in 15 minutes! Very humble, fixed the starter switch quickly and charged fairly as displayed.', ?);
    """, (b1_id, cust_uid, ramesh_pid, t_yesterday))

    # Booking 2: Active booking in progress ('On the Way')
    cur.execute("""
    INSERT INTO bookings (user_id, provider_id, service_id, booking_date, booking_time, status, description, customer_name, customer_phone, address, latitude, longitude, created_at)
    VALUES (?, ?, 2, '2026-09-22', '03:00 PM', 'On the Way', 'Bathroom tap leaking heavily and kitchen drain pipe blocked', 'Venkata Rao', '+91 9876543210', 'House No. 4-21, Gandhi Nagar', 17.3850, 78.4867, ?);
    """, (cust_uid, suresh_pid, t_1h))

    print("Seeding Sample Medicine Request...")
    cur.execute("""
    INSERT INTO medicine_requests (user_id, medicine_name, strength, quantity, prescription_image, customer_phone, address, latitude, longitude, status, created_at)
    VALUES (?, 'Insulin Glargine', '100 IU/ml', '2 pens', NULL, '+91 9876543210', 'House 4-21 Gandhi Nagar', 17.3850, 78.4867, 'Responded', ?);
    """, (cust_uid, t_6h))
    req1_id = cur.lastrowid

    balaji_ph_id = pharm_map["Balaji Medical & General Store"]
    cur.execute("""
    INSERT INTO pharmacy_responses (request_id, pharmacy_id, response_status, notes, responded_at)
    VALUES (?, ?, 'Expected Later', 'Stock arriving today evening by 6:30 PM with cold-chain transport. We can reserve 2 pens for you.', ?);
    """, (req1_id, balaji_ph_id, t_1h))

    # Sample Notification
    cur.execute("""
    INSERT INTO notifications (user_id, title, message, is_read, created_at)
    VALUES (?, 'Suresh Plumber is On the Way', 'Your plumbing service request has been accepted and Suresh is traveling to your location.', 0, ?);
    """, (cust_uid, t_25m))

    conn.commit()
    conn.close()
    print("Database seeded successfully with rich realistic local data!")

if __name__ == '__main__':
    seed_database()
