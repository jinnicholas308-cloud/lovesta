"""
Admin routes: dashboard, user/memory/couple management, inquiry management,
              pet admin (force rarity, grant tickets, edit/delete), stats.
보안: admin_required 데코레이터, 입력 검증, XSS escape, 레이트 리밋.
"""
import re
from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from markupsafe import escape
from app.extensions import db
from app.models import User, Memory, Couple, Comment, Inquiry, Pet
from app.admin.decorators import admin_required
from app.utils.email import send_inquiry_reply, send_limit_increase_notification
from app.utils.pet_generator import admin_force_rarity, admin_grant_tickets
from app.models.pet import RARITIES, RARITY_ORDER, BREEDS, MBTI_LIST
from app.utils.security import rate_limit

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    stats = {
        'users': User.query.count(),
        'couples': Couple.query.count(),
        'memories': Memory.query.count(),
        'comments': Comment.query.count(),
        'inquiries_pending': Inquiry.query.filter_by(status='pending').count(),
        'pets_total': Pet.query.count(),
    }

    week_ago = datetime.utcnow() - timedelta(days=7)
    stats['new_users_week'] = User.query.filter(User.created_at >= week_ago).count()
    stats['new_memories_week'] = Memory.query.filter(Memory.created_at >= week_ago).count()

    pet_stats = {}
    for rarity in RARITY_ORDER:
        pet_stats[rarity] = {
            'count': Pet.query.filter_by(rarity=rarity).count(),
            'label': RARITIES[rarity]['label'],
            'color': RARITIES[rarity]['color'],
        }
    stats['pet_stats'] = pet_stats

    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_memories = Memory.query.order_by(Memory.created_at.desc()).limit(5).all()

    return render_template('admin/dashboard.html',
                           stats=stats,
                           recent_users=recent_users,
                           recent_memories=recent_memories)


# ── 유저 관리 ──

@admin_bp.route('/users')
@login_required
@admin_required
def user_list():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('q', '').strip()[:100]

    query = User.query
    if search:
        safe_search = f'%{search}%'
        query = query.filter(
            db.or_(
                User.username.ilike(safe_search),
                User.email.ilike(safe_search),
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
    flash(f'{escape(user.username)} 을(를) {status}했습니다.', 'success')
    return redirect(url_for('admin.user_list'))


@admin_bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
@login_required
@admin_required
def reset_user_password(user_id):
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
    flash(f'{escape(user.username)} 의 비밀번호를 재설정했습니다.', 'success')
    return redirect(url_for('admin.user_list'))


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('자기 자신은 삭제할 수 없습니다.', 'error')
        return redirect(url_for('admin.user_list'))
    username = user.username
    db.session.delete(user)
    db.session.commit()
    flash(f'{escape(username)} 계정이 삭제되었습니다.', 'info')
    return redirect(url_for('admin.user_list'))


# ── 추억 관리 ──

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
    from app.utils.file_handler import delete_image, delete_video
    memory = Memory.query.get_or_404(memory_id)
    mt = getattr(memory, 'media_type', 'image') or 'image'
    if mt == 'video':
        delete_video(memory.image_path)
    else:
        delete_image(memory.image_path)
    db.session.delete(memory)
    db.session.commit()
    flash('추억이 삭제되었습니다.', 'info')
    return redirect(url_for('admin.memory_list'))


# ── 커플 관리 ──

@admin_bp.route('/couples')
@login_required
@admin_required
def couple_list():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('q', '').strip()[:50]

    query = Couple.query
    if search:
        query = query.filter(Couple.invite_code.ilike(f'%{search}%'))

    couples = query.order_by(Couple.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('admin/couples.html',
                           couples=couples, search=search,
                           rarities=RARITIES, rarity_order=RARITY_ORDER, breeds=BREEDS)


@admin_bp.route('/couples/<int:couple_id>/set-limit', methods=['POST'])
@login_required
@admin_required
def set_couple_limit(couple_id):
    couple = Couple.query.get_or_404(couple_id)
    new_limit = request.form.get('max_members', 2, type=int)
    if new_limit < 2 or new_limit > 10:
        flash('2~10 사이로 설정해주세요.', 'error')
        return redirect(url_for('admin.couple_list'))

    old_limit = couple.max_members or 2
    couple.max_members = new_limit
    db.session.commit()

    if new_limit > old_limit:
        send_limit_increase_notification(couple, new_limit)

    flash(f'커플 {escape(couple.invite_code)}의 인원 제한이 {new_limit}명으로 변경되었습니다.', 'success')
    return redirect(url_for('admin.couple_list'))


@admin_bp.route('/couples/<int:couple_id>/force-pet', methods=['POST'])
@login_required
@admin_required
def force_pet(couple_id):
    couple = Couple.query.get_or_404(couple_id)
    rarity = request.form.get('rarity', 'rare')
    breed = request.form.get('breed', '')

    if rarity not in RARITY_ORDER:
        flash('유효하지 않은 희귀도입니다.', 'error')
        return redirect(url_for('admin.couple_list'))
    if breed and breed not in BREEDS:
        breed = None

    pet = admin_force_rarity(couple, rarity, breed if breed else None)
    if pet:
        flash(f'커플 {escape(couple.invite_code)}에 {RARITIES[rarity]["label"]} {pet.breed_info["name"]} 지급!', 'success')
    else:
        flash('유효하지 않은 희귀도입니다.', 'error')

    return redirect(url_for('admin.couple_list'))


@admin_bp.route('/couples/<int:couple_id>/grant-tickets', methods=['POST'])
@login_required
@admin_required
def grant_tickets(couple_id):
    """어드민: 커플에 리롤권 수동 지급."""
    couple = Couple.query.get_or_404(couple_id)
    amount = request.form.get('amount', 0, type=int)
    if amount < 1 or amount > 100:
        flash('1~100 사이로 입력해주세요.', 'error')
        return redirect(url_for('admin.couple_list'))
    total = admin_grant_tickets(couple, amount)
    flash(f'커플 {escape(couple.invite_code)}에 리롤권 {amount}장 지급 (현재: {total}장)', 'success')
    return redirect(url_for('admin.couple_list'))


# ── 펫 관리 (수정/삭제) ──

@admin_bp.route('/pets')
@login_required
@admin_required
def pet_list():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('q', '').strip()[:50]

    query = Pet.query
    if search:
        safe = f'%{search}%'
        query = query.filter(
            db.or_(
                Pet.name.ilike(safe),
                Pet.breed.ilike(safe),
                Pet.rarity.ilike(safe),
            )
        )

    pets = query.order_by(Pet.created_at.desc()).paginate(
        page=page, per_page=30, error_out=False
    )
    return render_template('admin/pets.html',
                           pets=pets, search=search,
                           rarities=RARITIES, rarity_order=RARITY_ORDER,
                           breeds=BREEDS, mbti_list=MBTI_LIST)


@admin_bp.route('/pets/<int:pet_id>/edit', methods=['POST'])
@login_required
@admin_required
def edit_pet(pet_id):
    pet = Pet.query.get_or_404(pet_id)

    new_name = request.form.get('name', '').strip()[:50]
    new_name = re.sub(r'[<>&\"\';\\]', '', new_name)
    new_rarity = request.form.get('rarity', pet.rarity)
    new_breed = request.form.get('breed', pet.breed)
    new_personality = request.form.get('personality', pet.personality)

    if new_name:
        pet.name = new_name
    if new_rarity in RARITY_ORDER:
        pet.rarity = new_rarity
    if new_breed in BREEDS:
        pet.breed = new_breed
    if new_personality in MBTI_LIST:
        pet.personality = new_personality

    db.session.commit()
    flash(f'펫 #{pet.id} 수정 완료', 'success')
    return redirect(url_for('admin.pet_list'))


@admin_bp.route('/pets/<int:pet_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_pet(pet_id):
    pet = Pet.query.get_or_404(pet_id)
    pet_info = f'{pet.breed_info["name"]} ({pet.rarity_info["label"]})'
    db.session.delete(pet)
    db.session.commit()
    flash(f'펫 #{pet_id} {pet_info} 삭제 완료', 'info')
    return redirect(url_for('admin.pet_list'))


# ── 문의 관리 ──

@admin_bp.route('/inquiries')
@login_required
@admin_required
def inquiry_list():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '').strip()[:20]

    query = Inquiry.query
    if status_filter in ('pending', 'answered', 'closed'):
        query = query.filter_by(status=status_filter)

    inquiries = query.order_by(Inquiry.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('admin/inquiries.html',
                           inquiries=inquiries, status_filter=status_filter)


@admin_bp.route('/inquiries/<int:inquiry_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def inquiry_detail(inquiry_id):
    inquiry = Inquiry.query.get_or_404(inquiry_id)

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'reply':
            reply_text = request.form.get('reply', '').strip()[:2000]
            if reply_text:
                inquiry.admin_reply = reply_text
                inquiry.replied_at = datetime.utcnow()
                inquiry.status = 'answered'
                # 유저에게 답변 알림
                from app.models.notification import Notification
                Notification.send(
                    inquiry.user_id, 'inquiry_reply',
                    '문의에 답변이 도착했습니다.',
                    body=reply_text[:80],
                    url=f'/inquiry/{inquiry.id}'
                )
                db.session.commit()
                send_inquiry_reply(inquiry, reply_text)
                flash('답변이 전송되었습니다!', 'success')

        elif action == 'close':
            inquiry.status = 'closed'
            db.session.commit()
            flash('문의가 종료 처리되었습니다.', 'info')

        elif action == 'increase_limit':
            if inquiry.couple_id:
                couple = Couple.query.get(inquiry.couple_id)
                if couple:
                    new_limit = request.form.get('new_limit', 2, type=int)
                    couple.max_members = max(2, min(10, new_limit))
                    db.session.commit()
                    send_limit_increase_notification(couple, couple.max_members)
                    flash(f'커플 인원이 {couple.max_members}명으로 증설되었습니다!', 'success')

        return redirect(url_for('admin.inquiry_detail', inquiry_id=inquiry_id))

    return render_template('admin/inquiry_detail.html', inquiry=inquiry)
