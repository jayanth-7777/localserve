from flask import Blueprint, request, jsonify, session
from database import query_db, execute_db, haversine
from utils import time_ago
from config import Config

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/set-location', methods=['POST'])
def set_location():
    data = request.get_json() or {}
    lat = data.get('lat')
    lng = data.get('lng')
    if lat is not None and lng is not None:
        try:
            session['user_lat'] = float(lat)
            session['user_lng'] = float(lng)
            if 'user_id' in session:
                execute_db("UPDATE users SET latitude = ?, longitude = ? WHERE user_id = ?",
                           (session['user_lat'], session['user_lng'], session['user_id']))
            return jsonify({'status': 'success', 'lat': session['user_lat'], 'lng': session['user_lng']})
        except ValueError:
            pass
    return jsonify({'status': 'error', 'message': 'Invalid coordinates'}), 400

@api_bp.route('/assistant', methods=['POST'])
def smart_assistant():
    """Smart Service Assistant NLP and Keyword Intent Parser with Multilingual Support."""
    data = request.get_json() or {}
    query = data.get('query', '').strip().lower()
    user_lat = float(session.get('user_lat', Config.DEFAULT_LAT))
    user_lng = float(session.get('user_lng', Config.DEFAULT_LNG))

    if not query:
        return jsonify({'status': 'error', 'message': 'Empty query'}), 400

    # Keyword intent mappings
    intents = {
        'Plumber': [
            'leak', 'pipe', 'tap', 'water', 'drain', 'flush', 'plumbing', 'faucet', 'sump',
            'లీక్', 'పైపు', 'నల్లా', 'నీళ్లు', 'డ్రైనేజ్', 'మోటార్ పైపు', 'नल', 'पाइप', 'पानी'
        ],
        'Electrician': [
            'current', 'shock', 'switch', 'light', 'fan', 'bulb', 'spark', 'wiring', 'meter', 'tripping', 'power',
            'కరెంట్', 'స్విచ్', 'ఫ్యాన్', 'వైరింగ్', 'స్టార్టర్', 'షాక్', 'స్పార్క్', 'విద్యుత్', 'बिजली', 'पंखा'
        ],
        'Mechanic': [
            'bike', 'scooter', 'tractor', 'puncture', 'brake', 'engine', 'oil', 'wheel', 'chain', 'tyre',
            'బైక్', 'ట్రాక్టర్', 'పంచర్', 'బ్రేక్', 'ఇంజిన్', 'గేర్', 'గాడీ', 'मैकेनिक', 'ट्रेक्टर', 'पंचर'
        ],
        'Carpenter': [
            'door', 'lock', 'wood', 'table', 'chair', 'cot', 'almirah', 'furniture', 'carpenter',
            'తలుపు', 'తాళం', 'చెక్క', 'మంచం', 'వడ్రంగి', 'టేబుల్', 'दरवाजा', 'लकड़ी', 'बढ़ई'
        ],
        'Appliance Repair': [
            'fridge', 'refrigerator', 'cooler', 'ac', 'washing machine', 'gas',
            'ఫ్రిజ్', 'కూలర్', 'ఏసీ', 'వాషింగ్ మెషిన్', 'कूलर', 'फ्रिज'
        ],
        'Cleaning': [
            'clean', 'wash', 'sweep', 'dust', 'cleaning',
            'క్లీనింగ్', 'శుభ్రం', 'చెత్త', 'झाड़ू', 'सफाई'
        ]
    }

    matched_category = None
    for category, keywords in intents.items():
        if any(kw in query for kw in keywords):
            matched_category = category
            break

    # Check if medicine related
    med_keywords = ['medicine', 'tablet', 'syrup', 'fever', 'headache', 'cold', 'ors', 'pain', 'paracetamol', 'cough',
                    'మందు', 'టాబ్లెట్', 'జ్వరం', 'తలనొప్పి', 'జలుబు', 'దగ్గు', 'दवा', 'गोली', 'बुखार']
    if any(kw in query for kw in med_keywords):
        return jsonify({
            'intent': 'medicine',
            'type': 'medicine',
            'category': 'Medicines',
            'title': 'Local Medicine Availability',
            'redirect_url': f'/medicines?q={query}',
            'message': f"Looking for medicines related to '{query}' across nearby verified pharmacies."
        })

    # Check if SkillShare related
    skill_keywords = ['learn', 'course', 'training', 'teach', 'class', 'workshop',
                      'నేర్చుకోవాలి', 'శిక్షణ', 'కోర్సు', 'सीखना', 'कोर्स', 'ट्रेनिंग']
    if any(kw in query for kw in skill_keywords):
        return jsonify({
            'intent': 'skillshare',
            'type': 'skillshare',
            'category': 'SkillShare',
            'title': 'SkillShare Practical Courses',
            'redirect_url': f'/skillshare/courses?q={query}',
            'message': f"Found Skill Mentors and practical training courses for '{query}'."
        })

    # If service category matched
    if matched_category:
        nearby_provs = query_db("""
            SELECT p.*, u.name, u.phone, s.icon,
                   haversine(?, ?, p.latitude, p.longitude) as distance
            FROM providers p
            JOIN users u ON p.user_id = u.user_id
            LEFT JOIN services s ON p.category = s.category
            WHERE p.verification_status = 'Verified' AND p.category = ?
            ORDER BY CASE p.availability WHEN 'Available' THEN 1 ELSE 2 END, distance ASC
            LIMIT 3
        """, (user_lat, user_lng, matched_category))

        return jsonify({
            'intent': 'service',
            'type': 'service',
            'category': matched_category,
            'title': f'{matched_category} Service Found',
            'redirect_url': f'/services?category={matched_category}',
            'message': f"Identified your need as {matched_category}. Here are the nearest verified experts.",
            'providers': [dict(p) for p in nearby_provs]
        })

    # General fallback
    return jsonify({
        'intent': 'general',
        'type': 'general',
        'category': 'General Search',
        'title': 'Searching LOCALServe',
        'redirect_url': f'/services?q={query}',
        'message': f"Searching for verified providers matching '{query}'."
    })

@api_bp.route('/providers/nearby')
def nearby_providers():
    lat = float(request.args.get('lat', session.get('user_lat', Config.DEFAULT_LAT)))
    lng = float(request.args.get('lng', session.get('user_lng', Config.DEFAULT_LNG)))
    radius = float(request.args.get('radius', 15.0))
    category = request.args.get('category', '')
    available_only = request.args.get('available_now', '') == '1'

    query = """
        SELECT p.provider_id, p.category, p.experience_years, p.charges_per_hr,
               p.availability, p.latitude, p.longitude, p.address, p.bio, p.rating, p.rating_count,
               p.completed_jobs_count, p.years_on_platform,
               u.name, u.phone, s.icon,
               haversine(?, ?, p.latitude, p.longitude) as distance
        FROM providers p
        JOIN users u ON p.user_id = u.user_id
        LEFT JOIN services s ON p.category = s.category
        WHERE p.verification_status = 'Verified'
    """
    params = [lat, lng]

    if category:
        query += " AND p.category = ?"
        params.append(category)

    if available_only:
        query += " AND p.availability = 'Available'"

    query += " AND haversine(?, ?, p.latitude, p.longitude) <= ? ORDER BY CASE p.availability WHEN 'Available' THEN 1 ELSE 2 END, distance ASC"
    params.extend([lat, lng, radius])

    providers = query_db(query, tuple(params))
    results = [dict(p) for p in providers]
    return jsonify({'count': len(results), 'providers': results})

@api_bp.route('/mentors/nearby')
def nearby_mentors():
    lat = float(request.args.get('lat', session.get('user_lat', Config.DEFAULT_LAT)))
    lng = float(request.args.get('lng', session.get('user_lng', Config.DEFAULT_LNG)))
    radius = float(request.args.get('radius', 25.0))

    query = """
        SELECT mp.*, u.name, u.phone, p.category, p.latitude, p.longitude, p.address,
               haversine(?, ?, p.latitude, p.longitude) as distance
        FROM mentor_profiles mp
        JOIN providers p ON mp.provider_id = p.provider_id
        JOIN users u ON p.user_id = u.user_id
        WHERE mp.verification_status = 'Verified'
          AND haversine(?, ?, p.latitude, p.longitude) <= ?
        ORDER BY distance ASC
    """
    mentors = query_db(query, (lat, lng, lat, lng, radius))
    return jsonify({'count': len(mentors), 'mentors': [dict(m) for m in mentors]})

@api_bp.route('/pharmacies/nearby')
def nearby_pharmacies():
    lat = float(request.args.get('lat', session.get('user_lat', Config.DEFAULT_LAT)))
    lng = float(request.args.get('lng', session.get('user_lng', Config.DEFAULT_LNG)))
    radius = float(request.args.get('radius', 15.0))

    query = """
        SELECT ph.*, haversine(?, ?, ph.latitude, ph.longitude) as distance
        FROM pharmacies ph
        WHERE ph.verification_status = 'Verified'
          AND haversine(?, ?, ph.latitude, ph.longitude) <= ?
        ORDER BY distance ASC
    """
    pharmacies = query_db(query, (lat, lng, lat, lng, radius))
    return jsonify({'count': len(pharmacies), 'pharmacies': [dict(p) for p in pharmacies]})

@api_bp.route('/medicines/search')
def search_medicines():
    q = request.args.get('q', '').strip().lower()
    lat = float(request.args.get('lat', session.get('user_lat', Config.DEFAULT_LAT)))
    lng = float(request.args.get('lng', session.get('user_lng', Config.DEFAULT_LNG)))

    query = """
        SELECT mi.inventory_id, mi.availability, mi.price, mi.last_updated, mi.notes,
               m.medicine_id, m.name as medicine_name, m.telugu_name, m.hindi_name,
               m.strength, m.category, m.description as medicine_desc, m.icon,
               ph.pharmacy_id, ph.name as pharmacy_name, ph.phone as pharmacy_phone,
               ph.address as pharmacy_address,
               haversine(?, ?, ph.latitude, ph.longitude) as distance
        FROM medicine_inventory mi
        JOIN medicines m ON mi.medicine_id = m.medicine_id
        JOIN pharmacies ph ON mi.pharmacy_id = ph.pharmacy_id
        WHERE ph.verification_status = 'Verified'
    """
    params = [lat, lng]

    if q:
        query += " AND (LOWER(m.name) LIKE ? OR LOWER(m.telugu_name) LIKE ? OR LOWER(m.hindi_name) LIKE ? OR LOWER(m.category) LIKE ?)"
        term = f"%{q}%"
        params.extend([term, term, term, term])

    query += " ORDER BY distance ASC, mi.availability ASC, mi.last_updated DESC"

    records = query_db(query, tuple(params))
    results = []
    for r in records:
        d = dict(r)
        d['updated_ago'] = time_ago(d['last_updated'])
        results.append(d)

    return jsonify({'count': len(results), 'medicines': results})

@api_bp.route('/impact')
def get_impact_metrics():
    impact = {
        'people_trained': 126 + query_db("SELECT COUNT(DISTINCT user_id) as c FROM enrollments", one=True)['c'],
        'courses_completed': 84 + query_db("SELECT COUNT(*) as c FROM enrollments WHERE status = 'Completed'", one=True)['c'],
        'local_skill_profiles': 32 + query_db("SELECT COUNT(*) as c FROM user_skill_profiles WHERE is_available_for_work = 1", one=True)['c'],
        'skill_exchanges': 18 + query_db("SELECT COUNT(*) as c FROM skill_exchanges WHERE status = 'Active'", one=True)['c'],
        'workshops_held': 14 + query_db("SELECT COUNT(*) as c FROM training_sessions WHERE status IN ('Scheduled', 'Completed')", one=True)['c'],
        'services_completed': 420 + query_db("SELECT COUNT(*) as c FROM bookings WHERE status = 'Completed'", one=True)['c'],
        'medicines_resolved': 310 + query_db("SELECT COUNT(*) as c FROM medicine_requests WHERE status IN ('Responded', 'Fulfilled')", one=True)['c']
    }
    return jsonify(impact)

@api_bp.route('/notifications')
def get_notifications():
    if 'user_id' not in session:
        return jsonify([])
    notes = query_db("""
        SELECT * FROM notifications
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 10
    """, (session['user_id'],))
    return jsonify([dict(n) for n in notes])

@api_bp.route('/notifications/<int:nid>/read', methods=['POST'])
def mark_read(nid):
    if 'user_id' in session:
        execute_db("UPDATE notifications SET is_read = 1 WHERE notification_id = ? AND user_id = ?",
                   (nid, session['user_id']))
    return jsonify({'status': 'ok'})
