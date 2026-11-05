import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from database import query_db, execute_db, haversine
from routes.auth import login_required
from utils import time_ago, save_prescription, save_problem_photo
from config import Config

customer_bp = Blueprint('customer', __name__)

@customer_bp.route('/')
def index():
    user_lat = session.get('user_lat', Config.DEFAULT_LAT)
    user_lng = session.get('user_lng', Config.DEFAULT_LNG)
    
    services = query_db("SELECT * FROM services ORDER BY service_id ASC")
    
    # Top verified providers with distance and active availability
    providers = query_db("""
        SELECT p.*, u.name, u.phone, s.icon, s.name as service_name,
               haversine(?, ?, p.latitude, p.longitude) as distance
        FROM providers p
        JOIN users u ON p.user_id = u.user_id
        LEFT JOIN services s ON p.category = s.category
        WHERE p.verification_status = 'Verified'
        ORDER BY CASE p.availability WHEN 'Available' THEN 1 ELSE 2 END, distance ASC
        LIMIT 6
    """, (user_lat, user_lng))

    # Top medicines
    medicines = query_db("""
        SELECT m.*, COUNT(mi.inventory_id) as pharmacy_count
        FROM medicines m
        JOIN medicine_inventory mi ON m.medicine_id = mi.medicine_id
        WHERE mi.availability IN ('Available', 'Low Stock')
        GROUP BY m.medicine_id
        LIMIT 6
    """)

    # Community Skill Impact Statistics
    impact = {
        'people_trained': 126 + query_db("SELECT COUNT(DISTINCT user_id) as c FROM enrollments", one=True)['c'],
        'courses_completed': 84 + query_db("SELECT COUNT(*) as c FROM enrollments WHERE status = 'Completed'", one=True)['c'],
        'local_skill_profiles': 32 + query_db("SELECT COUNT(*) as c FROM user_skill_profiles WHERE is_available_for_work = 1", one=True)['c'],
        'skill_exchanges': 18 + query_db("SELECT COUNT(*) as c FROM skill_exchanges WHERE status = 'Active'", one=True)['c'],
        'workshops_held': 14 + query_db("SELECT COUNT(*) as c FROM training_sessions WHERE status IN ('Scheduled', 'Completed')", one=True)['c'],
        'services_completed': 420 + query_db("SELECT COUNT(*) as c FROM bookings WHERE status = 'Completed'", one=True)['c'],
        'medicines_resolved': 310 + query_db("SELECT COUNT(*) as c FROM medicine_requests WHERE status IN ('Responded', 'Fulfilled')", one=True)['c']
    }

    # Community Notices
    notices = query_db("SELECT * FROM community_notices WHERE is_active = 1 ORDER BY date_effective DESC LIMIT 3")

    return render_template(
        'index.html',
        services=services,
        providers=providers,
        medicines=medicines,
        impact=impact,
        notices=notices
    )

@customer_bp.route('/set-location')
def set_location():
    loc_id = request.args.get('loc', '').lower()
    custom_lat = request.args.get('lat')
    custom_lng = request.args.get('lng')
    custom_name = request.args.get('name', '').strip()
    next_url = request.args.get('next', url_for('customer.index'))

    if custom_lat is not None and custom_lng is not None:
        try:
            session['user_lat'] = float(custom_lat)
            session['user_lng'] = float(custom_lng)
            session['location_name'] = custom_name or f"GPS Location ({float(custom_lat):.3f}, {float(custom_lng):.3f})"
            session['active_location_id'] = 'custom'
            flash(f"Location set to {session['location_name']}. Showing services within 30 km radius.", 'info')
            return redirect(next_url)
        except ValueError:
            pass

    matched = next((l for l in Config.LOCATIONS if l['id'] == loc_id), Config.LOCATIONS[0])
    session['active_location_id'] = matched['id']
    session['user_lat'] = matched['lat']
    session['user_lng'] = matched['lng']
    session['location_name'] = matched['name']
    flash(f"Switched region to {matched['name']} ({matched['telugu_name']}) - PIN {matched['pincode']}. Showing services within 30 km.", 'info')
    return redirect(next_url)

@customer_bp.route('/services')
def services_list():
    category = request.args.get('category', '')
    radius = float(request.args.get('radius', Config.DEFAULT_RADIUS_KM))
    search = request.args.get('q', '').strip().lower()
    available_only = request.args.get('available_now', '') == '1'
    
    user_lat = float(request.args.get('lat', session.get('user_lat', Config.DEFAULT_LAT)))
    user_lng = float(request.args.get('lng', session.get('user_lng', Config.DEFAULT_LNG)))
    location_name = session.get('location_name', Config.LOCATION_NAME)

    query = """
        SELECT p.*, u.name, u.phone, u.email, s.icon, s.name as service_name,
               s.telugu_name as service_telugu, s.hindi_name as service_hindi,
               haversine(?, ?, p.latitude, p.longitude) as distance,
               mp.mentor_id
        FROM providers p
        JOIN users u ON p.user_id = u.user_id
        LEFT JOIN services s ON p.category = s.category
        LEFT JOIN mentor_profiles mp ON p.provider_id = mp.provider_id AND mp.verification_status = 'Verified'
        WHERE p.verification_status = 'Verified'
    """
    params = [user_lat, user_lng]

    if category:
        query += " AND p.category = ?"
        params.append(category)

    if available_only:
        query += " AND p.availability = 'Available'"

    if search:
        query += " AND (LOWER(u.name) LIKE ? OR LOWER(p.category) LIKE ? OR LOWER(p.bio) LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term, term])

    query += f" AND haversine(?, ?, p.latitude, p.longitude) <= ?"
    params.extend([user_lat, user_lng, radius])
    query += " ORDER BY CASE p.availability WHEN 'Available' THEN 1 ELSE 2 END, distance ASC"

    providers = query_db(query, tuple(params))
    all_services = query_db("SELECT * FROM services ORDER BY name ASC")

    return render_template(
        'services.html',
        providers=providers,
        services=all_services,
        selected_category=category,
        radius=radius,
        search=search,
        available_only=available_only,
        user_lat=user_lat,
        user_lng=user_lng,
        location_name=location_name
    )

@customer_bp.route('/provider/<int:provider_id>')
def provider_detail(provider_id):
    user_lat = session.get('user_lat', Config.DEFAULT_LAT)
    user_lng = session.get('user_lng', Config.DEFAULT_LNG)

    provider = query_db("""
        SELECT p.*, u.name, u.phone, u.email, s.icon, s.name as service_name,
               haversine(?, ?, p.latitude, p.longitude) as distance,
               mp.mentor_id
        FROM providers p
        JOIN users u ON p.user_id = u.user_id
        LEFT JOIN services s ON p.category = s.category
        LEFT JOIN mentor_profiles mp ON p.provider_id = mp.provider_id AND mp.verification_status = 'Verified'
        WHERE p.provider_id = ?
    """, (user_lat, user_lng, provider_id), one=True)

    if not provider:
        flash('Provider not found.', 'danger')
        return redirect(url_for('customer.services_list'))

    reviews = query_db("""
        SELECT r.*, u.name as reviewer_name
        FROM reviews r
        JOIN users u ON r.user_id = u.user_id
        WHERE r.provider_id = ?
        ORDER BY r.created_at DESC
    """, (provider_id,))

    service = query_db("SELECT * FROM services WHERE category = ?", (provider['category'],), one=True)

    # Trust Score attributes
    trust_score = {
        'identity_verified': True,
        'provider_verified': provider['verification_status'] == 'Verified',
        'completed_jobs': provider['completed_jobs_count'] or len(reviews) or 25,
        'years_on_platform': provider['years_on_platform'] or 2,
        'rating': provider['rating'] or 5.0
    }

    # Mentor courses if mentor
    mentor_courses = []
    if provider['mentor_id']:
        mentor_courses = query_db("""
            SELECT * FROM courses WHERE mentor_id = ? ORDER BY course_id DESC
        """, (provider['mentor_id'],))

    return render_template(
        'provider_detail.html',
        provider=provider,
        reviews=reviews,
        service=service,
        trust_score=trust_score,
        mentor_courses=mentor_courses
    )

@customer_bp.route('/book/<int:provider_id>', methods=['POST'])
@login_required
def book_service(provider_id):
    provider = query_db("SELECT * FROM providers WHERE provider_id = ?", (provider_id,), one=True)
    if not provider:
        flash('Service provider not found.', 'danger')
        return redirect(url_for('customer.services_list'))

    service = query_db("SELECT service_id FROM services WHERE category = ?", (provider['category'],), one=True)
    service_id = service['service_id'] if service else None

    booking_date = request.form.get('booking_date') or datetime.date.today().strftime('%Y-%m-%d')
    booking_time = request.form.get('booking_time', 'Morning (9 AM - 12 PM)')
    description = request.form.get('description', '').strip()
    customer_name = request.form.get('customer_name', session.get('user_name', 'Customer'))
    customer_phone = request.form.get('customer_phone', session.get('user_phone', ''))
    address = request.form.get('address', '').strip()
    lat = request.form.get('latitude') or session.get('user_lat', Config.DEFAULT_LAT)
    lng = request.form.get('longitude') or session.get('user_lng', Config.DEFAULT_LNG)

    # Problem Photo Upload ("Show the Problem")
    problem_photo = request.files.get('problem_image') or request.files.get('problem_photo')
    problem_photo_filename = save_problem_photo(problem_photo) if problem_photo else None

    booking_id = execute_db("""
        INSERT INTO bookings (user_id, provider_id, service_id, booking_date, booking_time, status,
                              description, problem_image, customer_name, customer_phone, address, latitude, longitude)
        VALUES (?, ?, ?, ?, ?, 'Requested', ?, ?, ?, ?, ?, ?, ?)
    """, (session['user_id'], provider_id, service_id, booking_date, booking_time,
          description, problem_photo_filename, customer_name, customer_phone, address, lat, lng))

    # Notify provider
    execute_db("""
        INSERT INTO notifications (user_id, title, message)
        VALUES (?, 'New Service Booking Request', ?)
    """, (provider['user_id'], f"New booking request #{booking_id} from {customer_name}. {'Problem photo attached.' if problem_photo_filename else ''}"))

    flash(f'Service requested successfully! Booking ID: #{booking_id}. The provider will review your problem and respond shortly.', 'success')
    return redirect(url_for('customer.dashboard'))

@customer_bp.route('/medicines')
def medicines_list():
    q = request.args.get('q', '').strip().lower()
    category = request.args.get('category', '')
    user_lat = float(request.args.get('lat', session.get('user_lat', Config.DEFAULT_LAT)))
    user_lng = float(request.args.get('lng', session.get('user_lng', Config.DEFAULT_LNG)))

    query = """
        SELECT mi.inventory_id, mi.availability, mi.price, mi.last_updated, mi.notes,
               m.medicine_id, m.name as medicine_name, m.telugu_name, m.hindi_name,
               m.strength, m.category, m.description as medicine_desc, m.icon,
               ph.pharmacy_id, ph.name as pharmacy_name, ph.phone as pharmacy_phone,
               ph.address as pharmacy_address, ph.timings,
               haversine(?, ?, ph.latitude, ph.longitude) as distance
        FROM medicine_inventory mi
        JOIN medicines m ON mi.medicine_id = m.medicine_id
        JOIN pharmacies ph ON mi.pharmacy_id = ph.pharmacy_id
        WHERE ph.verification_status = 'Verified'
    """
    params = [user_lat, user_lng]

    if q:
        query += " AND (LOWER(m.name) LIKE ? OR LOWER(m.telugu_name) LIKE ? OR LOWER(m.hindi_name) LIKE ? OR LOWER(m.category) LIKE ?)"
        term = f"%{q}%"
        params.extend([term, term, term, term])

    if category:
        query += " AND m.category = ?"
        params.append(category)

    query += " ORDER BY distance ASC, mi.availability ASC, mi.last_updated DESC"

    raw_results = query_db(query, tuple(params))
    
    results = []
    for row in raw_results:
        d = dict(row)
        d['updated_ago'] = time_ago(d['last_updated'])
        results.append(d)

    categories = query_db("SELECT DISTINCT category FROM medicines ORDER BY category ASC")

    return render_template(
        'medicines.html',
        medicines=results,
        categories=categories,
        search_query=q,
        selected_category=category,
        user_lat=user_lat,
        user_lng=user_lng
    )

@customer_bp.route('/medicine-request', methods=['GET', 'POST'])
@login_required
def medicine_request():
    if request.method == 'POST':
        med_name = request.form.get('medicine_name', '').strip()
        strength = request.form.get('strength', '').strip()
        quantity = request.form.get('quantity', '1 strip').strip()
        customer_phone = request.form.get('customer_phone', session.get('user_phone', ''))
        address = request.form.get('address', '').strip()
        lat = request.form.get('latitude') or session.get('user_lat', Config.DEFAULT_LAT)
        lng = request.form.get('longitude') or session.get('user_lng', Config.DEFAULT_LNG)

        prescription_file = request.files.get('prescription_image')
        prescription_filename = save_prescription(prescription_file) if prescription_file else None

        req_id = execute_db("""
            INSERT INTO medicine_requests (user_id, medicine_name, strength, quantity,
                                          prescription_image, customer_phone, address, latitude, longitude, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Broadcasted')
        """, (session['user_id'], med_name, strength, quantity, prescription_filename, customer_phone, address, lat, lng))

        pharmacies = query_db("SELECT user_id FROM pharmacies WHERE verification_status = 'Verified'")
        for ph in pharmacies:
            execute_db("""
                INSERT INTO notifications (user_id, title, message)
                VALUES (?, 'New Medicine Inquiry from Nearby Patient', ?)
            """, (ph['user_id'], f"Patient requested {med_name} {strength} ({quantity}). Please check your dashboard to respond."))

        flash(f'Medicine availability request #{req_id} broadcasted to nearby pharmacies! Check your dashboard for responses.', 'success')
        return redirect(url_for('customer.dashboard'))

    prefill = request.args.get('prefill', '')
    return render_template('medicine_request.html', prefill=prefill)

@customer_bp.route('/dashboard')
@login_required
def dashboard():
    uid = session['user_id']
    user = query_db("SELECT * FROM users WHERE user_id = ?", (uid,), one=True)

    # Customer service bookings
    bookings = query_db("""
        SELECT b.*, p.charges_per_hr, u.name as provider_name, u.phone as provider_phone,
               s.name as service_name, s.icon as service_icon,
               r.rating as user_rating, r.comment as user_review
        FROM bookings b
        JOIN providers p ON b.provider_id = p.provider_id
        JOIN users u ON p.user_id = u.user_id
        LEFT JOIN services s ON b.service_id = s.service_id
        LEFT JOIN reviews r ON b.booking_id = r.booking_id
        WHERE b.user_id = ?
        ORDER BY b.created_at DESC
    """, (uid,))

    # Customer medicine requests
    requests_raw = query_db("""
        SELECT mr.*
        FROM medicine_requests mr
        WHERE mr.user_id = ?
        ORDER BY mr.created_at DESC
    """, (uid,))

    medicine_requests = []
    for req_item in requests_raw:
        item = dict(req_item)
        item['created_ago'] = time_ago(item['created_at'])
        responses = query_db("""
            SELECT pr.*, ph.name as pharmacy_name, ph.phone as pharmacy_phone, ph.address as pharmacy_address
            FROM pharmacy_responses pr
            JOIN pharmacies ph ON pr.pharmacy_id = ph.pharmacy_id
            WHERE pr.request_id = ?
            ORDER BY pr.responded_at DESC
        """, (item['request_id'],))
        
        proc_responses = []
        for r in responses:
            rd = dict(r)
            rd['responded_ago'] = time_ago(rd['responded_at'])
            proc_responses.append(rd)
        item['responses'] = proc_responses
        medicine_requests.append(item)

    # Customer SkillShare Enrollments
    my_courses = query_db("""
        SELECT e.*, c.title as course_title, c.level, c.duration,
               sc.name as category_name, sc.icon as category_icon,
               u.name as mentor_name,
               cert.verification_code, cert.certificate_number
        FROM enrollments e
        JOIN courses c ON e.course_id = c.course_id
        JOIN skill_categories sc ON c.skill_id = sc.skill_id
        JOIN mentor_profiles mp ON c.mentor_id = mp.mentor_id
        JOIN providers p ON mp.provider_id = p.provider_id
        JOIN users u ON p.user_id = u.user_id
        LEFT JOIN skill_certificates cert ON e.enrollment_id = cert.enrollment_id
        WHERE e.user_id = ?
        ORDER BY e.enrolled_at DESC
    """, (uid,))

    # My Registered Workshops
    my_workshops = query_db("""
        SELECT ts.*, c.title as course_title, u.name as mentor_name
        FROM session_registrations sr
        JOIN training_sessions ts ON sr.session_id = ts.session_id
        LEFT JOIN courses c ON ts.course_id = c.course_id
        JOIN mentor_profiles mp ON ts.mentor_id = mp.mentor_id
        JOIN providers p ON mp.provider_id = p.provider_id
        JOIN users u ON p.user_id = u.user_id
        WHERE sr.user_id = ?
        ORDER BY ts.date ASC
    """, (uid,))

    # My Active Skill Profile (if any)
    my_skill_profiles = query_db("""
        SELECT * FROM user_skill_profiles WHERE user_id = ?
    """, (uid,))

    # Notifications
    notifications = query_db("""
        SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC LIMIT 10
    """, (uid,))

    return render_template(
        'customer_dashboard.html',
        user=user,
        bookings=bookings,
        medicine_requests=medicine_requests,
        my_courses=my_courses,
        my_workshops=my_workshops,
        my_skill_profiles=my_skill_profiles,
        notifications=notifications
    )

@customer_bp.route('/review/<int:booking_id>', methods=['POST'])
@login_required
def add_review(booking_id):
    booking = query_db("SELECT * FROM bookings WHERE booking_id = ? AND user_id = ?",
                       (booking_id, session['user_id']), one=True)
    if not booking:
        flash('Booking not found or not authorized.', 'danger')
        return redirect(url_for('customer.dashboard'))

    rating = int(request.form.get('rating', 5))
    comment = request.form.get('comment', '').strip()

    execute_db("""
        INSERT INTO reviews (booking_id, user_id, provider_id, rating, comment)
        VALUES (?, ?, ?, ?, ?)
    """, (booking_id, session['user_id'], booking['provider_id'], rating, comment))

    stats = query_db("""
        SELECT AVG(rating) as avg_rating, COUNT(review_id) as count
        FROM reviews WHERE provider_id = ?
    """, (booking['provider_id'],), one=True)

    if stats and stats['count']:
        execute_db("""
            UPDATE providers
            SET rating = ?, rating_count = ?, completed_jobs_count = completed_jobs_count + 1
            WHERE provider_id = ?
        """, (round(stats['avg_rating'], 1), stats['count'], booking['provider_id']))

    flash('Thank you! Your rating and feedback have been recorded.', 'success')
    return redirect(url_for('customer.dashboard'))

@customer_bp.route('/complaint', methods=['POST'])
@login_required
def submit_complaint():
    target_type = request.form.get('target_type', 'Provider')
    target_id = request.form.get('target_id')
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()

    execute_db("""
        INSERT INTO complaints (user_id, target_type, target_id, title, description, status)
        VALUES (?, ?, ?, ?, ?, 'Submitted')
    """, (session['user_id'], target_type, target_id, title, description))

    flash('Complaint submitted. The community administrator will investigate.', 'info')
    return redirect(url_for('customer.dashboard'))

@customer_bp.route('/notices')
def notices():
    all_notices = query_db("SELECT * FROM community_notices WHERE is_active = 1 ORDER BY date_effective DESC")
    return render_template('notices.html', notices=all_notices)

@customer_bp.route('/volunteers', endpoint='volunteers_view')
@customer_bp.route('/community-volunteers', endpoint='volunteers')
def volunteers():
    vols = query_db("""
        SELECT v.*, u.name, u.email
        FROM volunteers v
        JOIN users u ON v.user_id = u.user_id
        ORDER BY v.volunteer_id ASC
    """)
    return render_template('volunteers.html', volunteers=vols)

@customer_bp.route('/emergency', endpoint='emergency')
@customer_bp.route('/emergency-help', endpoint='emergency_view')
def emergency_view():
    problem = (request.args.get('problem') or request.args.get('issue') or 'all').lower()
    user_lat = float(request.args.get('lat', session.get('user_lat', Config.DEFAULT_LAT)))
    user_lng = float(request.args.get('lng', session.get('user_lng', Config.DEFAULT_LNG)))

    category_map = {
        'electrical': 'Electrician',
        'plumbing': 'Plumber',
        'water leak': 'Plumber',
        'vehicle': 'Mechanic',
        'mechanic': 'Mechanic',
        'locksmith': 'Carpenter',
        'appliance': 'Appliance Tech'
    }

    providers = []
    pharmacies = []

    if problem == 'medicine':
        pharmacies = query_db("""
            SELECT ph.*, haversine(?, ?, ph.latitude, ph.longitude) as distance
            FROM pharmacies ph
            WHERE ph.verification_status = 'Verified'
            ORDER BY distance ASC
            LIMIT 6
        """, (user_lat, user_lng))
    else:
        query = """
            SELECT p.*, u.name, u.phone, u.address,
                   haversine(?, ?, p.latitude, p.longitude) as distance
            FROM providers p
            JOIN users u ON p.user_id = u.user_id
            WHERE p.verification_status = 'Verified'
              AND p.availability = 'Available'
        """
        params = [user_lat, user_lng]

        if problem in category_map:
            query += " AND p.category = ?"
            params.append(category_map[problem])

        query += " ORDER BY distance ASC LIMIT 6"
        providers = query_db(query, tuple(params))

        pharmacies = query_db("""
            SELECT ph.*, haversine(?, ?, ph.latitude, ph.longitude) as distance
            FROM pharmacies ph
            WHERE ph.verification_status = 'Verified'
            ORDER BY distance ASC
            LIMIT 3
        """, (user_lat, user_lng))

    return render_template(
        'emergency.html',
        problem=problem,
        providers=providers,
        pharmacies=pharmacies,
        user_lat=user_lat,
        user_lng=user_lng
    )
