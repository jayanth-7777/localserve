from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database import query_db, execute_db
from routes.auth import role_required
from utils import time_ago

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@role_required(['admin'])
def dashboard():
    # 1. Platform statistics
    stats = {
        'total_users': query_db("SELECT COUNT(*) as c FROM users", one=True)['c'],
        'total_providers': query_db("SELECT COUNT(*) as c FROM providers", one=True)['c'],
        'verified_providers': query_db("SELECT COUNT(*) as c FROM providers WHERE verification_status = 'Verified'", one=True)['c'],
        'pending_providers': query_db("SELECT COUNT(*) as c FROM providers WHERE verification_status = 'Pending'", one=True)['c'],
        'total_pharmacies': query_db("SELECT COUNT(*) as c FROM pharmacies", one=True)['c'],
        'verified_pharmacies': query_db("SELECT COUNT(*) as c FROM pharmacies WHERE verification_status = 'Verified'", one=True)['c'],
        'total_bookings': query_db("SELECT COUNT(*) as c FROM bookings", one=True)['c'],
        'completed_bookings': query_db("SELECT COUNT(*) as c FROM bookings WHERE status = 'Completed'", one=True)['c'],
        'total_requests': query_db("SELECT COUNT(*) as c FROM medicine_requests", one=True)['c'],
        'open_complaints': query_db("SELECT COUNT(*) as c FROM complaints WHERE status IN ('Submitted', 'Investigating')", one=True)['c']
    }

    # 2. Providers verification list
    providers = query_db("""
        SELECT p.*, u.name, u.email, u.phone, u.created_at as registered_date
        FROM providers p
        JOIN users u ON p.user_id = u.user_id
        ORDER BY CASE p.verification_status WHEN 'Pending' THEN 1 ELSE 2 END, p.provider_id DESC
    """)

    # 3. Pharmacies verification list
    pharmacies = query_db("""
        SELECT ph.*, u.email, u.created_at as registered_date
        FROM pharmacies ph
        JOIN users u ON ph.user_id = u.user_id
        ORDER BY CASE ph.verification_status WHEN 'Pending' THEN 1 ELSE 2 END, ph.pharmacy_id DESC
    """)

    # 4. Complaints list
    raw_complaints = query_db("""
        SELECT c.*, u.name as complainant_name, u.phone as complainant_phone
        FROM complaints c
        JOIN users u ON c.user_id = u.user_id
        ORDER BY CASE c.status WHEN 'Submitted' THEN 1 WHEN 'Investigating' THEN 2 ELSE 3 END, c.created_at DESC
    """)
    complaints = []
    for comp in raw_complaints:
        cd = dict(comp)
        cd['created_ago'] = time_ago(cd['created_at'])
        complaints.append(cd)

    # 5. Service Categories
    services = query_db("SELECT * FROM services ORDER BY service_id ASC")

    # 6. Recent platform bookings
    recent_bookings = query_db("""
        SELECT b.*, u.name as customer_name, p_u.name as provider_name, s.name as service_name
        FROM bookings b
        JOIN users u ON b.user_id = u.user_id
        JOIN providers p ON b.provider_id = p.provider_id
        JOIN users p_u ON p.user_id = p_u.user_id
        LEFT JOIN services s ON b.service_id = s.service_id
        ORDER BY b.created_at DESC
        LIMIT 15
    """)

    return render_template(
        'admin_dashboard.html',
        stats=stats,
        providers=providers,
        pharmacies=pharmacies,
        complaints=complaints,
        services=services,
        recent_bookings=recent_bookings
    )

@admin_bp.route('/provider/<int:provider_id>/status', methods=['POST'])
@role_required(['admin'])
def update_provider_status(provider_id):
    status = request.form.get('status')
    if status in ['Verified', 'Pending', 'Rejected', 'Suspended']:
        execute_db("UPDATE providers SET verification_status = ? WHERE provider_id = ?", (status, provider_id))
        
        provider = query_db("SELECT user_id FROM providers WHERE provider_id = ?", (provider_id,), one=True)
        if provider:
            execute_db("""
                INSERT INTO notifications (user_id, title, message)
                VALUES (?, 'Provider Account Status Update', ?)
            """, (provider['user_id'], f"Your provider account status has been updated to: {status} by the platform administrator."))

        flash(f'Provider verification status changed to {status}.', 'success')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/pharmacy/<int:pharmacy_id>/status', methods=['POST'])
@role_required(['admin'])
def update_pharmacy_status(pharmacy_id):
    status = request.form.get('status')
    if status in ['Verified', 'Pending', 'Rejected', 'Suspended']:
        execute_db("UPDATE pharmacies SET verification_status = ? WHERE pharmacy_id = ?", (status, pharmacy_id))
        
        pharmacy = query_db("SELECT user_id FROM pharmacies WHERE pharmacy_id = ?", (pharmacy_id,), one=True)
        if pharmacy:
            execute_db("""
                INSERT INTO notifications (user_id, title, message)
                VALUES (?, 'Pharmacy Account Status Update', ?)
            """, (pharmacy['user_id'], f"Your pharmacy account status has been updated to: {status}."))

        flash(f'Pharmacy verification status changed to {status}.', 'success')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/complaint/<int:complaint_id>/resolve', methods=['POST'])
@role_required(['admin'])
def resolve_complaint(complaint_id):
    status = request.form.get('status', 'Resolved')
    notes = request.form.get('admin_notes', '').strip()

    execute_db("""
        UPDATE complaints SET status = ?, admin_notes = ? WHERE complaint_id = ?
    """, (status, notes, complaint_id))

    complaint = query_db("SELECT user_id, title FROM complaints WHERE complaint_id = ?", (complaint_id,), one=True)
    if complaint:
        execute_db("""
            INSERT INTO notifications (user_id, title, message)
            VALUES (?, 'Complaint Status Update', ?)
        """, (complaint['user_id'], f"Your complaint regarding '{complaint['title']}' has been updated to: {status}. Note: {notes}"))

    flash('Complaint updated successfully.', 'success')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/service/add', methods=['POST'])
@role_required(['admin'])
def add_service():
    name = request.form.get('name', '').strip()
    category = request.form.get('category', '').strip()
    icon = request.form.get('icon', 'fa-tools').strip()
    telugu = request.form.get('telugu_name', '').strip()
    hindi = request.form.get('hindi_name', '').strip()
    price = float(request.form.get('base_price', 150))
    desc = request.form.get('description', '').strip()

    if name and category:
        execute_db("""
            INSERT OR REPLACE INTO services (name, category, icon, telugu_name, hindi_name, base_price, description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, category, icon, telugu, hindi, price, desc))
        flash(f'Service category "{name}" added/updated successfully.', 'success')
    else:
        flash('Service name and category are required.', 'warning')

    return redirect(url_for('admin.dashboard'))
