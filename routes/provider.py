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

    # 1. Incoming Pending Requests (status = 'Requested') with problem photo
    pending_bookings = query_db("""
        SELECT b.*, u.name as customer_name, u.phone as customer_phone, u.address as customer_addr
        FROM bookings b
        JOIN users u ON b.user_id = u.user_id
        WHERE b.provider_id = ? AND b.status = 'Requested'
        ORDER BY b.created_at DESC
    """, (pid,))

    # 2. Active Ongoing Bookings
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

    # 5. Skill Mentor Mode details
    mentor = query_db("SELECT * FROM mentor_profiles WHERE provider_id = ?", (pid,), one=True)
    mentor_courses = []
    mentor_sessions = []
    if mentor:
        mentor_courses = query_db("""
            SELECT c.*, sc.name as category_name,
                   (SELECT COUNT(*) FROM enrollments WHERE course_id = c.course_id) as enrolled_count
            FROM courses c
            JOIN skill_categories sc ON c.skill_id = sc.skill_id
            WHERE c.mentor_id = ?
            ORDER BY c.course_id DESC
        """, (mentor['mentor_id'],))
        
        mentor_sessions = query_db("""
            SELECT ts.*, c.title as course_title,
                   (SELECT COUNT(*) FROM session_registrations WHERE session_id = ts.session_id) as registered_count
            FROM training_sessions ts
            LEFT JOIN courses c ON ts.course_id = c.course_id
            WHERE ts.mentor_id = ?
            ORDER BY ts.date ASC
        """, (mentor['mentor_id'],))

    # All Skill Categories for Course Creation
    skill_categories = query_db("SELECT * FROM skill_categories ORDER BY name ASC")

    stats = {
        'total_completed': len([b for b in history_bookings if b['status'] == 'Completed']),
        'total_active': len(active_bookings),
        'total_pending': len(pending_bookings),
        'rating': provider['rating'] or 5.0,
        'rating_count': provider['rating_count'] or 0,
        'learners_taught': mentor['total_learners'] if mentor else 0
    }

    return render_template(
        'provider_dashboard.html',
        provider=provider,
        pending_bookings=pending_bookings,
        active_bookings=active_bookings,
        history_bookings=history_bookings,
        reviews=reviews,
        stats=stats,
        mentor=mentor,
        mentor_courses=mentor_courses,
        mentor_sessions=mentor_sessions,
        skill_categories=skill_categories
    )

@provider_bp.route('/toggle-availability', methods=['POST'])
@role_required(['provider'])
def toggle_availability():
    provider = query_db("SELECT verification_status FROM providers WHERE user_id = ?", (session['user_id'],), one=True)
    if provider and provider['verification_status'] != 'Verified':
        flash('Your profile is currently pending Administrator verification. Status changes will be unlocked once approved.', 'warning')
        return redirect(url_for('provider.dashboard'))

    new_status = request.form.get('availability', 'Available')
    if new_status not in ['Available', 'Busy', 'Offline']:
        new_status = 'Available'
        
    execute_db("UPDATE providers SET availability = ? WHERE user_id = ?",
               (new_status, session['user_id']))
    flash(f'Your status is now updated to: {new_status}', 'info')
    return redirect(url_for('provider.dashboard'))

@provider_bp.route('/toggle-mentor-mode', methods=['POST'])
@role_required(['provider'])
def toggle_mentor_mode():
    provider = query_db("SELECT provider_id, experience_years FROM providers WHERE user_id = ?", (session['user_id'],), one=True)
    existing = query_db("SELECT mentor_id FROM mentor_profiles WHERE provider_id = ?", (provider['provider_id'],), one=True)

    bio = request.form.get('bio', 'Certified SevaSetu skill mentor teaching practical trade skills.').strip()
    languages = request.form.get('languages', 'Telugu, English').strip()
    teaching_mode = request.form.get('teaching_mode', 'In-Person')
    is_free = 1 if request.form.get('is_community_free') == 'on' else 0

    if existing:
        execute_db("""
            UPDATE mentor_profiles
            SET bio = ?, languages = ?, teaching_mode = ?, is_community_free = ?
            WHERE mentor_id = ?
        """, (bio, languages, teaching_mode, is_free, existing['mentor_id']))
        flash('Skill Mentor profile updated!', 'success')
    else:
        execute_db("""
            INSERT INTO mentor_profiles (provider_id, bio, experience_years, teaching_mode, languages, is_community_free, verification_status)
            VALUES (?, ?, ?, ?, ?, ?, 'Verified')
        """, (provider['provider_id'], bio, provider['experience_years'], teaching_mode, languages, is_free))
        flash('🎉 Skill Mentor Mode activated! You can now publish courses and conduct workshops.', 'success')

    return redirect(url_for('provider.dashboard'))

@provider_bp.route('/course/create', methods=['POST'])
@role_required(['provider'])
def create_course():
    provider = query_db("SELECT provider_id FROM providers WHERE user_id = ?", (session['user_id'],), one=True)
    mentor = query_db("SELECT mentor_id FROM mentor_profiles WHERE provider_id = ?", (provider['provider_id'],), one=True)
    
    if not mentor:
        flash('Please enable Skill Mentor Mode first.', 'warning')
        return redirect(url_for('provider.dashboard'))

    skill_id = request.form.get('skill_id')
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    level = request.form.get('level', 'Beginner')
    duration = request.form.get('duration', '3 Days').strip()
    fee = float(request.form.get('fee', 0.0))
    mode = request.form.get('mode', 'In-Person')
    location = request.form.get('location', 'Mentor Workshop / Community Center').strip()
    safety = request.form.get('safety_instructions', 'Always wear protective gear and ensure electrical/water supplies are turned off before beginning repairs.').strip()

    cid = execute_db("""
        INSERT INTO courses (mentor_id, skill_id, title, description, level, duration, fee, mode, location, safety_instructions)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (mentor['mentor_id'], skill_id, title, description, level, duration, fee, mode, location, safety))

    # Add default intro lesson
    execute_db("""
        INSERT INTO course_lessons (course_id, title, description, content, safety_warning, lesson_order)
        VALUES (?, 'Lesson 1: Introduction, Safety & Tools Overview', 'Familiarize yourself with basic tools and personal safety gear.',
                'Inspect all tools before beginning. Always disconnect electrical or water mains before troubleshooting.',
                'Safety First: Never work with bare hands on live circuits or pressurized lines.', 1)
    """, (cid,))

    flash(f'Course "{title}" created! Initial lesson has been added.', 'success')
    return redirect(url_for('provider.dashboard'))

@provider_bp.route('/course/<int:course_id>/lesson/add', methods=['POST'])
@role_required(['provider'])
def add_lesson(course_id):
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    content = request.form.get('content', '').strip()
    video_url = request.form.get('video_url', '').strip()
    safety_warning = request.form.get('safety_warning', '').strip()
    order = int(request.form.get('lesson_order', 2))

    execute_db("""
        INSERT INTO course_lessons (course_id, title, description, content, video_url, safety_warning, lesson_order)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (course_id, title, description, content, video_url, safety_warning, order))

    flash('New lesson added to course syllabus!', 'success')
    return redirect(url_for('provider.dashboard'))

@provider_bp.route('/session/create', methods=['POST'])
@role_required(['provider'])
def create_session():
    provider = query_db("SELECT provider_id FROM providers WHERE user_id = ?", (session['user_id'],), one=True)
    mentor = query_db("SELECT mentor_id FROM mentor_profiles WHERE provider_id = ?", (provider['provider_id'],), one=True)
    
    if not mentor:
        flash('Please enable Skill Mentor Mode first.', 'warning')
        return redirect(url_for('provider.dashboard'))

    course_id = request.form.get('course_id') or None
    title = request.form.get('title', '').strip()
    date = request.form.get('date')
    time = request.form.get('time', '10:00 AM - 1:00 PM').strip()
    location = request.form.get('location', 'Village Community Hall').strip()
    capacity = int(request.form.get('capacity', 20))
    fee = float(request.form.get('fee', 0.0))

    execute_db("""
        INSERT INTO training_sessions (course_id, mentor_id, title, date, time, location, capacity, available_seats, fee, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Scheduled')
    """, (course_id, mentor['mentor_id'], title, date, time, location, capacity, capacity, fee))

    flash(f'Community Workshop "{title}" scheduled for {date}!', 'success')
    return redirect(url_for('provider.dashboard'))

@provider_bp.route('/booking/<int:booking_id>/respond', methods=['POST'])
@role_required(['provider'])
def respond_booking(booking_id):
    action = request.form.get('action')
    provider = query_db("SELECT provider_id FROM providers WHERE user_id = ?", (session['user_id'],), one=True)
    
    booking = query_db("SELECT * FROM bookings WHERE booking_id = ? AND provider_id = ?",
                       (booking_id, provider['provider_id']), one=True)
    if not booking:
        flash('Booking not found or not assigned to you.', 'danger')
        return redirect(url_for('provider.dashboard'))

    if action == 'accept':
        execute_db("UPDATE bookings SET status = 'Accepted' WHERE booking_id = ?", (booking_id,))
        execute_db("""
            INSERT INTO notifications (user_id, title, message)
            VALUES (?, 'Booking Accepted!', 'The provider has accepted your service request. Expected arrival: 15–30 mins.')
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

    provider = query_db("SELECT provider_id FROM providers WHERE user_id = ?", (session['user_id'],), one=True)
    booking = query_db("SELECT * FROM bookings WHERE booking_id = ? AND provider_id = ?",
                       (booking_id, provider['provider_id']), one=True)
    
    if not booking:
        flash('Booking not found.', 'danger')
        return redirect(url_for('provider.dashboard'))

    execute_db("UPDATE bookings SET status = ? WHERE booking_id = ?", (new_status, booking_id))
    
    status_msg = {
        'Provider Assigned': 'A technician has been scheduled for your service.',
        'On the Way': 'The provider is now traveling to your location! Expected arrival: 10–20 mins.',
        'Service Started': 'The provider has reached your location and work has started.',
        'Completed': 'Your service has been marked as Completed. Please leave a rating & review!'
    }.get(new_status, f'Your booking status changed to {new_status}.')

    execute_db("""
        INSERT INTO notifications (user_id, title, message)
        VALUES (?, 'Service Progress Update', ?)
    """, (booking['user_id'], status_msg))

    flash(f'Booking #{booking_id} status updated to "{new_status}".', 'success')
    return redirect(url_for('provider.dashboard'))
