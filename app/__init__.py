import os
from flask import Flask
from app.config import config_map
from app.extensions import db, login_manager


def create_app(env: str = None):
    app = Flask(__name__)

    env = env or os.getenv('FLASK_ENV', 'default')
    app.config.from_object(config_map[env])

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '로그인이 필요합니다.'
    login_manager.login_message_category = 'warning'

    # User loader
    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Blueprints
    from app.routes.auth_routes import auth_bp
    from app.routes.oauth_routes import oauth_bp, init_oauth
    from app.routes.memory_routes import memories_bp
    from app.routes.comment_routes import comment_bp
    from app.routes.couple_routes import couple_bp
    from app.routes.admin_routes import admin_bp

    init_oauth(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(oauth_bp)
    app.register_blueprint(memories_bp)
    app.register_blueprint(comment_bp)
    app.register_blueprint(couple_bp)
    app.register_blueprint(admin_bp)

    with app.app_context():
        db.create_all()

    return app
