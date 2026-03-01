"""
Security utilities: rate limiter, security headers, input sanitisation helpers.

방어 대상:
 - SQL Injection → SQLAlchemy ORM 파라미터 바인딩 (text() 포함)
 - XSS           → Jinja2 자동 이스케이프 + markupsafe.escape
 - CSRF          → Flask-WTF CSRFProtect (전역)
 - Session Hijacking → httponly / samesite cookie + 로그인 시 세션 재생성
 - Clickjacking  → X-Frame-Options DENY
 - Rate Limiting  → 인메모리 IP 기반 (로그인·회원가입·가챠)
 - Path Traversal → 파일명 uuid 전용 + secure_filename
 - Open Redirect  → next 파라미터 검증 (상대경로만)
"""
import re
import time
import threading
from functools import wraps
from collections import defaultdict
from flask import request, abort, g
from markupsafe import escape as _escape


# ──────────────────── Rate Limiter (in-memory) ────────────────────

class RateLimiter:
    """
    IP 기반 인메모리 레이트 리미터.
    window(초) 동안 max_requests 이상 요청 시 429 반환.
    """

    def __init__(self):
        self._hits: dict[str, list[float]] = defaultdict(list)
        self._lock = threading.Lock()

    def _cleanup(self, key: str, window: float):
        now = time.time()
        self._hits[key] = [t for t in self._hits[key] if now - t < window]

    def is_limited(self, key: str, max_requests: int, window: int) -> bool:
        with self._lock:
            self._cleanup(key, window)
            if len(self._hits[key]) >= max_requests:
                return True
            self._hits[key].append(time.time())
            return False


_limiter = RateLimiter()


def rate_limit(max_requests: int = 10, window: int = 60, scope: str = ''):
    """
    데코레이터: 특정 엔드포인트에 레이트 리밋 적용.
    scope 를 지정하면 엔드포인트 이름 대신 사용.
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            ip = request.remote_addr or '0.0.0.0'
            key = f'rl:{scope or request.endpoint}:{ip}'
            if _limiter.is_limited(key, max_requests, window):
                abort(429)
            return f(*args, **kwargs)
        return wrapper
    return decorator


# ──────────────────── Security Headers ────────────────────

def apply_security_headers(response):
    """
    after_request 핸들러: 모든 응답에 보안 헤더 추가.
    """
    # Clickjacking 방지
    response.headers['X-Frame-Options'] = 'DENY'
    # MIME sniffing 방지
    response.headers['X-Content-Type-Options'] = 'nosniff'
    # XSS 필터 (구형 브라우저 호환)
    response.headers['X-XSS-Protection'] = '1; mode=block'
    # Referrer 정보 제한
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    # 권한 정책
    response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
    # Content Security Policy (Tailwind CDN + Google OAuth + Cloudinary + AdSense)
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.tailwindcss.com "
        "https://accounts.google.com https://apis.google.com "
        "https://pagead2.googlesyndication.com https://adservice.google.com https://www.googletagservices.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: https://res.cloudinary.com https://*.googleusercontent.com "
        "https://pagead2.googlesyndication.com https://*.google.com blob:; "
        "connect-src 'self' https://pagead2.googlesyndication.com https://*.google.com; "
        "frame-src https://accounts.google.com https://googleads.g.doubleclick.net https://tpc.googlesyndication.com; "
        "object-src 'none'; "
        "base-uri 'self';"
    )
    # HTTPS 강제 (프로덕션)
    if not request.is_secure and request.headers.get('X-Forwarded-Proto') == 'https':
        pass  # 이미 HTTPS (리버스 프록시)
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    # 캐시 제어 (민감 페이지)
    if request.endpoint and 'admin' in (request.endpoint or ''):
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
    return response


# ──────────────────── Input Sanitisation ────────────────────

_DANGEROUS_CHARS = re.compile(r'[<>&\"\';\\]')


def sanitize_input(value: str, max_length: int = 500) -> str:
    """위험 문자를 제거하고 길이를 제한한 문자열 반환."""
    if not value:
        return ''
    value = value.strip()[:max_length]
    return _DANGEROUS_CHARS.sub('', value)


def safe_redirect_url(target: str, fallback: str = '/') -> str:
    """
    Open Redirect 방지: 상대 경로('/')만 허용.
    외부 URL이면 fallback 반환.
    """
    if not target:
        return fallback
    # '/path' 형식만 허용, '//' 또는 'http' 시작 차단
    if target.startswith('/') and not target.startswith('//'):
        return target
    return fallback
