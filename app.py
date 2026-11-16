import os
from flask import Flask, render_template, redirect, url_for, g
from config import Config
from database.db import (
    init_db, seed_admin_user, get_user_by_email, get_all_users,
    get_all_events, get_tickets_by_user_id, get_ticket_statistics, get_all_tickets
)
from utils.auth_utils import hash_password, get_current_user_from_request, login_required, admin_required
from routes.auth_routes import auth_bp
from routes.event_routes import event_bp
from routes.admin_event_routes import admin_event_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # 1. Initialize Database & Seed Default Admin on Startup
    with app.app_context():
        init_db()
        admin = get_user_by_email(Config.ADMIN_DEFAULT_EMAIL)
        if not admin:
            hashed_admin_pw = hash_password(Config.ADMIN_DEFAULT_PASSWORD)
            seed_admin_user(
                name=Config.ADMIN_DEFAULT_NAME,
                email=Config.ADMIN_DEFAULT_EMAIL,
                password_hash=hashed_admin_pw
            )

    # 2. Register Blueprints (Phase 1 & Phase 2)
    app.register_blueprint(auth_bp)
    app.register_blueprint(event_bp)
    app.register_blueprint(admin_event_bp)

    # 3. Global Context Processor: Makes current_user accessible in all Jinja templates
    @app.context_processor
    def inject_user():
        user = get_current_user_from_request()
        return dict(current_user=user)

    # 4. Core Landing & Demonstration Routes: Unauthenticated users see Login first
    @app.route('/')
    def index():
        user = get_current_user_from_request()
        if user:
            if user.get('role') == 'Admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('dashboard'))
        return redirect(url_for('auth.login'))

    @app.route('/dashboard')
    @login_required
    def dashboard():
        """Customer Dashboard: Protected by JWT (@login_required)"""
        events = get_all_events()
        my_tickets_list = get_tickets_by_user_id(g.current_user['user_id'])
        return render_template('dashboard.html', user=g.current_user, events=events, my_tickets=my_tickets_list)

    @app.route('/admin')
    @admin_required
    def admin_dashboard():
        """Admin Dashboard: Protected by Role-Based Access Control (@admin_required)"""
        users_list = get_all_users()
        events = get_all_events()
        stats = get_ticket_statistics()
        tickets = get_all_tickets()
        return render_template(
            'admin_dashboard.html', 
            user=g.current_user, 
            users_list=users_list,
            events=events,
            stats=stats,
            tickets=tickets
        )

    return app

if __name__ == '__main__':
    app = create_app()
    print("=" * 65)
    print("  CrypTix E-Ticketing System - Phase 1 & 2 Active")
    print(f"  * Default Admin:    {Config.ADMIN_DEFAULT_EMAIL}")
    print(f"  * Default Password: {Config.ADMIN_DEFAULT_PASSWORD}")
    print("  * Access Server:    http://127.0.0.1:5000")
    print("=" * 65)
    app.run(host='127.0.0.1', port=5000, debug=True)
