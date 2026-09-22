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

@api_bp.route('/providers/nearby')
def nearby_providers():
    lat = float(request.args.get('lat', session.get('user_lat', Config.DEFAULT_LAT)))
    lng = float(request.args.get('lng', session.get('user_lng', Config.DEFAULT_LNG)))
    radius = float(request.args.get('radius', 15.0))
    category = request.args.get('category', '')

    query = """
        SELECT p.provider_id, p.category, p.experience_years, p.charges_per_hr,
               p.availability, p.latitude, p.longitude, p.address, p.bio, p.rating, p.rating_count,
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

    query += " AND haversine(?, ?, p.latitude, p.longitude) <= ? ORDER BY distance ASC"
    params.extend([lat, lng, radius])

    providers = query_db(query, tuple(params))
    results = [dict(p) for p in providers]
    return jsonify({'count': len(results), 'providers': results})

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
