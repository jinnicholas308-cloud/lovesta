"""
Admin routes: dashboard, user management, memory management.
Access restricted to users with is_admin=True.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from app.extensions import db
from app.models import User, Memory, Couple
from app.admin.decorators import admin_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    stats = {
        'users': User.query.count(),
        'couples': Couple.query.count(),
        'memories': Memory.query.count(),
    }
    return render_template('admin/dashboard.html', stats=stats)


@admin_bp.route('/users')
@login_required
@admin_required
def user_list():
    page = request.args.get('page', 1, type=int)
    users = User.query.order_by(User.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('admin/user_list.html', users=users)


@admin_bp.route('/users/<int:user_id>/toggle-admin', methods=['POST'])
@login_required
@admin_required
def toggle_admin(user_id):
    user = User.query.get_or_404(user_id)
    user.is_admin = not user.is_admin
    db.session.commit()
    status = '관리자로 지정' if user.is_admin else '일반 유저로 변경'
    flash(f'{user.username} 을(를) {status}했습니다.', 'success')
    return redirect(url_for('admin.user_list'))


@admin_bp.route('/memories')
@login_required
@admin_required
def memory_list():
    page = request.args.get('page', 1, type=int)
    memories = Memory.query.order_by(Memory.created_at.desc()).paginate(page=page, per_page=20)
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
