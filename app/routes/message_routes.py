"""
Couple Messages: 커플 간 메모/위치/생각 공유 (Instagram DM 스타일)
"""
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models.couple_message import CoupleMessage
from app.utils.file_handler import save_image, allowed_file

message_bp = Blueprint('messages', __name__, url_prefix='/messages')


@message_bp.route('/')
@login_required
def chat():
    """커플 메시지 메인 (채팅 스타일 뷰)"""
    if not current_user.couple_id:
        flash('먼저 커플을 연결해주세요!', 'warning')
        return redirect(url_for('couple.setup'))

    page = request.args.get('page', 1, type=int)
    per_page = 30

    messages = CoupleMessage.query.filter_by(couple_id=current_user.couple_id) \
        .order_by(CoupleMessage.created_at.desc()) \
        .paginate(page=page, per_page=per_page, error_out=False)

    # 파트너 정보
    partner = None
    for m in current_user.couple.members:
        if m.id != current_user.id:
            partner = m
            break

    return render_template('couple/messages.html',
                           messages=messages,
                           partner=partner)


@message_bp.route('/send', methods=['POST'])
@login_required
def send():
    """메시지 전송"""
    if not current_user.couple_id:
        return jsonify({'success': False, 'message': '커플 연결이 필요합니다.'}), 400

    msg_type = request.form.get('msg_type', 'memo').strip()
    content = request.form.get('content', '').strip()
    location_name = request.form.get('location_name', '').strip()
    mood = request.form.get('mood', '').strip()

    if not content and msg_type != 'photo':
        flash('내용을 입력해주세요!', 'error')
        return redirect(url_for('messages.chat'))

    message = CoupleMessage(
        couple_id=current_user.couple_id,
        user_id=current_user.id,
        msg_type=msg_type if msg_type in ('memo', 'location', 'thought', 'photo') else 'memo',
        content=content or '',
        mood=mood[:10] if mood else None,
    )

    # 위치 정보
    if location_name:
        message.location_name = location_name[:200]

    lat = request.form.get('latitude')
    lng = request.form.get('longitude')
    if lat and lng:
        try:
            message.latitude = float(lat)
            message.longitude = float(lng)
        except (ValueError, TypeError):
            pass

    # 사진 첨부
    photo = request.files.get('photo')
    if photo and photo.filename and allowed_file(photo.filename):
        try:
            image_path = save_image(photo)
            message.image_path = image_path
            if not content:
                message.content = '사진을 공유했어요 📷'
        except Exception:
            flash('사진 업로드에 실패했어요.', 'error')

    db.session.add(message)
    db.session.commit()

    # AJAX 요청이면 JSON 응답
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'message': {
                'id': message.id,
                'msg_type': message.msg_type,
                'content': message.content,
                'mood': message.mood,
                'location_name': message.location_name,
                'image_path': message.image_path,
                'type_icon': message.type_icon,
                'author': current_user.username,
                'is_mine': True,
                'created_at': message.created_at.strftime('%H:%M'),
            }
        })

    return redirect(url_for('messages.chat'))


@message_bp.route('/<int:msg_id>/delete', methods=['POST'])
@login_required
def delete(msg_id):
    """메시지 삭제 (본인 것만)"""
    msg = CoupleMessage.query.get_or_404(msg_id)

    if msg.user_id != current_user.id:
        flash('본인 메시지만 삭제할 수 있어요.', 'error')
        return redirect(url_for('messages.chat'))

    db.session.delete(msg)
    db.session.commit()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True})

    flash('메시지가 삭제되었어요.', 'success')
    return redirect(url_for('messages.chat'))
