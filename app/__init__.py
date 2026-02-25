import os
from flask import Flask
from app.config import config_map
from app.extensions import db, login_manager


def create_app(env: str = None):
    app = Flask(__name__)

    env = env or os.getenv('FLASK_ENV', 'default')
    app.config.from_object(config_map[env])

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '로그인이 필요합니다.'
    login_manager.login_message_category = 'warning'

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from app.routes.auth import auth_bp
    from app.routes.memories import memories_bp
    from app.routes.couple import couple_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(memories_bp)
    app.register_blueprint(couple_bp)

    with app.app_context():
        db.create_all()

    return app
