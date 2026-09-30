import os
import datetime
import uuid
from werkzeug.utils import secure_filename
from config import Config

def time_ago(dt_val):
    """Convert datetime or ISO string to friendly relative time string."""
    if not dt_val:
        return "Not available"
    if isinstance(dt_val, str):
        try:
            dt = datetime.datetime.fromisoformat(dt_val.replace('Z', '+00:00'))
        except Exception:
            try:
                dt = datetime.datetime.strptime(dt_val, "%Y-%m-%d %H:%M:%S")
            except Exception:
                return dt_val
    else:
        dt = dt_val

    now = datetime.datetime.now()
    diff = now - dt

    seconds = int(diff.total_seconds())
    if seconds < 0:
        return "Just now"
    if seconds < 60:
        return f"{seconds} seconds ago"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes} min{'s' if minutes != 1 else ''} ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours} hr{'s' if hours != 1 else ''} ago"
    days = hours // 24
    if days == 1:
        return "Yesterday"
    if days < 7:
        return f"{days} days ago"
    return dt.strftime("%d %b %Y")

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def save_prescription(file):
    if file and file.filename and allowed_file(file.filename):
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        filename = secure_filename(f"rx_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        file.save(filepath)
        return filename
    return None

def save_problem_photo(file):
    if file and file.filename and allowed_file(file.filename):
        os.makedirs(Config.PROBLEM_UPLOAD_FOLDER, exist_ok=True)
        filename = secure_filename(f"prob_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
        filepath = os.path.join(Config.PROBLEM_UPLOAD_FOLDER, filename)
        file.save(filepath)
        return filename
    return None

def generate_cert_number(category_code="SKL"):
    year = datetime.datetime.now().year
    rand_suffix = uuid.uuid4().hex[:6].upper()
    return f"LS-{category_code[:3].upper()}-{year}-{rand_suffix}"

def generate_verification_code():
    return uuid.uuid4().hex[:12].lower()
