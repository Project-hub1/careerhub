from flask import Flask, render_template, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix
from config import Config
from flask_login import current_user
from .extensions import db, login_manager, migrate, csrf


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    # Trust the reverse proxy headers used by Render/Railway/Nginx so HTTPS URLs
    # and redirects are generated correctly behind the platform proxy.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)
    if app.config.get('ENV') == 'production' and app.config.get('SECRET_KEY') == 'dev-secret-change-me':
        raise RuntimeError('SECRET_KEY must be set in production.')
    import os
    os.makedirs(os.path.join(app.instance_path, 'uploads', 'resumes'), exist_ok=True)
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    from .models import User
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from .main.routes import main_bp
    from .auth.routes import auth_bp
    from .jobs.routes import jobs_bp
    from .candidate.routes import candidate_bp
    from .recruiter.routes import recruiter_bp
    from .admin.routes import admin_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(jobs_bp)
    app.register_blueprint(candidate_bp)
    app.register_blueprint(recruiter_bp)
    app.register_blueprint(admin_bp)

    @app.template_filter('lpa_range')
    def lpa_range(minimum, maximum):
        if minimum is None and maximum is None:
            return 'Salary not disclosed'
        if minimum is None:
            return f'Up to ₹{maximum / 100000:.1f} LPA'
        if maximum is None:
            return f'₹{minimum / 100000:.1f}+ LPA'
        return f'₹{minimum / 100000:.1f}–{maximum / 100000:.1f} LPA'

    @app.template_filter('experience_range')
    def experience_range(minimum, maximum):
        minimum = 0 if minimum is None else minimum
        if maximum is None:
            return f'{minimum:g}+ years'
        return f'{minimum:g}–{maximum:g} years'

    @app.context_processor
    def inject_nav_state():
        unread_notifications = 0
        unread_messages = 0
        if getattr(current_user, 'is_authenticated', False):
            from .models import Notification, Message
            unread_notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
            unread_messages = Message.query.filter_by(receiver_id=current_user.id, is_read=False).count()
        return {'unread_notifications': unread_notifications, 'unread_messages': unread_messages}

    # Fresh installs get a usable schema immediately; Flask-Migrate remains available for future schema evolution.
    with app.app_context():
        db.create_all()

    @app.route('/health')
    def health():
        return jsonify({'status': 'ok', 'service': 'careerhub'})

    @app.errorhandler(403)
    def forbidden(e): return render_template('error.html', code=403, message='You do not have permission to access this page.'), 403
    @app.errorhandler(404)
    def not_found(e): return render_template('error.html', code=404, message='The page you requested was not found.'), 404
    @app.errorhandler(405)
    def method_not_allowed(e): return render_template('error.html', code=405, message='This method is not allowed.'), 405
    @app.errorhandler(413)
    def too_large(e): return render_template('error.html', code=413, message='The uploaded file is too large.'), 413
    @app.errorhandler(500)
    def server_error(e): return render_template('error.html', code=500, message='Something went wrong on the server.'), 500

    from .cli import register_cli
    register_cli(app)
    return app
