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
        try:
            return User.query.get(int(user_id))
        except Exception:
            return None

    # Blueprints
    from app.routes.auth_routes import auth_bp
    from app.routes.oauth_routes import oauth_bp, init_oauth
    from app.routes.memory_routes import memories_bp
    from app.routes.comment_routes import comment_bp
    from app.routes.couple_routes import couple_bp
    from app.routes.admin_routes import admin_bp
    from app.routes.profile_routes import profile_bp

    init_oauth(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(oauth_bp)
    app.register_blueprint(memories_bp)
    app.register_blueprint(comment_bp)
    app.register_blueprint(couple_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(profile_bp)

    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            app.logger.warning(f'[DB] create_all 실패: {e}')
        _run_migrations(app)
        _ensure_admin(app)

    return app


def _run_migrations(app):
    """
    앱 시작 시 누락된 컬럼을 자동으로 추가합니다.
    PostgreSQL: ADD COLUMN IF NOT EXISTS 사용
    SQLite: 컬럼 없으면 추가 (OperationalError 무시)
    """
    from sqlalchemy import text, inspect

    # (테이블명, 컬럼명, 컬럼 타입)
    columns_to_add = [
        ('users',    'birthday',      'DATE'),
        ('users',    'favorite_food', 'VARCHAR(100)'),
        ('users',    'bio',           'TEXT'),
        ('users',    'mbti',          'VARCHAR(4)'),
        ('couples',  'pet_name',      'VARCHAR(50)'),
        ('memories', 'media_type',    "VARCHAR(10) DEFAULT 'image' NOT NULL"),
    ]

    db_url = str(app.config.get('SQLALCHEMY_DATABASE_URI', ''))
    is_pg  = db_url.startswith('postgresql')

    with app.app_context():
        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()

        for table, col, col_type in columns_to_add:
            if table not in existing_tables:
                continue
            existing_cols = [c['name'] for c in inspector.get_columns(table)]
            if col in existing_cols:
                continue
            try:
                if is_pg:
                    sql = f'ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col} {col_type}'
                else:
                    sql = f'ALTER TABLE {table} ADD COLUMN {col} {col_type}'
                db.session.execute(text(sql))
                db.session.commit()
                app.logger.info(f'[Migration] {table}.{col} 컬럼 추가 완료')
            except Exception as e:
                db.session.rollback()
                app.logger.warning(f'[Migration] {table}.{col} 추가 실패: {e}')


def _ensure_admin(app):
    """
    앱 시작 시 admin 계정 자동 생성 (없을 경우에만).
    환경변수: ADMIN_EMAIL, ADMIN_USERNAME, ADMIN_PASSWORD
    """
    from app.models import User
    try:
        admin_email = app.config['ADMIN_EMAIL']
        admin_user = User.query.filter_by(email=admin_email).first()
        if not admin_user:
            admin_user = User(
                username=app.config['ADMIN_USERNAME'],
                email=admin_email,
                is_admin=True,
            )
            admin_user.set_password(app.config['ADMIN_PASSWORD'])
            db.session.add(admin_user)
            db.session.commit()
            app.logger.info(f'[Admin] 관리자 계정 생성: {admin_email}')
        elif not admin_user.is_admin:
            admin_user.is_admin = True
            db.session.commit()
            app.logger.info(f'[Admin] 관리자 권한 복구: {admin_email}')
    except Exception as e:
        app.logger.warning(f'[Admin] 관리자 계정 초기화 실패: {e}')
