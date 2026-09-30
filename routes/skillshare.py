import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from database import query_db, execute_db
from routes.auth import login_required
from utils import time_ago, generate_cert_number, generate_verification_code

skillshare_bp = Blueprint('skillshare', __name__, url_prefix='/skillshare')

@skillshare_bp.route('/')
def index():
    categories = query_db("SELECT * FROM skill_categories ORDER BY skill_id ASC")
    
    # Featured Courses
    courses = query_db("""
        SELECT c.*, sc.name as category_name, sc.icon as category_icon,
               u.name as mentor_name, u.phone as mentor_phone, mp.experience_years
        FROM courses c
        JOIN skill_categories sc ON c.skill_id = sc.skill_id
        JOIN mentor_profiles mp ON c.mentor_id = mp.mentor_id
        JOIN providers p ON mp.provider_id = p.provider_id
        JOIN users u ON p.user_id = u.user_id
        ORDER BY c.course_id DESC
        LIMIT 6
    """)

    # Upcoming Community Workshops
    workshops = query_db("""
        SELECT ts.*, c.title as course_title, u.name as mentor_name, sc.icon as category_icon
        FROM training_sessions ts
        LEFT JOIN courses c ON ts.course_id = c.course_id
        LEFT JOIN skill_categories sc ON c.skill_id = sc.skill_id
        JOIN mentor_profiles mp ON ts.mentor_id = mp.mentor_id
        JOIN providers p ON mp.provider_id = p.provider_id
        JOIN users u ON p.user_id = u.user_id
        WHERE ts.status = 'Scheduled'
        ORDER BY ts.date ASC
        LIMIT 4
    """)

    # Community Skill Impact Metrics
    impact = {
        'people_trained': 126 + query_db("SELECT COUNT(DISTINCT user_id) as c FROM enrollments", one=True)['c'],
        'courses_completed': 84 + query_db("SELECT COUNT(*) as c FROM enrollments WHERE status = 'Completed'", one=True)['c'],
        'local_skill_profiles': 32 + query_db("SELECT COUNT(*) as c FROM user_skill_profiles WHERE is_available_for_work = 1", one=True)['c'],
        'skill_exchanges': 18 + query_db("SELECT COUNT(*) as c FROM skill_exchanges WHERE status = 'Active'", one=True)['c'],
        'workshops_held': 14 + query_db("SELECT COUNT(*) as c FROM training_sessions WHERE status IN ('Scheduled', 'Completed')", one=True)['c'],
        'services_completed': 420 + query_db("SELECT COUNT(*) as c FROM bookings WHERE status = 'Completed'", one=True)['c'],
        'medicines_resolved': 310 + query_db("SELECT COUNT(*) as c FROM medicine_requests WHERE status IN ('Responded', 'Fulfilled')", one=True)['c']
    }

    # Top Mentors
    mentors = query_db("""
        SELECT mp.*, u.name, u.phone, p.category, p.rating, p.rating_count,
               COUNT(c.course_id) as total_courses
        FROM mentor_profiles mp
        JOIN providers p ON mp.provider_id = p.provider_id
        JOIN users u ON p.user_id = u.user_id
        LEFT JOIN courses c ON mp.mentor_id = c.mentor_id
        WHERE mp.verification_status = 'Verified'
        GROUP BY mp.mentor_id
        ORDER BY mp.total_learners DESC, p.rating DESC
        LIMIT 4
    """)

    return render_template(
        'skillshare_index.html',
        categories=categories,
        courses=courses,
        workshops=workshops,
        impact=impact,
        mentors=mentors
    )

@skillshare_bp.route('/courses')
def courses_list():
    cat_code = request.args.get('category', '')
    level = request.args.get('level', '')
    fee_type = request.args.get('fee', '')  # 'free' or 'paid'
    search = request.args.get('q', '').strip().lower()

    query = """
        SELECT c.*, sc.name as category_name, sc.category_code, sc.icon as category_icon,
               u.name as mentor_name, u.phone as mentor_phone, mp.teaching_mode,
               (SELECT COUNT(*) FROM course_lessons WHERE course_id = c.course_id) as lesson_count
        FROM courses c
        JOIN skill_categories sc ON c.skill_id = sc.skill_id
        JOIN mentor_profiles mp ON c.mentor_id = mp.mentor_id
        JOIN providers p ON mp.provider_id = p.provider_id
        JOIN users u ON p.user_id = u.user_id
        WHERE mp.verification_status = 'Verified'
    """
    params = []

    if cat_code:
        query += " AND sc.category_code = ?"
        params.append(cat_code)

    if level:
        query += " AND c.level = ?"
        params.append(level)

    if fee_type == 'free':
        query += " AND c.fee = 0"
    elif fee_type == 'paid':
        query += " AND c.fee > 0"

    if search:
        query += " AND (LOWER(c.title) LIKE ? OR LOWER(c.description) LIKE ? OR LOWER(sc.name) LIKE ?)"
        t = f"%{search}%"
        params.extend([t, t, t])

    query += " ORDER BY c.course_id DESC"

    courses = query_db(query, tuple(params))
    categories = query_db("SELECT * FROM skill_categories ORDER BY name ASC")

    return render_template(
        'courses.html',
        courses=courses,
        categories=categories,
        selected_category=cat_code,
        selected_level=level,
        selected_fee=fee_type,
        search_query=search
    )

@skillshare_bp.route('/course/<int:course_id>')
def course_detail(course_id):
    course = query_db("""
        SELECT c.*, sc.name as category_name, sc.category_code, sc.icon as category_icon,
               u.name as mentor_name, u.phone as mentor_phone, u.address as mentor_address,
               mp.bio as mentor_bio, mp.experience_years as mentor_exp, mp.languages,
               mp.teaching_mode, p.rating as mentor_rating, p.rating_count as mentor_reviews
        FROM courses c
        JOIN skill_categories sc ON c.skill_id = sc.skill_id
        JOIN mentor_profiles mp ON c.mentor_id = mp.mentor_id
        JOIN providers p ON mp.provider_id = p.provider_id
        JOIN users u ON p.user_id = u.user_id
        WHERE c.course_id = ?
    """, (course_id,), one=True)

    if not course:
        flash('Course not found.', 'danger')
        return redirect(url_for('skillshare.courses_list'))

    lessons = query_db("""
        SELECT * FROM course_lessons
        WHERE course_id = ?
        ORDER BY lesson_order ASC
    """, (course_id,))

    # Check if logged in user is enrolled
    enrollment = None
    if 'user_id' in session:
        enrollment = query_db("""
            SELECT * FROM enrollments
            WHERE course_id = ? AND user_id = ?
        """, (course_id, session['user_id']), one=True)

    return render_template(
        'course_detail.html',
        course=course,
        lessons=lessons,
        enrollment=enrollment
    )

@skillshare_bp.route('/course/<int:course_id>/enroll', methods=['POST'])
@login_required
def enroll_course(course_id):
    uid = session['user_id']
    course = query_db("SELECT * FROM courses WHERE course_id = ?", (course_id,), one=True)
    if not course:
        flash('Course not found.', 'danger')
        return redirect(url_for('skillshare.courses_list'))

    existing = query_db("SELECT enrollment_id FROM enrollments WHERE course_id = ? AND user_id = ?", (course_id, uid), one=True)
    if existing:
        flash('You are already enrolled in this course! Continue learning below.', 'info')
        return redirect(url_for('skillshare.learn', enrollment_id=existing['enrollment_id']))

    eid = execute_db("""
        INSERT INTO enrollments (course_id, user_id, status, progress, enrolled_at)
        VALUES (?, ?, 'Enrolled', 0, CURRENT_TIMESTAMP)
    """, (course_id, uid))

    # Update mentor total learners count
    execute_db("UPDATE mentor_profiles SET total_learners = total_learners + 1 WHERE mentor_id = ?", (course['mentor_id'],))

    flash('Congratulations! You are enrolled. Start your first lesson now.', 'success')
    return redirect(url_for('skillshare.learn', enrollment_id=eid))

@skillshare_bp.route('/learn/<int:enrollment_id>')
@login_required
def learn(enrollment_id):
    uid = session['user_id']
    enrollment = query_db("""
        SELECT e.*, c.title as course_title, c.safety_instructions, c.course_id,
               sc.name as category_name, sc.category_code, u.name as mentor_name
        FROM enrollments e
        JOIN courses c ON e.course_id = c.course_id
        JOIN skill_categories sc ON c.skill_id = sc.skill_id
        JOIN mentor_profiles mp ON c.mentor_id = mp.mentor_id
        JOIN providers p ON mp.provider_id = p.provider_id
        JOIN users u ON p.user_id = u.user_id
        WHERE e.enrollment_id = ? AND e.user_id = ?
    """, (enrollment_id, uid), one=True)

    if not enrollment:
        flash('Enrollment not found.', 'danger')
        return redirect(url_for('skillshare.index'))

    lessons = query_db("""
        SELECT cl.*,
               CASE WHEN lc.completion_id IS NOT NULL THEN 1 ELSE 0 END as is_completed
        FROM course_lessons cl
        LEFT JOIN lesson_completions lc ON cl.lesson_id = lc.lesson_id AND lc.enrollment_id = ?
        WHERE cl.course_id = ?
        ORDER BY cl.lesson_order ASC
    """, (enrollment_id, enrollment['course_id']))

    # Active lesson
    lesson_id = request.args.get('lesson_id', type=int)
    active_lesson = None
    if lesson_id:
        active_lesson = next((l for l in lessons if l['lesson_id'] == lesson_id), None)
    if not active_lesson and lessons:
        active_lesson = lessons[0]

    certificate = query_db("SELECT * FROM skill_certificates WHERE enrollment_id = ?", (enrollment_id,), one=True)

    return render_template(
        'learning_view.html',
        enrollment=enrollment,
        lessons=lessons,
        active_lesson=active_lesson,
        certificate=certificate
    )

@skillshare_bp.route('/learn/<int:enrollment_id>/lesson/<int:lesson_id>/complete', methods=['POST'])
@login_required
def complete_lesson(enrollment_id, lesson_id):
    uid = session['user_id']
    enrollment = query_db("SELECT * FROM enrollments WHERE enrollment_id = ? AND user_id = ?", (enrollment_id, uid), one=True)
    if not enrollment:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('skillshare.index'))

    # Mark lesson complete
    execute_db("""
        INSERT OR IGNORE INTO lesson_completions (enrollment_id, lesson_id, completed_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
    """, (enrollment_id, lesson_id))

    # Calculate total progress
    total_lessons = query_db("SELECT COUNT(*) as c FROM course_lessons WHERE course_id = ?", (enrollment['course_id'],), one=True)['c']
    completed_lessons = query_db("SELECT COUNT(*) as c FROM lesson_completions WHERE enrollment_id = ?", (enrollment_id,), one=True)['c']

    progress = int((completed_lessons / total_lessons) * 100) if total_lessons > 0 else 100
    status = 'Completed' if progress >= 100 else 'In Progress'
    completed_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') if progress >= 100 else None

    execute_db("""
        UPDATE enrollments
        SET progress = ?, status = ?, completed_at = COALESCE(?, completed_at)
        WHERE enrollment_id = ?
    """, (progress, status, completed_at, enrollment_id))

    # If 100% completed, auto-issue official LOCALServe Certificate
    cert = None
    if progress >= 100:
        existing_cert = query_db("SELECT * FROM skill_certificates WHERE enrollment_id = ?", (enrollment_id,), one=True)
        if not existing_cert:
            course = query_db("""
                SELECT c.*, sc.category_code
                FROM courses c
                JOIN skill_categories sc ON c.skill_id = sc.skill_id
                WHERE c.course_id = ?
            """, (enrollment['course_id'],), one=True)
            cert_num = generate_cert_number(course['category_code'])
            verif_code = generate_verification_code()
            execute_db("""
                INSERT INTO skill_certificates (enrollment_id, certificate_number, verification_code)
                VALUES (?, ?, ?)
            """, (enrollment_id, cert_num, verif_code))
            flash('🎉 Congratulations! You have completed the entire course! Your LOCALServe Certificate is ready!', 'success')
            return redirect(url_for('skillshare.certificate_view', cert_code=verif_code))

    flash('Lesson marked as completed!', 'success')
    return redirect(url_for('skillshare.learn', enrollment_id=enrollment_id, lesson_id=lesson_id))

@skillshare_bp.route('/certificate/<string:cert_code>', endpoint='certificate_view')
@skillshare_bp.route('/cert/<string:cert_code>', endpoint='view_certificate')
@skillshare_bp.route('/verify/<string:cert_code>', endpoint='verify_lookup')
def certificate_view(cert_code):
    cert = query_db("""
        SELECT sc.*, e.enrolled_at, e.completed_at,
               c.title as course_title, c.duration, c.level,
               cat.name as category_name,
               u_student.name as student_name, u_student.phone as student_phone,
               u_mentor.name as mentor_name, p.category as mentor_trade
        FROM skill_certificates sc
        JOIN enrollments e ON sc.enrollment_id = e.enrollment_id
        JOIN courses c ON e.course_id = c.course_id
        JOIN skill_categories cat ON c.skill_id = cat.skill_id
        JOIN users u_student ON e.user_id = u_student.user_id
        JOIN mentor_profiles mp ON c.mentor_id = mp.mentor_id
        JOIN providers p ON mp.provider_id = p.provider_id
        JOIN users u_mentor ON p.user_id = u_mentor.user_id
        WHERE sc.verification_code = ? OR sc.certificate_number = ?
    """, (cert_code, cert_code), one=True)

    if not cert:
        flash('Invalid certificate code or number.', 'danger')
        return redirect(url_for('skillshare.verify_page'))

    return render_template('certificate.html', cert=cert)

@skillshare_bp.route('/verify', methods=['GET', 'POST'])
def verify_page():
    cert_id = request.args.get('cert_id') or request.form.get('cert_id')
    if cert_id:
        return redirect(url_for('skillshare.certificate_view', cert_code=cert_id.strip()))
    return render_template('certificate_verify.html')

@skillshare_bp.route('/workshops')
def workshops_list():
    workshops = query_db("""
        SELECT ts.*, (ts.capacity - ts.available_seats) as registered_count,
               c.title as course_title, c.duration,
               sc.name as category_name, sc.icon as category_icon,
               u.name as mentor_name, u.phone as mentor_phone, p.rating
        FROM training_sessions ts
        LEFT JOIN courses c ON ts.course_id = c.course_id
        LEFT JOIN skill_categories sc ON c.skill_id = sc.skill_id
        JOIN mentor_profiles mp ON ts.mentor_id = mp.mentor_id
        JOIN providers p ON mp.provider_id = p.provider_id
        JOIN users u ON p.user_id = u.user_id
        ORDER BY ts.date ASC
    """)

    my_registrations = []
    if 'user_id' in session:
        my_reg_rows = query_db("SELECT session_id FROM session_registrations WHERE user_id = ?", (session['user_id'],))
        my_registrations = [r['session_id'] for r in my_reg_rows]

    return render_template('workshops.html', workshops=workshops, my_registrations=my_registrations)

@skillshare_bp.route('/workshop/<int:session_id>/register', methods=['POST'], endpoint='register_workshop')
@skillshare_bp.route('/session/<int:session_id>/register', methods=['POST'], endpoint='register_session')
@login_required
def register_workshop(session_id):
    uid = session['user_id']
    workshop = query_db("SELECT * FROM training_sessions WHERE session_id = ?", (session_id,), one=True)
    if not workshop or workshop['available_seats'] <= 0:
        flash('Workshop is full or no longer available.', 'warning')
        return redirect(url_for('skillshare.workshops_list'))

    execute_db("""
        INSERT OR IGNORE INTO session_registrations (session_id, user_id, status)
        VALUES (?, ?, 'Confirmed')
    """, (session_id, uid))

    # Decrement seats
    execute_db("""
        UPDATE training_sessions
        SET available_seats = available_seats - 1
        WHERE session_id = ? AND available_seats > 0
    """, (session_id,))

    flash(f"Seat successfully reserved for '{workshop['title']}'! Details have been saved to your dashboard.", 'success')
    return redirect(url_for('skillshare.workshops_list'))

@skillshare_bp.route('/exchange', endpoint='skill_exchange')
@skillshare_bp.route('/skill-exchange', endpoint='skill_exchange_list')
def skill_exchange():
    exchanges = query_db("""
        SELECT se.*, u.name as user_name, u.phone as user_phone, u.address as user_address
        FROM skill_exchanges se
        JOIN users u ON se.user_id = u.user_id
        WHERE se.status = 'Active'
        ORDER BY se.created_at DESC
    """)
    return render_template('skill_exchange.html', exchanges=exchanges)

@skillshare_bp.route('/exchange/post', methods=['POST'])
@login_required
def post_exchange():
    teach_skill = request.form.get('teach_skill', '').strip()
    learn_skill = request.form.get('learn_skill', '').strip()
    notes = request.form.get('notes', '').strip()

    if teach_skill and learn_skill:
        execute_db("""
            INSERT INTO skill_exchanges (user_id, teach_skill, learn_skill, notes, status)
            VALUES (?, ?, ?, ?, 'Active')
        """, (session['user_id'], teach_skill, learn_skill, notes))
        flash('Your skill exchange proposal has been posted on the community board!', 'success')
    else:
        flash('Please specify both the skill you can teach and what you want to learn.', 'warning')

    return redirect(url_for('skillshare.skill_exchange'))

@skillshare_bp.route('/activate-work-profile', methods=['POST'])
@login_required
def activate_work_profile():
    uid = session['user_id']
    skill_name = request.form.get('skill_name', '').strip()
    cert_id = request.form.get('certificate_id')
    rate = float(request.form.get('hourly_rate', 120))
    bio = request.form.get('bio', 'Certified via LOCALServe SkillShare practical course.')

    execute_db("""
        INSERT INTO user_skill_profiles (user_id, skill_name, certificate_id, is_available_for_work, hourly_rate, bio)
        VALUES (?, ?, ?, 1, ?, ?)
    """, (uid, skill_name, cert_id, rate, bio))

    flash('Your Local Skill Profile is now active! Neighbors can view your availability for local work.', 'success')
    return redirect(url_for('customer.dashboard'))
