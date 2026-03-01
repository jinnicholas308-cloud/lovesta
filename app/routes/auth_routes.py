"""
Authentication routes: register, login, logout, forgot account (email/password).
Google OAuth is handled in oauth_routes.py.

보안 적용:
 - 로그인/회원가입 레이트 리밋 (10회/분)
 - 비밀번호 찾기 레이트 리밋 (5회/분)
 - 로그인 성공 시 세션 재생성 (세션 고정 공격 방지)
 - next 파라미터 Open Redirect 검증
 - 입력 길이 제한 + XSS 방지
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from markupsafe import escape
from app.extensions import db, csrf
from app.models import User
from app.utils.validators import validate_username, validate_password_strength, is_valid_email
from app.utils.security import rate_limit, safe_redirect_url

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/register', methods=['GET', 'POST'])
@rate_limit(max_requests=10, window=60, scope='auth_register')
def register():
    if current_user.is_authenticated:
        return redirect(url_for('memories.feed'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()[:50]
        email = request.form.get('email', '').strip()[:200]
        password = request.form.get('password', '')[:128]
        confirm_password = request.form.get('confirm_password', '')[:128]

        errors = (
            validate_username(username)
            + ([] if is_valid_email(email) else ['올바른 이메일 형식이 아닙니다.'])
            + validate_password_strength(password)
        )
        if password != confirm_password:
            errors.append('비밀번호가 일치하지 않습니다.')

        if errors:
            for e in errors:
                flash(e, 'error')
            return render_template('auth/register.html')

        if User.query.filter_by(username=username).first():
            flash('이미 사용 중인 사용자명입니다.', 'error')
            return render_template('auth/register.html')
        if User.query.filter_by(email=email).first():
            flash('이미 사용 중인 이메일입니다.', 'error')
            return render_template('auth/register.html')

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        # 세션 재생성 후 로그인 (세션 고정 공격 방지)
        session.clear()
        login_user(user, remember=True)
        flash(f'환영합니다, {escape(username)}님! 💕', 'success')
        return redirect(url_for('couple.setup'))

    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
@rate_limit(max_requests=10, window=60, scope='auth_login')
def login():
    if current_user.is_authenticated:
        return redirect(url_for('memories.feed'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()[:200]
        password = request.form.get('password', '')[:128]
        remember = request.form.get('remember') == 'on'

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            flash('이메일 또는 비밀번호가 올바르지 않습니다.', 'error')
            return render_template('auth/login.html')

        # 세션 재생성 → 로그인 (세션 고정 공격 방지)
        session.clear()
        login_user(user, remember=remember)

        # Open Redirect 방지: 상대경로만 허용
        next_page = request.args.get('next', '')
        next_page = safe_redirect_url(next_page, url_for('memories.feed'))
        return redirect(next_page)

    return render_template('auth/login.html')


@auth_bp.route('/logout', methods=['GET', 'POST'])
@csrf.exempt
def logout():
    """로그아웃: CSRF 면제 + remember me 쿠키까지 확실히 제거."""
    if current_user.is_authenticated:
        logout_user()
        # 주의: session.clear()를 logout_user() 뒤에 호출하면
        #   Flask-Login의 _remember="clear" 플래그가 지워져서
        #   remember me 쿠키가 삭제되지 않는 버그 발생!
    session.clear()
    flash('로그아웃 되었습니다.', 'info')
    resp = redirect(url_for('auth.login'))
    # remember me 쿠키 수동 삭제 (Flask-Login 플래그가 날아간 경우 대비)
    resp.delete_cookie('remember_token', path='/')
    return resp


# ─── 아이디 / 비밀번호 찾기 ────────────────────────────────────────────────────

@auth_bp.route('/forgot', methods=['GET', 'POST'])
@rate_limit(max_requests=5, window=60, scope='auth_forgot')
def forgot():
    """이메일로 계정 조회 (아이디 확인 + 비밀번호 재설정 옵션)."""
    if current_user.is_authenticated:
        return redirect(url_for('memories.feed'))

    found_user = None
    step = request.args.get('step', 'lookup')  # 'lookup' | 'reset'

    if request.method == 'POST':
        action = request.form.get('action', 'lookup')

        if action == 'lookup':
            email = request.form.get('email', '').strip().lower()[:200]
            if not email:
                flash('이메일을 입력해주세요.', 'error')
            elif not is_valid_email(email):
                flash('올바른 이메일 형식이 아닙니다.', 'error')
            else:
                user = User.query.filter(
                    db.func.lower(User.email) == email
                ).first()
                if user:
                    session['forgot_email'] = user.email
                    found_user = user
                    step = 'found'
                else:
                    flash('해당 이메일로 가입된 계정이 없습니다.', 'error')

        elif action == 'reset':
            email = session.get('forgot_email')
            new_password = request.form.get('new_password', '')[:128]
            confirm_password = request.form.get('confirm_password', '')[:128]

            if not email:
                flash('세션이 만료되었습니다. 다시 시도해주세요.', 'error')
                return redirect(url_for('auth.forgot'))

            errors = validate_password_strength(new_password)
            if new_password != confirm_password:
                errors.append('비밀번호가 일치하지 않습니다.')

            if errors:
                for e in errors:
                    flash(e, 'error')
                user = User.query.filter_by(email=email).first()
                found_user = user
                step = 'reset'
            else:
                user = User.query.filter_by(email=email).first()
                if user and not user.is_oauth_user:
                    user.set_password(new_password)
                    db.session.commit()
                    session.pop('forgot_email', None)
                    flash('비밀번호가 재설정되었습니다. 로그인해주세요.', 'success')
                    return redirect(url_for('auth.login'))
                elif user and user.is_oauth_user:
                    flash('Google 계정으로 가입된 사용자는 비밀번호를 재설정할 수 없습니다.', 'error')
                    return redirect(url_for('auth.forgot'))
                else:
                    flash('계정을 찾을 수 없습니다.', 'error')
                    return redirect(url_for('auth.forgot'))

    if step == 'reset' and session.get('forgot_email'):
        email = session.get('forgot_email')
        found_user = User.query.filter_by(email=email).first()

    return render_template('auth/forgot.html', found_user=found_user, step=step)
