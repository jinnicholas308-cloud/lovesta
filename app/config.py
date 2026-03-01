import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

# 프로젝트 루트 절대경로 (config.py 기준 두 단계 위)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _fix_db_url(url: str) -> str:
    """Railway/Render/Heroku 는 postgres:// 제공 → SQLAlchemy 는 postgresql:// 필요"""
    if url and url.startswith('postgres://'):
        return url.replace('postgres://', 'postgresql://', 1)
    return url


def _resolve_upload_dir() -> str:
    env_val = os.getenv('UPLOAD_DIR')
    if env_val:
        return os.path.abspath(env_val)
    return os.path.join(BASE_DIR, 'storage', 'uploads')


def _get_db_url() -> str:
    """
    DB URL 우선순위:
    1. DATABASE_URL 환경변수 (Railway PostgreSQL 플러그인 참조변수)
    2. DATABASE_PUBLIC_URL (Railway Postgres 퍼블릭 URL — 참조변수 실패 시 대응)
    3. 개별 PGHOST/PGPORT/PGDATABASE/PGUSER/PGPASSWORD 로 직접 구성
    4. SQLite fallback (로컬 개발 / DB 미연결 상태에서도 앱 기동)
    """
    for var in ('DATABASE_URL', 'DATABASE_PUBLIC_URL'):
        url = os.getenv(var) or ''
        if url:
            return _fix_db_url(url)

    pg_host = os.getenv('PGHOST') or os.getenv('RAILWAY_PRIVATE_DOMAIN')
    pg_port = os.getenv('PGPORT', '5432')
    pg_db   = os.getenv('PGDATABASE')
    pg_user = os.getenv('PGUSER')
    pg_pass = os.getenv('PGPASSWORD') or ''
    if pg_host and pg_db and pg_user:
        return f'postgresql://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}'

    return f'sqlite:///{os.path.join(BASE_DIR, "lovesta.db")}'


_DB_URL = _get_db_url()


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = _DB_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = _resolve_upload_dir()
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 100 * 1024 * 1024))  # 100MB (동영상)

    # PostgreSQL 연결 안정성 (Railway 재시작 후 끊긴 커넥션 자동 복구)
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }

    # 세션 설정 (로그인 유지)
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)
    REMEMBER_COOKIE_DURATION = timedelta(days=30)

    # ── 보안 설정 ──
    SESSION_COOKIE_HTTPONLY = True          # JS에서 쿠키 접근 차단
    SESSION_COOKIE_SAMESITE = 'Lax'        # CSRF 보호
    REMEMBER_COOKIE_HTTPONLY = True         # remember me 쿠키 JS 접근 차단
    REMEMBER_COOKIE_SAMESITE = 'Lax'       # remember me 쿠키 CSRF 보호
    WTF_CSRF_ENABLED = True                # Flask-WTF CSRF 전역 활성화
    WTF_CSRF_TIME_LIMIT = 3600             # CSRF 토큰 유효 시간(초)

    # Google OAuth
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')

    # Admin 계정 (Railway 환경변수로 관리)
    ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@lovesta.app')
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'Admin1234!')


class DevelopmentConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_SAMESITE = 'Lax'


class ProductionConfig(Config):
    DEBUG = False
    # HTTPS 환경에서 쿠키 보안 설정 (Railway는 HTTPS 제공)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_SECURE = True          # remember me 쿠키 HTTPS 전용
    REMEMBER_COOKIE_HTTPONLY = True
    # 프로덕션에선 SECRET_KEY 반드시 환경변수에서 가져오기
    @property
    def SECRET_KEY(self):  # noqa: N802
        key = os.getenv('SECRET_KEY', '')
        if not key or key == 'dev-secret-key-change-in-production':
            import secrets
            return secrets.token_hex(32)
        return key


config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}
