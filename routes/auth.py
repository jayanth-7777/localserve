from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g
from werkzeug.security import generate_password_hash, check_password_hash
from database import query_db, execute_db
from config import Config

auth_bp = Blueprint('auth', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this feature.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def role_required(allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in first.', 'warning')
                return redirect(url_for('auth.login', next=request.url))
            if session.get('user_role') not in allowed_roles:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('customer.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        user = query_db("SELECT * FROM users WHERE LOWER(email) = ?", (email,), one=True)
        if user and check_password_hash(user['password_hash'], password):
            session.clear()
            session['user_id'] = user['user_id']
            session['user_name'] = user['name']
            session['user_email'] = user['email']
            session['user_role'] = user['role']
            session['user_lat'] = user['latitude'] or Config.DEFAULT_LAT
            session['user_lng'] = user['longitude'] or Config.DEFAULT_LNG
            session['user_phone'] = user['phone']

            # If provider, cache provider_id
            if user['role'] == 'provider':
                p = query_db("SELECT provider_id, verification_status FROM providers WHERE user_id = ?", (user['user_id'],), one=True)
                if p:
                    session['provider_id'] = p['provider_id']
                    session['provider_status'] = p['verification_status']
                return redirect(url_for('provider.dashboard'))

            # If pharmacy, cache pharmacy_id
            elif user['role'] == 'pharmacy':
                ph = query_db("SELECT pharmacy_id, verification_status FROM pharmacies WHERE user_id = ?", (user['user_id'],), one=True)
                if ph:
                    session['pharmacy_id'] = ph['pharmacy_id']
                    session['pharmacy_status'] = ph['verification_status']
                return redirect(url_for('pharmacy.dashboard'))

            # If admin
            elif user['role'] == 'admin':
                return redirect(url_for('admin.dashboard'))

            # Default customer
            next_url = request.args.get('next') or url_for('customer.dashboard')
            return redirect(next_url)
        else:
            flash('Invalid email or password. Please try again.', 'danger')

    return render_template('login.html')

@auth_bp.route('/quick-login/<role>')
def quick_login(role):
    """Convenience endpoint for evaluators and testers to quickly test different roles."""
    role_emails = {
        'customer': 'customer@localserve.com',
        'provider': 'ramesh@provider.com',
        'pharmacy': 'balaji@pharmacy.com',
        'admin': 'admin@localserve.com'
    }
    target_email = role_emails.get(role)
    if not target_email:
        flash('Invalid demo role selected.', 'warning')
        return redirect(url_for('auth.login'))

    user = query_db("SELECT * FROM users WHERE email = ?", (target_email,), one=True)
    if user:
        session.clear()
        session['user_id'] = user['user_id']
        session['user_name'] = user['name']
        session['user_email'] = user['email']
        session['user_role'] = user['role']
        session['user_lat'] = user['latitude'] or Config.DEFAULT_LAT
        session['user_lng'] = user['longitude'] or Config.DEFAULT_LNG
        session['user_phone'] = user['phone']

        if user['role'] == 'provider':
            p = query_db("SELECT provider_id, verification_status FROM providers WHERE user_id = ?", (user['user_id'],), one=True)
            if p:
                session['provider_id'] = p['provider_id']
                session['provider_status'] = p['verification_status']
            return redirect(url_for('provider.dashboard'))

        elif user['role'] == 'pharmacy':
            ph = query_db("SELECT pharmacy_id, verification_status FROM pharmacies WHERE user_id = ?", (user['user_id'],), one=True)
            if ph:
                session['pharmacy_id'] = ph['pharmacy_id']
                session['pharmacy_status'] = ph['verification_status']
            return redirect(url_for('pharmacy.dashboard'))

        elif user['role'] == 'admin':
            return redirect(url_for('admin.dashboard'))

        return redirect(url_for('customer.dashboard'))

    flash('Demo user not found. Please run seed script.', 'danger')
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    services = query_db("SELECT * FROM services ORDER BY name ASC")
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        role = request.form.get('role', 'customer')
        address = request.form.get('address', '').strip()
        latitude = request.form.get('latitude', Config.DEFAULT_LAT)
        longitude = request.form.get('longitude', Config.DEFAULT_LNG)

        try:
            latitude = float(latitude) if latitude else Config.DEFAULT_LAT
            longitude = float(longitude) if longitude else Config.DEFAULT_LNG
        except ValueError:
            latitude, longitude = Config.DEFAULT_LAT, Config.DEFAULT_LNG

        # Check existing user
        existing = query_db("SELECT user_id FROM users WHERE LOWER(email) = ?", (email,), one=True)
        if existing:
            flash('An account with this email already exists. Please login.', 'warning')
            return redirect(url_for('auth.login'))

        pwd_hash = generate_password_hash(password)
        user_id = execute_db("""
            INSERT INTO users (name, email, phone, password_hash, role, latitude, longitude, address)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, email, phone, pwd_hash, role, latitude, longitude, address))

        # Handle Provider specific fields
        if role == 'provider':
            category = request.form.get('category', 'Electrician')
            experience = int(request.form.get('experience_years', 2))
            charges = float(request.form.get('charges_per_hr', 150))
            bio = request.form.get('bio', '')

            execute_db("""
                INSERT INTO providers (user_id, category, experience_years, charges_per_hr, availability, verification_status, latitude, longitude, address, bio)
                VALUES (?, ?, ?, ?, 'Available', 'Pending', ?, ?, ?, ?)
            """, (user_id, category, experience, charges, latitude, longitude, address, bio))
            flash('Provider registration submitted! Account is pending admin verification.', 'success')

        # Handle Pharmacy specific fields
        elif role == 'pharmacy':
            pharmacy_name = request.form.get('pharmacy_name', name)
            timings = request.form.get('timings', '8:00 AM - 10:00 PM')

            execute_db("""
                INSERT INTO pharmacies (user_id, name, phone, address, latitude, longitude, verification_status, timings)
                VALUES (?, ?, ?, ?, ?, ?, 'Pending', ?)
            """, (user_id, pharmacy_name, phone, address, latitude, longitude, timings))
            flash('Pharmacy registered successfully! Account is pending admin verification.', 'success')

        else:
            flash('Customer registration successful! Please login.', 'success')

        return redirect(url_for('auth.login'))

    return render_template('register.html', services=services)

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('customer.index'))
