import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / '.env')

def _database_url():
    url = os.getenv('DATABASE_URL', '').strip()
    if not url:
        return f'sqlite:///{BASE_DIR / "careerhub.db"}'
    # Some managed PostgreSQL providers still expose the legacy postgres:// scheme.
    if url.startswith('postgres://'):
        url = 'postgresql+psycopg://' + url[len('postgres://'):]
    elif url.startswith('postgresql://') and '+psycopg' not in url:
        url = 'postgresql+psycopg://' + url[len('postgresql://'):]
    return url

class Config:
    ENV = os.getenv('FLASK_ENV', 'production')
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-change-me')
    SQLALCHEMY_DATABASE_URI = _database_url()
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_TIME_LIMIT = None
    DEV_SHOW_RESET_LINK = os.getenv('DEV_SHOW_RESET_LINK', '0') == '1'
    JOBS_PER_PAGE = int(os.getenv('JOBS_PER_PAGE', '20'))
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024
    UPLOAD_EXTENSIONS = {'pdf','doc','docx'}
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', '1') == '1'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
