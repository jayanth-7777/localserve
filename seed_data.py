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
        "user_skill_profiles", "volunteers", "community_notices", "skill_exchanges",
        "session_registrations", "training_sessions", "skill_certificates",
        "lesson_completions", "enrollments", "course_lessons", "courses",
        "mentor_profiles", "skill_categories", "notifications", "complaints",
        "reviews", "pharmacy_responses", "medicine_requests", "medicine_inventory",
        "medicines", "pharmacies", "bookings", "providers", "services", "users"
    ]
    for table in tables:
        cur.execute(f"DELETE FROM {table};")
    try:
        cur.execute("DELETE FROM sqlite_sequence;")
    except Exception:
        pass

    print("Seeding Users...")
    users_data = [
        # Admin
        ("Panchayat Development Officer", "admin@localserve.com", "+91 9999900000", generate_password_hash("admin123"), "admin", 16.3486, 81.0442, "Gudlavalleru Gram Panchayat Office, Main Road, Gudlavalleru - 521356"),
        # Customer
        ("Venkata Rao", "customer@localserve.com", "+91 9876543210", generate_password_hash("pass123"), "customer", 16.3492, 81.0455, "House No. 2-45, Gandhi Bomma Street, Gudlavalleru - 521356"),
        # Gudlavalleru Providers
        ("Ramesh Electrician", "ramesh@provider.com", "+91 9848012345", generate_password_hash("pass123"), "provider", 16.3540, 81.0480, "Plot 12, Power Substation Road, Gudlavalleru - 521356"),
        ("Suresh Plumber", "suresh@provider.com", "+91 9848023456", generate_password_hash("pass123"), "provider", 16.3460, 81.0410, "Shop 3, RTC Bus Stand Complex, Gudlavalleru - 521356"),
        ("Anand Carpenter", "anand@provider.com", "+91 9848034567", generate_password_hash("pass123"), "provider", 16.3475, 81.0430, "Wood Works Lane, Main Bazaar, Gudlavalleru - 521356"),
        ("Ravi Mechanic", "ravi@provider.com", "+91 9848045678", generate_password_hash("pass123"), "provider", 16.3580, 81.0510, "College Road Junction Auto Garage, Near SRGEC, Gudlavalleru - 521356"),
        ("Shiva Tech (Cooler/Fridge)", "shiva@provider.com", "+91 9848056789", generate_password_hash("pass123"), "provider", 16.3450, 81.0460, "Opp. ZP High School, Gudlavalleru - 521356"),
        # Gudlavalleru Pharmacies
        ("Balaji Medical & General Store", "balaji@pharmacy.com", "+91 9123456780", generate_password_hash("pass123"), "pharmacy", 16.3470, 81.0425, "RTC Bus Stand Road, Near Community Hospital, Gudlavalleru - 521356"),
        ("Sri Rama Gramin Pharmacy", "srirama@pharmacy.com", "+91 9123456781", generate_password_hash("pass123"), "pharmacy", 16.3510, 81.0470, "Station Road, Near Gudlavalleru Railway Station, Gudlavalleru - 521356"),
        # Gudlavalleru Community Volunteer
        ("Kavitha Volunteer", "kavitha@volunteer.com", "+91 9848088776", generate_password_hash("pass123"), "customer", 16.3505, 81.0460, "College Road & Station Area, Gudlavalleru - 521356"),

        # Gudivada Providers & Pharmacies (~12 km from Gudlavalleru)
        ("Kishore Electricals (Gudivada)", "kishore@provider.com", "+91 9848123456", generate_password_hash("pass123"), "provider", 16.4420, 80.9940, "Nehru Chowk, Eluru Road, Gudivada - 521301"),
        ("Krishna Plumbing & Sanitation (Gudivada)", "krishna@provider.com", "+91 9848134567", generate_password_hash("pass123"), "provider", 16.4380, 80.9910, "RTC Complex Road, Gudivada - 521301"),
        ("Venkateswara Auto Garage (Gudivada)", "venkat.auto@provider.com", "+91 9848145678", generate_password_hash("pass123"), "provider", 16.4450, 80.9960, "Bhimavaram Bypass Road, Gudivada - 521301"),
        ("Sri Venkateswara Medicals (Gudivada)", "venkat.med@pharmacy.com", "+91 9123456782", generate_password_hash("pass123"), "pharmacy", 16.4405, 80.9930, "Opp. Government Area Hospital, Gudivada - 521301"),
        ("Apollo Pharmacy Gudivada", "apollo.gudivada@pharmacy.com", "+91 9123456783", generate_password_hash("pass123"), "pharmacy", 16.4390, 80.9915, "Gowri Shankar Talkies Road, Gudivada - 521301"),

        # Machilipatnam Providers & Pharmacies (~26 km from Gudlavalleru)
        ("Coastal Cooling & Appliance Care (Machilipatnam)", "coastal@provider.com", "+91 9848212345", generate_password_hash("pass123"), "provider", 16.1890, 81.1400, "Robertsonpet Main Road, Machilipatnam - 521001"),
        ("Durga Heavy & Two-Wheeler Mechanics (Machilipatnam)", "durga@provider.com", "+91 9848223456", generate_password_hash("pass123"), "provider", 16.1850, 81.1350, "Near Old Bus Stand & Port Road, Machilipatnam - 521001"),
        ("District Hospital Road Medicals (Machilipatnam)", "dh.med@pharmacy.com", "+91 9123456784", generate_password_hash("pass123"), "pharmacy", 16.1880, 81.1375, "Near District Headquarters Hospital, Machilipatnam - 521001"),
        ("Sri Satya Sai Pharmacy (Machilipatnam)", "satyasai@pharmacy.com", "+91 9123456785", generate_password_hash("pass123"), "pharmacy", 16.1865, 81.1395, "Koneru Center, Machilipatnam - 521001"),
        ("Rajesh Volunteer (Machilipatnam)", "rajesh@volunteer.com", "+91 9848299887", generate_password_hash("pass123"), "customer", 16.1870, 81.1380, "Koneru Center & Port Road, Machilipatnam - 521001")
    ]

    cur.executemany("""
    INSERT INTO users (name, email, phone, password_hash, role, latitude, longitude, address)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    """, users_data)

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
        # Gudlavalleru Providers
        (user_map["ramesh@provider.com"], "Electrician", 8, 150.0, "Available", "Verified", 16.3540, 81.0480, "Plot 12, Power Substation Road, Gudlavalleru", "Certified electrician with 8 years experience in house wiring, motor starters and farm borewell electricals across Gudlavalleru Mandal.", 4.9, 38, 86, 2),
        (user_map["suresh@provider.com"], "Plumber", 5, 140.0, "Available", "Verified", 16.3460, 81.0410, "Shop 3, RTC Bus Stand Complex, Gudlavalleru", "Quick plumbing repairs, CPVC line fittings, overhead tank cleaning and submersible motor connections in Gudlavalleru.", 4.8, 25, 54, 2),
        (user_map["anand@provider.com"], "Carpenter", 10, 200.0, "Busy", "Verified", 16.3475, 81.0430, "Wood Works Lane, Main Bazaar, Gudlavalleru", "Expert wood artisan for teakwood doors, lock replacement, almirah repairs and window frames in Gudlavalleru.", 4.7, 19, 32, 3),
        (user_map["ravi@provider.com"], "Mechanic", 12, 180.0, "Available", "Verified", 16.3580, 81.0510, "College Road Junction Garage, Near SRGEC, Gudlavalleru", "On-spot puncture repair, tractor hydraulic checks, two-wheeler engine tuning near SRGEC campus.", 4.9, 52, 110, 4),
        (user_map["shiva@provider.com"], "Appliance Repair", 6, 200.0, "Available", "Verified", 16.3450, 81.0460, "Opp. ZP High School, Gudlavalleru", "Refrigerator gas charging, cooler fan repair, ceiling fan winding and washing machine servicing in Gudlavalleru.", 4.6, 14, 28, 1),
        
        # Gudivada Providers (~12 km)
        (user_map["kishore@provider.com"], "Electrician", 9, 160.0, "Available", "Verified", 16.4420, 80.9940, "Nehru Chowk, Eluru Road, Gudivada - 521301", "Industrial motor rewinding, commercial shop wiring, and 3-phase pump starters in Gudivada area.", 4.8, 44, 98, 3),
        (user_map["krishna@provider.com"], "Plumber", 7, 150.0, "Available", "Verified", 16.4380, 80.9910, "RTC Complex Road, Gudivada - 521301", "Sanitary line unclogging, bathroom pipeline fittings, and rooftop overhead tank float valves in Gudivada.", 4.9, 31, 67, 2),
        (user_map["venkat.auto@provider.com"], "Mechanic", 11, 200.0, "Available", "Verified", 16.4450, 80.9960, "Bhimavaram Bypass Road, Gudivada - 521301", "24/7 highway breakdown assistance, tractor clutch repairs and bike engine servicing in Gudivada.", 4.7, 58, 142, 4),

        # Machilipatnam Providers (~26 km)
        (user_map["coastal@provider.com"], "Appliance Repair", 10, 220.0, "Available", "Verified", 16.1890, 81.1400, "Robertsonpet Main Road, Machilipatnam - 521001", "Split AC duct cleaning, commercial deep freezer maintenance, and inverter servicing in Machilipatnam.", 4.8, 36, 75, 3),
        (user_map["durga@provider.com"], "Mechanic", 14, 200.0, "Available", "Verified", 16.1850, 81.1350, "Near Old Bus Stand & Port Road, Machilipatnam - 521001", "Marine boat engine tuning, agricultural tiller servicing, and auto breakdown help in Machilipatnam.", 4.9, 64, 180, 5),
    ]

    cur.executemany("""
    INSERT INTO providers (user_id, category, experience_years, charges_per_hr, availability, verification_status, latitude, longitude, address, bio, rating, rating_count, completed_jobs_count, years_on_platform)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, providers_data)

    print("Seeding Pharmacies...")
    pharmacies_data = [
        # Gudlavalleru Pharmacies
        (user_map["balaji@pharmacy.com"], "Balaji Medical & General Store", "+91 9123456780", "RTC Bus Stand Road, Near Community Hospital, Gudlavalleru - 521356", 16.3470, 81.0425, "Verified", "7:30 AM - 10:30 PM"),
        (user_map["srirama@pharmacy.com"], "Sri Rama Gramin Pharmacy", "+91 9123456781", "Station Road, Near Gudlavalleru Railway Station, Gudlavalleru - 521356", 16.3510, 81.0470, "Verified", "8:00 AM - 9:30 PM"),
        
        # Gudivada Pharmacies
        (user_map["venkat.med@pharmacy.com"], "Sri Venkateswara Medicals (Gudivada)", "+91 9123456782", "Opp. Government Area Hospital, Gudivada - 521301", 16.4405, 80.9930, "Verified", "24 Hours Emergency"),
        (user_map["apollo.gudivada@pharmacy.com"], "Apollo Pharmacy Gudivada", "+91 9123456783", "Gowri Shankar Talkies Road, Gudivada - 521301", 16.4390, 80.9915, "Verified", "7:00 AM - 11:00 PM"),

        # Machilipatnam Pharmacies
        (user_map["dh.med@pharmacy.com"], "District Hospital Road Medicals (Machilipatnam)", "+91 9123456784", "Near District Headquarters Hospital, Machilipatnam - 521001", 16.1880, 81.1375, "Verified", "24 Hours Emergency"),
        (user_map["satyasai@pharmacy.com"], "Sri Satya Sai Pharmacy (Machilipatnam)", "+91 9123456785", "Koneru Center, Machilipatnam - 521001", 16.1865, 81.1395, "Verified", "8:00 AM - 10:30 PM")
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
        # Balaji Medical (Gudlavalleru)
        (pharm_map["Balaji Medical & General Store"], med_map["Paracetamol 500mg"], "Available", 20.0, t_10m, "Fresh batch arrived today. Strip of 10."),
        (pharm_map["Balaji Medical & General Store"], med_map["ORS Sachet"], "Available", 22.0, t_25m, "WHO formula orange flavor in stock."),
        (pharm_map["Balaji Medical & General Store"], med_map["Cetirizine 10mg"], "Low Stock", 18.0, t_1h, "Only 3 strips remaining."),
        (pharm_map["Balaji Medical & General Store"], med_map["Cough Syrup DX"], "Available", 85.0, t_10m, "Sugar-free version also available."),
        (pharm_map["Balaji Medical & General Store"], med_map["Pantoprazole 40mg"], "Available", 65.0, t_6h, "Standard strip of 10 tablets."),
        (pharm_map["Balaji Medical & General Store"], med_map["Diclofenac Gel"], "Available", 55.0, t_25m, "Fast-acting topical gel."),

        # Sri Rama Pharmacy (Gudlavalleru)
        (pharm_map["Sri Rama Gramin Pharmacy"], med_map["Paracetamol 500mg"], "Available", 22.0, t_1h, "10-tablet strip."),
        (pharm_map["Sri Rama Gramin Pharmacy"], med_map["Metformin 500mg"], "Available", 42.0, t_6h, "Regular diabetic stock available."),
        (pharm_map["Sri Rama Gramin Pharmacy"], med_map["Dettol Antiseptic Liquid"], "Available", 72.0, t_yesterday, "100ml bottle."),
        (pharm_map["Sri Rama Gramin Pharmacy"], med_map["Amoxicillin 500mg"], "Low Stock", 90.0, t_1h, "Requires valid prescription."),
        (pharm_map["Sri Rama Gramin Pharmacy"], med_map["Azithromycin 500mg"], "Unavailable", 120.0, t_yesterday, "Out of stock, distributor shipment delayed."),

        # Sri Venkateswara Medicals (Gudivada)
        (pharm_map["Sri Venkateswara Medicals (Gudivada)"], med_map["Paracetamol 500mg"], "Available", 20.0, t_10m, "24-hour emergency stock ready."),
        (pharm_map["Sri Venkateswara Medicals (Gudivada)"], med_map["Azithromycin 500mg"], "Available", 115.0, t_25m, "Full stock in blister packs."),
        (pharm_map["Sri Venkateswara Medicals (Gudivada)"], med_map["Pantoprazole 40mg"], "Available", 60.0, t_1h, "Strip of 10 tablets."),
        (pharm_map["Sri Venkateswara Medicals (Gudivada)"], med_map["Metformin 500mg"], "Available", 40.0, t_1h, "Available."),

        # Apollo Pharmacy Gudivada
        (pharm_map["Apollo Pharmacy Gudivada"], med_map["ORS Sachet"], "Available", 22.0, t_10m, "Electrolyte recharge stock available."),
        (pharm_map["Apollo Pharmacy Gudivada"], med_map["Diclofenac Gel"], "Available", 58.0, t_25m, "Volini & generic diclofenac in stock."),
        (pharm_map["Apollo Pharmacy Gudivada"], med_map["Cetirizine 10mg"], "Available", 18.0, t_10m, "Allergy tabs in stock."),

        # District Hospital Road Medicals (Machilipatnam)
        (pharm_map["District Hospital Road Medicals (Machilipatnam)"], med_map["Paracetamol 500mg"], "Available", 19.0, t_10m, "Hospital emergency counter ready."),
        (pharm_map["District Hospital Road Medicals (Machilipatnam)"], med_map["Amoxicillin 500mg"], "Available", 88.0, t_1h, "Fresh batch available."),
        (pharm_map["District Hospital Road Medicals (Machilipatnam)"], med_map["Dettol Antiseptic Liquid"], "Available", 70.0, t_6h, "Antiseptic in stock."),

        # Sri Satya Sai Pharmacy (Machilipatnam)
        (pharm_map["Sri Satya Sai Pharmacy (Machilipatnam)"], med_map["Cough Syrup DX"], "Available", 82.0, t_25m, "Syrups and bronchodilators available."),
        (pharm_map["Sri Satya Sai Pharmacy (Machilipatnam)"], med_map["Pantoprazole 40mg"], "Available", 62.0, t_1h, "Gastro-resistant tabs in stock.")
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
    VALUES (?, ?, 1, '2026-09-20', '10:30 AM', 'Completed', 'Motor switch sparking and ceiling fan regulator broken', 'Venkata Rao', '+91 9876543210', 'House No. 2-45, Gandhi Bomma Street, Gudlavalleru - 521356', 16.3492, 81.0455, ?);
    """, (cust_uid, ramesh_pid, t_yesterday))
    b1_id = cur.lastrowid

    cur.execute("""
    INSERT INTO reviews (booking_id, user_id, provider_id, rating, comment, created_at)
    VALUES (?, ?, ?, 5, 'Ramesh arrived in 15 minutes! Very humble, fixed the starter switch quickly and charged fairly as displayed.', ?);
    """, (b1_id, cust_uid, ramesh_pid, t_yesterday))

    # Booking 2: Active booking in progress ('On the Way')
    cur.execute("""
    INSERT INTO bookings (user_id, provider_id, service_id, booking_date, booking_time, status, description, customer_name, customer_phone, address, latitude, longitude, created_at)
    VALUES (?, ?, 2, '2026-09-22', '03:00 PM', 'On the Way', 'Bathroom tap leaking heavily and kitchen drain pipe blocked', 'Venkata Rao', '+91 9876543210', 'House No. 2-45, Gandhi Bomma Street, Gudlavalleru - 521356', 16.3492, 81.0455, ?);
    """, (cust_uid, suresh_pid, t_1h))

    print("Seeding Sample Medicine Request...")
    cur.execute("""
    INSERT INTO medicine_requests (user_id, medicine_name, strength, quantity, prescription_image, customer_phone, address, latitude, longitude, status, created_at)
    VALUES (?, 'Insulin Glargine', '100 IU/ml', '2 pens', NULL, '+91 9876543210', 'House 2-45, Gandhi Bomma Street, Gudlavalleru - 521356', 16.3492, 81.0455, 'Responded', ?);
    """, (cust_uid, t_6h))
    req1_id = cur.lastrowid

    balaji_ph_id = pharm_map["Balaji Medical & General Store"]
    cur.execute("""
    INSERT INTO pharmacy_responses (request_id, pharmacy_id, response_status, notes, responded_at)
    VALUES (?, ?, 'Expected Later', 'Stock arriving today evening by 6:30 PM with cold-chain transport. We can reserve 2 pens for you.', ?);
    """, (req1_id, balaji_ph_id, t_1h))

    # ==================== SKILLSHARE SEEDING ====================
    print("Seeding Skill Categories...")
    skills_data = [
        ("Electrical Skills", "electrical", "fa-bolt", "విద్యుత్ నైపుణ్యాలు", "बिजली कौशल", "Fan repair, basic wiring, switch replacement, electrical safety."),
        ("Plumbing Skills", "plumbing", "fa-faucet-drip", "ప్లంబింగ్ నైపుణ్యాలు", "प्लंबिंग कौशल", "Tap repair, pipe fitting, water tank leakage and jointing."),
        ("Two-Wheeler Mechanics", "mechanic", "fa-wrench", "బైక్ & మోటార్ మెకానిక్", "मैकेनिक कौशल", "Puncture repair, chain lube, spark plug cleaning, oil changes."),
        ("Carpentry & Woodwork", "carpentry", "fa-hammer", "వడ్రంగి చెక్క పనులు", "बढ़ई काम", "Door lock fitting, table repair, basic wood jointing."),
        ("Home Maintenance", "home_maintenance", "fa-screwdriver", "ఇంటి నిర్వహణ పనులు", "घर की मरम्मत", "Appliance upkeep, cooler cleaning, drain declogging."),
        ("Digital & Smartphone Skills", "digital", "fa-mobile-screen", "డిజిటల్ & మొబైల్ నైపుణ్యాలు", "डिजिटल कौशल", "Smartphone usage, UPI payments, Aadhaar/Panchayat online portals.")
    ]
    cur.executemany("""
    INSERT INTO skill_categories (name, category_code, icon, telugu_name, hindi_name, description)
    VALUES (?, ?, ?, ?, ?, ?);
    """, skills_data)

    cur.execute("SELECT skill_id, category_code FROM skill_categories")
    skill_map = {row[1]: row[0] for row in cur.fetchall()}

    print("Seeding Skill Mentors...")
    # Ramesh Electrician as Mentor
    cur.execute("""
    INSERT INTO mentor_profiles (provider_id, bio, experience_years, teaching_mode, languages, is_community_free, verification_status, total_learners)
    VALUES (?, 'Passionate electrician committed to empowering youth with safe electrical repair skills. Conducts regular weekend hands-on workshops.', 8, 'In-Person & Workshop', 'Telugu, Hindi, English', 1, 'Verified', 23);
    """, (ramesh_pid,))
    ramesh_mid = cur.lastrowid

    # Suresh Plumber as Mentor
    cur.execute("""
    INSERT INTO mentor_profiles (provider_id, bio, experience_years, teaching_mode, languages, is_community_free, verification_status, total_learners)
    VALUES (?, 'Expert in rural drinking water plumbing, tank fittings, and pump connections. Teaches leak fixing and pipe work.', 5, 'In-Person', 'Telugu', 1, 'Verified', 18);
    """, (suresh_pid,))
    suresh_mid = cur.lastrowid

    ravi_pid = prov_map[user_map["ravi@provider.com"]]
    # Ravi Mechanic as Mentor
    cur.execute("""
    INSERT INTO mentor_profiles (provider_id, bio, experience_years, teaching_mode, languages, is_community_free, verification_status, total_learners)
    VALUES (?, 'Two-wheeler and tractor mechanic. Teaches on-road emergency puncture repair and bike servicing.', 12, 'Workshop & Practical', 'Telugu, Hindi', 1, 'Verified', 15);
    """, (ravi_pid,))
    ravi_mid = cur.lastrowid

    print("Seeding Courses & Lessons...")
    # Course 1: Basic Household Electrical & Fan Repair
    cur.execute("""
    INSERT INTO courses (mentor_id, skill_id, title, description, level, duration, fee, mode, location, safety_instructions)
    VALUES (?, ?, 'Basic Household Electrical & Fan Repair',
            'Learn how to safely repair ceiling fans, replace burnt switches, and wire basic single-phase connections at home.',
            'Beginner', '3 Days', 0.0, 'In-Person & Hands-on', 'Ramesh Workshop / Community Hall',
            'CRITICAL SAFETY WARNING: Always turn off the Main MCB power switch before touching any electrical appliance or socket.');
    """, (ramesh_mid, skill_map['electrical']))
    c1_id = cur.lastrowid

    cur.execute("""
    INSERT INTO course_lessons (course_id, title, description, content, video_url, safety_warning, lesson_order)
    VALUES
    (?, 'Lesson 1: Safety Precautions & Tester Usage',
        'Learn how to hold a neon tester, wear rubber footwear, and verify zero voltage.',
        'Step 1: Put on dry rubber slippers.\nStep 2: Turn off the main breaker.\nStep 3: Insert phase tester into socket to ensure light does not glow.\nStep 4: Keep one hand in pocket to prevent heart path ground loop.',
        'https://www.youtube.com', 'Never touch bare wires while standing on wet ground or without a tester verification.', 1),
    (?, 'Lesson 2: Ceiling Fan Capacitor & Regulator Replacement',
        'Diagnose why a ceiling fan runs slow or hums without rotating.',
        'Step 1: Safely disconnect fan canopy.\nStep 2: Note the wire connections on capacitor clip (2.5uF or 3.15uF).\nStep 3: Discharge capacitor by shorting leads before touching.\nStep 4: Connect new capacitor matching original rating.',
        'https://www.youtube.com', 'Always discharge capacitors before handling. They store high voltage even with power off.', 2),
    (?, 'Lesson 3: Switch & Socket Board Replacement',
        'Replace loose or burnt switches with modern modular switches.',
        'Step 1: Unscrew faceplate.\nStep 2: Connect red (phase) wire to bottom switch terminal.\nStep 3: Connect load wire to top switch terminal.\nStep 4: Tighten screws firmly to prevent arching sparks.',
        'https://www.youtube.com', 'Loose wire screws cause heat and fire sparks. Ensure connections are securely clamped.', 3);
    """, (c1_id, c1_id, c1_id))

    # Course 2: Practical Plumbing & Leak Prevention
    cur.execute("""
    INSERT INTO courses (mentor_id, skill_id, title, description, level, duration, fee, mode, location, safety_instructions)
    VALUES (?, ?, 'Practical Plumbing & Tap Leakage Repair',
            'Master household pipe repairs, washer replacement in dripping taps, and solvent welding for PVC joints.',
            'Beginner', '2 Days', 0.0, 'Hands-on Workshop', 'Bus Stand Community Workshop',
            'Turn off the main overhead tank valve before disassembling any tap or pipe fitting.');
    """, (suresh_mid, skill_map['plumbing']))
    c2_id = cur.lastrowid

    cur.execute("""
    INSERT INTO course_lessons (course_id, title, description, content, video_url, safety_warning, lesson_order)
    VALUES
    (?, 'Lesson 1: Diagnosing Dripping Taps & Washer Replacement',
        'Replace rubber washers and ceramic cartridges in brass and CP taps.',
        'Step 1: Shut off inlet angle valve.\nStep 2: Use adjustable wrench to remove spindle.\nStep 3: Inspect rubber O-ring for tears.\nStep 4: Wrap PTFE Teflon tape 4-5 turns clockwise around threads and tighten.',
        'https://www.youtube.com', 'Do not overtighten brass threads or you may crack the internal housing.', 1),
    (?, 'Lesson 2: PVC Pipe Cutting & Solvent Welding',
        'Learn how to cut and join PVC pipes for water lines without leaks.',
        'Step 1: Cut pipe square using hacksaw.\nStep 2: Deburr edges with sandpaper.\nStep 3: Apply PVC primer and solvent cement evenly.\nStep 4: Push into fitting and hold for 30 seconds.',
        'https://www.youtube.com', 'Use solvent cement in well-ventilated space. Avoid eye or skin contact.', 2);
    """, (c2_id, c2_id))

    # Course 3: Two-Wheeler Emergency Maintenance & Puncture Repair
    cur.execute("""
    INSERT INTO courses (mentor_id, skill_id, title, description, level, duration, fee, mode, location, safety_instructions)
    VALUES (?, ?, 'Two-Wheeler Maintenance & Puncture Repair',
            'Learn tubeless and tube tyre puncture repair, chain tensioning, and spark plug cleaning.',
            'Beginner', '2 Days', 0.0, 'In-Person', 'Highway Garage',
            'Ensure the bike is on double center stand on level solid ground before working on wheels.');
    """, (ravi_mid, skill_map['mechanic']))
    c3_id = cur.lastrowid

    cur.execute("""
    INSERT INTO course_lessons (course_id, title, description, content, video_url, safety_warning, lesson_order)
    VALUES
    (?, 'Lesson 1: Tubeless Tyre Puncture Fixing with Strip Tool',
        'Fix punctures in 5 minutes without opening the wheel.',
        'Step 1: Locate nail or puncture with soapy water.\nStep 2: Remove nail using pliers.\nStep 3: Thread repair rubber strip into eyelet needle.\nStep 4: Insert firmly and pull back needle. Trim excess rubber strip flush with tyre.',
        'https://www.youtube.com', 'Ensure tyre pressure is maintained according to manufacturer specifications (28-32 PSI).', 1);
    """, (c3_id,))

    # Course 4: Digital Skills for Rural Residents
    cur.execute("""
    INSERT INTO courses (mentor_id, skill_id, title, description, level, duration, fee, mode, location, safety_instructions)
    VALUES (?, ?, 'Basic Smartphone & UPI Digital Payments for Daily Life',
            'Empower yourself to use UPI (PhonePe, Google Pay), check electricity bills, and access MeeSeva services.',
            'Beginner', '1 Day', 0.0, 'In-Person', 'Gudlavalleru Gram Panchayat Hall, PIN: 521356',
            'NEVER share your UPI PIN, OTP, or password with anyone, even bank officials.');
    """, (ramesh_mid, skill_map['digital']))

    print("Seeding Completed Enrollment & Certificate for Venkata Rao...")
    cur.execute("""
    INSERT INTO enrollments (course_id, user_id, status, progress, enrolled_at, completed_at)
    VALUES (?, ?, 'Completed', 100, ?, ?);
    """, (c1_id, cust_uid, t_yesterday, t_1h))
    e1_id = cur.lastrowid

    # Record all lesson completions
    cur.execute("SELECT lesson_id FROM course_lessons WHERE course_id = ?", (c1_id,))
    for l_row in cur.fetchall():
        cur.execute("""
        INSERT INTO lesson_completions (enrollment_id, lesson_id, completed_at)
        VALUES (?, ?, ?);
        """, (e1_id, l_row[0], t_1h))

    # Issue Certificate
    cur.execute("""
    INSERT INTO skill_certificates (enrollment_id, certificate_number, verification_code, issued_at)
    VALUES (?, 'LS-ELE-2026-00128', 'ls2026ele777', ?);
    """, (e1_id, t_1h))
    cert1_id = cur.lastrowid

    # Activate Local Skill Profile for Venkata Rao
    cur.execute("""
    INSERT INTO user_skill_profiles (user_id, skill_name, certificate_id, is_available_for_work, hourly_rate, bio)
    VALUES (?, 'Household Electrical & Fan Repair', ?, 1, 100.0, 'Certified in basic electrical repairs by SevaSetu SkillShare. Available for evening neighborhood repairs in Gudlavalleru and nearby Gudivada.');
    """, (cust_uid, cert1_id))

    print("Seeding Community Group Workshops...")
    cur.execute("""
    INSERT INTO training_sessions (course_id, mentor_id, title, date, time, location, capacity, available_seats, fee, status)
    VALUES
    (?, ?, 'Free Community Electrical Safety & Fan Repair Workshop', '2026-10-05', '10:00 AM - 1:00 PM', 'Gudlavalleru Gram Panchayat Community Hall, PIN: 521356', 20, 14, 0.0, 'Scheduled'),
    (?, ?, 'Practical Water Tap & Pipe Jointing Session', '2026-10-10', '02:00 PM - 5:00 PM', 'RTC Bus Stand Community Workshop, Gudlavalleru - 521356', 15, 9, 0.0, 'Scheduled'),
    (?, ?, 'Two-Wheeler Carburetor & Electrical Diagnostic Camp', '2026-10-14', '11:00 AM - 3:00 PM', 'Nehru Chowk Community Hall, Gudivada - 521301', 25, 18, 0.0, 'Scheduled');
    """, (c1_id, ramesh_mid, c2_id, suresh_mid, c1_id, ramesh_mid))

    print("Seeding Community Notices & Volunteers across Gudlavalleru, Gudivada & Machilipatnam...")
    notices_data = [
        ("Drinking Water Tank & Pipeline Maintenance", "Water Supply", "Gudlavalleru Gram Panchayat drinking water supply will be paused tomorrow from 10:00 AM to 2:00 PM for overhead tank desilting near Ryves canal.", "2026-10-02"),
        ("Free Eye & General Health Camp at Gudlavalleru PHC", "Health Camp", "Free health checkup, blood sugar testing, and eye consultation by district hospital medical team at Gudlavalleru Community Hall this Sunday.", "2026-10-06"),
        ("Krishna District Mobile Health Van (Machilipatnam - Gudivada - Gudlavalleru)", "Health Camp", "District Hospital Machilipatnam Mobile Diagnostic Unit will visit Gudlavalleru Friday and Gudivada Saturday with free diagnostic kits.", "2026-10-12"),
        ("Agricultural Sprayer & Motor Maintenance Camp", "Agriculture", "Bring manual and battery pesticide sprayers to Gudlavalleru Market Yard / Rythu Seva Kendram for free nozzle cleanup and pump washer servicing.", "2026-10-08"),
        ("Gudivada - Gudlavalleru Rural RTC Direct Shuttles", "Transport", "New scheduled morning and evening RTC feeder shuttles connecting Gudlavalleru SRGEC to Gudivada Junction and Machilipatnam RTC Depot.", "2026-10-15")
    ]
    cur.executemany("""
    INSERT INTO community_notices (title, category, content, date_effective)
    VALUES (?, ?, ?, ?);
    """, notices_data)

    vol_uid = user_map["kavitha@volunteer.com"]
    vol_rajesh_uid = user_map["rajesh@volunteer.com"]
    cur.execute("""
    INSERT INTO volunteers (user_id, area, phone, skills_assisted)
    VALUES
    (?, 'College Road, Gandhi Bomma Center & Station Area, Gudlavalleru (521356)', '+91 9848088776', 'Assisting elderly residents with medicine search and booking verified electricians/plumbers across Gudlavalleru Mandal.'),
    (?, 'Koneru Center, District Hospital & Port Road, Machilipatnam (521001)', '+91 9848299887', 'Guiding senior citizens with hospital medicine availability and doorstep appliance repair technicians.');
    """, (vol_uid, vol_rajesh_uid))

    # Peer to Peer Skill Exchange
    cur.execute("""
    INSERT INTO skill_exchanges (user_id, teach_skill, learn_skill, notes, status)
    VALUES
    (?, 'Basic Smartphone & Online Banking', 'Ceiling Fan Repair', 'I can teach smartphone usage, online bill payment in exchange for learning fan troubleshooting.', 'Active'),
    (?, 'Vegetable Gardening & Composting', 'Motor Switch Wiring', 'Experienced in terrace farming. Want to learn starter switch replacement.', 'Active');
    """, (cust_uid, vol_uid))

    conn.commit()
    conn.close()
    print("Database seeded with rich SevaSetu multi-town services across Gudlavalleru, Gudivada & Machilipatnam!")

if __name__ == '__main__':
    seed_database()
