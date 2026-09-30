import os
from flask import Flask, render_template, session
from config import Config
from database import close_db, init_db, query_db
from utils import time_ago

from routes.auth import auth_bp
from routes.customer import customer_bp
from routes.provider import provider_bp
from routes.pharmacy import pharmacy_bp
from routes.admin import admin_bp
from routes.api import api_bp
from routes.skillshare import skillshare_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize DB tables if not present
    if not os.path.exists(Config.DATABASE_PATH):
        with app.app_context():
            init_db()

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(customer_bp)
    app.register_blueprint(provider_bp)
    app.register_blueprint(pharmacy_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(skillshare_bp)

    # Teardown database connection
    app.teardown_appcontext(close_db)

    # Template filters
    @app.template_filter('timeago')
    def timeago_filter(dt):
        return time_ago(dt)

    # Global context processor
    @app.context_processor
    def inject_global_data():
        unread_notifications = 0
        if 'user_id' in session:
            note_row = query_db("""
                SELECT COUNT(*) as c FROM notifications
                WHERE user_id = ? AND is_read = 0
            """, (session['user_id'],), one=True)
            if note_row:
                unread_notifications = note_row['c']
        
        all_services = query_db("SELECT * FROM services ORDER BY name ASC")
        all_skills = query_db("SELECT * FROM skill_categories ORDER BY name ASC")
        
        return dict(
            unread_notifications=unread_notifications,
            global_services=all_services,
            global_skills=all_skills
        )

    # 404 Error handler
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('base.html', not_found=True), 404

    return app

if __name__ == '__main__':
    app = create_app()
    print("==================================================")
    print("LOCALServe 2.0: Community Services & SkillShare Running")
    print("Access locally at: http://127.0.0.1:5000")
    print("==================================================")
    app.run(debug=True, host='127.0.0.1', port=5000)
