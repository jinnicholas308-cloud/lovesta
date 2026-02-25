import os
from dotenv import load_dotenv

load_dotenv()

# 프로젝트 루트 절대경로 (config.py 기준 두 단계 위)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _fix_db_url(url: str) -> str:
    """Render/Heroku provide postgres:// but SQLAlchemy needs postgresql://"""
    if url and url.startswith('postgres://'):
        return url.replace('postgres://', 'postgresql://', 1)
    return url


def _resolve_upload_dir() -> str:
    """환경변수가 없으면 프로젝트 루트 기준 절대경로 반환"""
    env_val = os.getenv('UPLOAD_DIR')
    if env_val:
        return os.path.abspath(env_val)
    return os.path.join(BASE_DIR, 'storage', 'uploads')


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    SQLALCHEMY_DATABASE_URI = _fix_db_url(
        os.getenv('DATABASE_URL', 'sqlite:///lovesta.db')
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = _resolve_upload_dir()
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))

    # Google OAuth
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}
