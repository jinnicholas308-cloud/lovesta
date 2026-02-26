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


_DB_URL = _fix_db_url(
    # os.getenv 기본값은 변수가 "없을 때"만 적용 → 빈 문자열('')은 통과됨
    # or 연산자로 None/'' 둘 다 fallback 처리
    os.getenv('DATABASE_URL') or f'sqlite:///{os.path.join(BASE_DIR, "lovesta.db")}'
)


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = _DB_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = _resolve_upload_dir()
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))

    # PostgreSQL 연결 안정성 (Railway 재시작 후 끊긴 커넥션 자동 복구)
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }

    # 세션 설정 (로그인 유지)
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)
    REMEMBER_COOKIE_DURATION = timedelta(days=30)

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


config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}
