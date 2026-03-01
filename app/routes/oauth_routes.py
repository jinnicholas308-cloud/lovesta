"""
Google OAuth2 routes.
Requires env vars: GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
Setup guide: https://console.cloud.google.com/

보안: 콜백 레이트 리밋, 세션 재생성, 입력 검증.
"""
from flask import Blueprint, redirect, url_for, flash, session, request, current_app
from flask_login import login_user, current_user
from authlib.integrations.flask_client import OAuth
from app.extensions import db
from app.models import User
from app.utils.security import rate_limit

oauth_bp = Blueprint('oauth', __name__, url_prefix='/auth')
oauth = OAuth()


def init_oauth(app):
    """Call this from create_app() to register Google provider."""
    oauth.init_app(app)
    oauth.register(
        name='google',
        client_id=app.config.get('GOOGLE_CLIENT_ID'),
        client_secret=app.config.get('GOOGLE_CLIENT_SECRET'),
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'},
    )


@oauth_bp.route('/google')
@rate_limit(max_requests=10, window=60, scope='oauth_google')
def google_login():
    if current_user.is_authenticated:
        return redirect(url_for('memories.feed'))
    redirect_uri = url_for('oauth.google_callback', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@oauth_bp.route('/google/callback')
@rate_limit(max_requests=10, window=60, scope='oauth_callback')
def google_callback():
    try:
        token = oauth.google.authorize_access_token()
        user_info = token.get('userinfo')
        if not user_info:
            raise ValueError('Google 사용자 정보를 가져올 수 없습니다.')
    except Exception as e:
        flash(f'Google 로그인 실패: {e}', 'error')
        return redirect(url_for('auth.login'))

    google_id = user_info['sub']
    email = user_info.get('email', '')[:200]
    name = user_info.get('name', email.split('@')[0])[:100]
    picture = user_info.get('picture', '')[:500]

    # Find by google_id first, then by email
    user = User.query.filter_by(google_id=google_id).first()
    if not user:
        user = User.query.filter_by(email=email).first()
        if user:
            user.google_id = google_id
            if picture:
                user.profile_image = picture
        else:
            username = _unique_username(name)
            user = User(
                username=username,
                email=email,
                google_id=google_id,
                profile_image=picture if picture else None,
            )
            db.session.add(user)

    db.session.commit()

    # 세션 재생성 후 로그인 (세션 고정 공격 방지)
    session.clear()
    login_user(user, remember=True)

    if not user.couple_id:
        return redirect(url_for('couple.setup'))
    return redirect(url_for('memories.feed'))


def _unique_username(base: str) -> str:
    """Generate a unique username based on a base string."""
    import re
    slug = re.sub(r'[^\w가-힣]', '_', base)[:40]
    username = slug
    counter = 1
    while User.query.filter_by(username=username).first():
        username = f'{slug}_{counter}'
        counter += 1
    return username
