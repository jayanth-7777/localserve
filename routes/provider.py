from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database import query_db, execute_db
from routes.auth import role_required
from utils import time_ago

provider_bp = Blueprint('provider', __name__, url_prefix='/provider')

@provider_bp.route('/dashboard')
@role_required(['provider'])
def dashboard():
    uid = session['user_id']
    provider = query_db("""
        SELECT p.*, u.name, u.email, u.phone, s.icon, s.name as service_name
        FROM providers p
        JOIN users u ON p.user_id = u.user_id
        LEFT JOIN services s ON p.category = s.category
        WHERE p.user_id = ?
    """, (uid,), one=True)

    if not provider:
        flash('Provider profile not found.', 'danger')
        return redirect(url_for('customer.index'))

    pid = provider['provider_id']

    # 1. Incoming Pending Requests (status = 'Requested')
    pending_bookings = query_db("""
        SELECT b.*, u.name as customer_name, u.phone as customer_phone, u.address as customer_addr
        FROM bookings b
        JOIN users u ON b.user_id = u.user_id
        WHERE b.provider_id = ? AND b.status = 'Requested'
        ORDER BY b.created_at DESC
    """, (pid,))

    # 2. Active Ongoing Bookings (status in 'Accepted', 'Provider Assigned', 'On the Way', 'Service Started')
    active_bookings = query_db("""
        SELECT b.*, u.name as customer_name, u.phone as customer_phone, u.address as customer_addr
        FROM bookings b
        JOIN users u ON b.user_id = u.user_id
        WHERE b.provider_id = ? AND b.status IN ('Accepted', 'Provider Assigned', 'On the Way', 'Service Started')
        ORDER BY b.created_at DESC
    """, (pid,))

    # 3. Completed or Rejected Job History
    history_bookings = query_db("""
        SELECT b.*, u.name as customer_name, u.phone as customer_phone,
               r.rating as review_rating, r.comment as review_comment
        FROM bookings b
        JOIN users u ON b.user_id = u.user_id
        LEFT JOIN reviews r ON b.booking_id = r.booking_id
        WHERE b.provider_id = ? AND b.status IN ('Completed', 'Rejected')
        ORDER BY b.created_at DESC
        LIMIT 20
    """, (pid,))

    # 4. Reviews received
    reviews = query_db("""
        SELECT r.*, u.name as reviewer_name, b.booking_date
        FROM reviews r
        JOIN users u ON r.user_id = u.user_id
        JOIN bookings b ON r.booking_id = b.booking_id
        WHERE r.provider_id = ?
        ORDER BY r.created_at DESC
    """, (pid,))

    # Statistics
    stats = {
        'total_completed': len([b for b in history_bookings if b['status'] == 'Completed']),
        'total_active': len(active_bookings),
        'total_pending': len(pending_bookings),
        'rating': provider['rating'] or 5.0,
        'rating_count': provider['rating_count'] or 0
    }

    return render_template(
        'provider_dashboard.html',
        provider=provider,
        pending_bookings=pending_bookings,
        active_bookings=active_bookings,
        history_bookings=history_bookings,
        reviews=reviews,
        stats=stats
    )

@provider_bp.route('/toggle-availability', methods=['POST'])
@role_required(['provider'])
def toggle_availability():
    new_status = request.form.get('availability', 'Available')
    if new_status not in ['Available', 'Busy', 'Offline']:
        new_status = 'Available'
        
    execute_db("UPDATE providers SET availability = ? WHERE user_id = ?",
               (new_status, session['user_id']))
    flash(f'Your status is now updated to: {new_status}', 'info')
    return redirect(url_for('provider.dashboard'))

@provider_bp.route('/booking/<int:booking_id>/respond', methods=['POST'])
@role_required(['provider'])
def respond_booking(booking_id):
    action = request.form.get('action')  # 'accept' or 'reject'
    provider = query_db("SELECT provider_id, category FROM providers WHERE user_id = ?", (session['user_id'],), one=True)
    
    booking = query_db("SELECT * FROM bookings WHERE booking_id = ? AND provider_id = ?",
                       (booking_id, provider['provider_id']), one=True)
    if not booking:
        flash('Booking not found or not assigned to you.', 'danger')
        return redirect(url_for('provider.dashboard'))

    if action == 'accept':
        execute_db("UPDATE bookings SET status = 'Accepted' WHERE booking_id = ?", (booking_id,))
        execute_db("""
            INSERT INTO notifications (user_id, title, message)
            VALUES (?, 'Booking Accepted!', 'The provider has accepted your service request. They will prepare to visit.')
        """, (booking['user_id'],))
        flash(f'Booking #{booking_id} accepted!', 'success')
    elif action == 'reject':
        execute_db("UPDATE bookings SET status = 'Rejected' WHERE booking_id = ?", (booking_id,))
        execute_db("""
            INSERT INTO notifications (user_id, title, message)
            VALUES (?, 'Booking Update', 'The provider was unable to accept your request at this time. Please try another nearby provider.')
        """, (booking['user_id'],))
        flash(f'Booking #{booking_id} rejected.', 'warning')

    return redirect(url_for('provider.dashboard'))

@provider_bp.route('/booking/<int:booking_id>/status', methods=['POST'])
@role_required(['provider'])
def update_status(booking_id):
    new_status = request.form.get('status')
    valid_statuses = ['Accepted', 'Provider Assigned', 'On the Way', 'Service Started', 'Completed']
    
    if new_status not in valid_statuses:
        flash('Invalid status update.', 'danger')
        return redirect(url_for('provider.dashboard'))

    provider = query_db("SELECT provider_id, user_id FROM providers WHERE user_id = ?", (session['user_id'],), one=True)
    booking = query_db("SELECT * FROM bookings WHERE booking_id = ? AND provider_id = ?",
                       (booking_id, provider['provider_id']), one=True)
    
    if not booking:
        flash('Booking not found.', 'danger')
        return redirect(url_for('provider.dashboard'))

    execute_db("UPDATE bookings SET status = ? WHERE booking_id = ?", (new_status, booking_id))
    
    # Send notification to customer
    status_msg = {
        'Provider Assigned': 'A technician has been scheduled for your service.',
        'On the Way': 'The provider is now traveling to your location!',
        'Service Started': 'The provider has reached and work has started.',
        'Completed': 'Your service has been marked as Completed. Please leave a rating!'
    }.get(new_status, f'Your booking status changed to {new_status}.')

    execute_db("""
        INSERT INTO notifications (user_id, title, message)
        VALUES (?, 'Service Progress Update', ?)
    """, (booking['user_id'], status_msg))

    flash(f'Booking #{booking_id} status updated to "{new_status}".', 'success')
    return redirect(url_for('provider.dashboard'))
