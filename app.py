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

        active_loc_id = session.get('active_location_id', 'gudlavalleru')
        active_loc = next((loc for loc in Config.LOCATIONS if loc['id'] == active_loc_id), Config.LOCATIONS[0])
        
        return dict(
            unread_notifications=unread_notifications,
            global_services=all_services,
            global_skills=all_skills,
            app_name=getattr(Config, 'APP_NAME', 'SevaSetu'),
            app_name_telugu=getattr(Config, 'APP_NAME_TELUGU', 'సేవాసేతు'),
            locations=getattr(Config, 'LOCATIONS', []),
            active_location=active_loc,
            community_name=active_loc['name'],
            community_pincode=active_loc['pincode'],
            community_district=getattr(Config, 'DISTRICT', 'Krishna District, Andhra Pradesh'),
            default_lat=session.get('user_lat', active_loc['lat']),
            default_lng=session.get('user_lng', active_loc['lng'])
        )

    # 404 Error handler
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('base.html', not_found=True), 404

    return app

if __name__ == '__main__':
    app = create_app()
    print("==================================================")
    print("SevaSetu: Community Services & SkillShare Platform")
    print("Regional Hubs: Gudlavalleru | Gudivada | Machilipatnam")
    print("Access locally at: http://127.0.0.1:5000")
    print("==================================================")
    app.run(debug=True, host='127.0.0.1', port=5000)
