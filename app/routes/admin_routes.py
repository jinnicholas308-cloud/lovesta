"""
Admin routes: dashboard, user management, memory management, activity logs.
Access restricted to users with is_admin=True.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models import User, Memory, Couple, Comment
from app.admin.decorators import admin_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    from datetime import datetime, timedelta
    stats = {
        'users': User.query.count(),
        'couples': Couple.query.count(),
        'memories': Memory.query.count(),
        'comments': Comment.query.count(),
    }
    week_ago = datetime.utcnow() - timedelta(days=7)
    stats['new_users_week'] = User.query.filter(User.created_at >= week_ago).count()
    stats['new_memories_week'] = Memory.query.filter(Memory.created_at >= week_ago).count()

    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_memories = Memory.query.order_by(Memory.created_at.desc()).limit(5).all()

    return render_template('admin/dashboard.html',
                           stats=stats,
                           recent_users=recent_users,
                           recent_memories=recent_memories)


@admin_bp.route('/users')
@login_required
@admin_required
def user_list():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('q', '').strip()

    query = User.query
    if search:
        query = query.filter(
            db.or_(
                User.username.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%'),
            )
        )

    users = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('admin/user_list.html', users=users, search=search)


@admin_bp.route('/users/<int:user_id>/toggle-admin', methods=['POST'])
@login_required
@admin_required
def toggle_admin(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('자기 자신의 권한은 변경할 수 없습니다.', 'error')
        return redirect(url_for('admin.user_list'))
    user.is_admin = not user.is_admin
    db.session.commit()
    status = '관리자로 지정' if user.is_admin else '일반 유저로 변경'
    flash(f'{user.username} 을(를) {status}했습니다.', 'success')
    return redirect(url_for('admin.user_list'))


@admin_bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
@login_required
@admin_required
def reset_user_password(user_id):
    """관리자가 특정 유저의 비밀번호를 임시 비밀번호로 초기화."""
    user = User.query.get_or_404(user_id)
    new_pw = request.form.get('new_password', '').strip()
    if not new_pw or len(new_pw) < 6:
        flash('비밀번호는 6자 이상이어야 합니다.', 'error')
        return redirect(url_for('admin.user_list'))
    if user.is_oauth_user:
        flash('Google OAuth 계정은 비밀번호를 재설정할 수 없습니다.', 'error')
        return redirect(url_for('admin.user_list'))
    user.set_password(new_pw)
    db.session.commit()
    flash(f'{user.username} 의 비밀번호를 재설정했습니다.', 'success')
    return redirect(url_for('admin.user_list'))


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """유저 계정 삭제 (본인 삭제 불가)."""
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('자기 자신은 삭제할 수 없습니다.', 'error')
        return redirect(url_for('admin.user_list'))
    username = user.username
    db.session.delete(user)
    db.session.commit()
    flash(f'{username} 계정이 삭제되었습니다.', 'info')
    return redirect(url_for('admin.user_list'))


@admin_bp.route('/memories')
@login_required
@admin_required
def memory_list():
    page = request.args.get('page', 1, type=int)
    memories = Memory.query.order_by(Memory.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('admin/memory_list.html', memories=memories)


@admin_bp.route('/memories/<int:memory_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_memory(memory_id):
    from app.utils.file_handler import delete_image
    memory = Memory.query.get_or_404(memory_id)
    delete_image(memory.image_path)
    db.session.delete(memory)
    db.session.commit()
    flash('추억이 삭제되었습니다.', 'info')
    return redirect(url_for('admin.memory_list'))
