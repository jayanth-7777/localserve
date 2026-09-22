import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database import query_db, execute_db
from routes.auth import role_required
from utils import time_ago

pharmacy_bp = Blueprint('pharmacy', __name__, url_prefix='/pharmacy')

@pharmacy_bp.route('/dashboard')
@role_required(['pharmacy'])
def dashboard():
    uid = session['user_id']
    pharmacy = query_db("""
        SELECT * FROM pharmacies WHERE user_id = ?
    """, (uid,), one=True)

    if not pharmacy:
        flash('Pharmacy profile not found.', 'danger')
        return redirect(url_for('customer.index'))

    ph_id = pharmacy['pharmacy_id']

    # 1. Current Inventory with relative timestamps
    raw_inventory = query_db("""
        SELECT mi.*, m.name as medicine_name, m.telugu_name, m.hindi_name,
               m.strength, m.category, m.icon
        FROM medicine_inventory mi
        JOIN medicines m ON mi.medicine_id = m.medicine_id
        WHERE mi.pharmacy_id = ?
        ORDER BY mi.last_updated DESC
    """, (ph_id,))

    inventory = []
    for item in raw_inventory:
        d = dict(item)
        d['updated_ago'] = time_ago(d['last_updated'])
        inventory.append(d)

    # 2. Master catalog medicines not yet in pharmacy's inventory
    available_catalog = query_db("""
        SELECT * FROM medicines
        WHERE medicine_id NOT IN (
            SELECT medicine_id FROM medicine_inventory WHERE pharmacy_id = ?
        )
        ORDER BY name ASC
    """, (ph_id,))

    # 3. Community Medicine Requests from nearby patients
    raw_requests = query_db("""
        SELECT mr.*, u.name as customer_name,
               pr.response_status as my_response_status, pr.notes as my_response_notes
        FROM medicine_requests mr
        JOIN users u ON mr.user_id = u.user_id
        LEFT JOIN pharmacy_responses pr ON mr.request_id = pr.request_id AND pr.pharmacy_id = ?
        ORDER BY mr.created_at DESC
        LIMIT 25
    """, (ph_id,))

    medicine_requests = []
    for req in raw_requests:
        d = dict(req)
        d['created_ago'] = time_ago(d['created_at'])
        medicine_requests.append(d)

    stats = {
        'total_items': len(inventory),
        'available_count': len([i for i in inventory if i['availability'] == 'Available']),
        'low_stock_count': len([i for i in inventory if i['availability'] == 'Low Stock']),
        'pending_requests': len([r for r in medicine_requests if not r['my_response_status']])
    }

    return render_template(
        'pharmacy_dashboard.html',
        pharmacy=pharmacy,
        inventory=inventory,
        available_catalog=available_catalog,
        medicine_requests=medicine_requests,
        stats=stats
    )

@pharmacy_bp.route('/inventory/update/<int:inventory_id>', methods=['POST'])
@role_required(['pharmacy'])
def update_inventory(inventory_id):
    pharmacy = query_db("SELECT pharmacy_id FROM pharmacies WHERE user_id = ?", (session['user_id'],), one=True)
    availability = request.form.get('availability', 'Available')
    price = float(request.form.get('price', 20.0))
    notes = request.form.get('notes', '').strip()

    execute_db("""
        UPDATE medicine_inventory
        SET availability = ?, price = ?, notes = ?, last_updated = CURRENT_TIMESTAMP
        WHERE inventory_id = ? AND pharmacy_id = ?
    """, (availability, price, notes, inventory_id, pharmacy['pharmacy_id']))

    flash('Medicine inventory and reporting timestamp updated successfully!', 'success')
    return redirect(url_for('pharmacy.dashboard'))

@pharmacy_bp.route('/inventory/quick-confirm/<int:inventory_id>', methods=['POST'])
@role_required(['pharmacy'])
def quick_confirm(inventory_id):
    """Refreshes last_updated timestamp to prove stock was just verified."""
    pharmacy = query_db("SELECT pharmacy_id FROM pharmacies WHERE user_id = ?", (session['user_id'],), one=True)
    execute_db("""
        UPDATE medicine_inventory
        SET last_updated = CURRENT_TIMESTAMP
        WHERE inventory_id = ? AND pharmacy_id = ?
    """, (inventory_id, pharmacy['pharmacy_id']))

    flash('Stock confirmed! Timestamp updated to Just Now.', 'info')
    return redirect(url_for('pharmacy.dashboard'))

@pharmacy_bp.route('/inventory/add', methods=['POST'])
@role_required(['pharmacy'])
def add_to_inventory():
    pharmacy = query_db("SELECT pharmacy_id FROM pharmacies WHERE user_id = ?", (session['user_id'],), one=True)
    med_id = request.form.get('medicine_id')
    availability = request.form.get('availability', 'Available')
    price = float(request.form.get('price', 25.0))
    notes = request.form.get('notes', '').strip()

    # If new medicine name provided that's not in catalog
    custom_name = request.form.get('custom_name', '').strip()
    if not med_id and custom_name:
        strength = request.form.get('custom_strength', 'Standard')
        category = request.form.get('custom_category', 'General')
        med_id = execute_db("""
            INSERT INTO medicines (name, strength, category, description)
            VALUES (?, ?, ?, 'Added by pharmacy')
        """, (custom_name, strength, category))

    if med_id:
        execute_db("""
            INSERT OR REPLACE INTO medicine_inventory (pharmacy_id, medicine_id, availability, price, notes, last_updated)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (pharmacy['pharmacy_id'], med_id, availability, price, notes))
        flash('Medicine added to your pharmacy catalog!', 'success')
    else:
        flash('Please select or enter a valid medicine.', 'warning')

    return redirect(url_for('pharmacy.dashboard'))

@pharmacy_bp.route('/request/<int:request_id>/respond', methods=['POST'])
@role_required(['pharmacy'])
def respond_request(request_id):
    pharmacy = query_db("SELECT * FROM pharmacies WHERE user_id = ?", (session['user_id'],), one=True)
    status = request.form.get('response_status')  # 'Available', 'Not Available', 'Expected Later'
    notes = request.form.get('notes', '').strip()

    med_req = query_db("SELECT * FROM medicine_requests WHERE request_id = ?", (request_id,), one=True)
    if not med_req:
        flash('Medicine request not found.', 'danger')
        return redirect(url_for('pharmacy.dashboard'))

    execute_db("""
        INSERT OR REPLACE INTO pharmacy_responses (request_id, pharmacy_id, response_status, notes, responded_at)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (request_id, pharmacy['pharmacy_id'], status, notes))

    # Mark request as Responded
    execute_db("UPDATE medicine_requests SET status = 'Responded' WHERE request_id = ?", (request_id,))

    # Notify customer
    notify_text = f"{pharmacy['name']} responded '{status}' to your request for {med_req['medicine_name']}."
    if notes:
        notify_text += f" Note: {notes}"

    execute_db("""
        INSERT INTO notifications (user_id, title, message)
        VALUES (?, 'Medicine Request Response', ?)
    """, (med_req['user_id'], notify_text))

    flash('Your response has been sent to the patient!', 'success')
    return redirect(url_for('pharmacy.dashboard'))
