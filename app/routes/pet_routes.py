"""
Pet gacha routes: 10-pull, collection, set active, interaction bonus.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, jsonify, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Couple, Pet
from app.utils.pet_generator import do_gacha
from app.models.pet import RARITIES, RARITY_ORDER, BREEDS

pet_bp = Blueprint('pet', __name__, url_prefix='/pet')


@pet_bp.route('/')
@login_required
def collection():
    """펫 컬렉션 보기."""
    if not current_user.couple_id:
        return redirect(url_for('couple.setup'))

    couple = Couple.query.get(current_user.couple_id)
    pets = Pet.query.filter_by(couple_id=couple.id)\
                    .order_by(Pet.created_at.desc()).all()

    tickets = getattr(current_user, 'reroll_tickets', 0) or 0
    return render_template('pet/collection.html',
                           couple=couple, pets=pets, tickets=tickets,
                           rarities=RARITIES, rarity_order=RARITY_ORDER, breeds=BREEDS)


@pet_bp.route('/gacha', methods=['GET', 'POST'])
@login_required
def gacha():
    """10연차 뽑기."""
    if not current_user.couple_id:
        return redirect(url_for('couple.setup'))

    couple = Couple.query.get(current_user.couple_id)
    tickets = getattr(current_user, 'reroll_tickets', 0) or 0

    if request.method == 'POST':
        success, message, pets = do_gacha(couple, current_user)
        if not success:
            flash(message, 'error')
            return redirect(url_for('pet.collection'))

        # 뽑기 결과를 세션 없이 JSON으로 반환 (JS가 애니메이션 처리)
        pet_data = []
        for p in pets:
            pet_data.append({
                'id':          p.id,
                'breed':       p.breed,
                'emoji':       p.display_emoji,
                'breed_name':  p.breed_info['name'],
                'rarity':      p.rarity,
                'rarity_label': p.rarity_info['label'],
                'rarity_color': p.rarity_info['color'],
                'rarity_bg':   p.rarity_info['bg'],
                'rarity_text': p.rarity_info['text'],
                'rarity_border': p.rarity_info['border'],
                'rarity_glow': p.rarity_info['glow'],
                'personality': p.personality,
                'personality_label': p.personality_label,
                'is_active':   p.is_active,
            })
        return jsonify({'success': True, 'pets': pet_data,
                        'tickets_remaining': current_user.reroll_tickets})

    return render_template('pet/gacha.html',
                           couple=couple, tickets=tickets,
                           rarities=RARITIES, rarity_order=RARITY_ORDER)


@pet_bp.route('/<int:pet_id>/activate', methods=['POST'])
@login_required
def activate(pet_id):
    """특정 펫을 활성 펫으로 설정."""
    if not current_user.couple_id:
        return jsonify({'error': '커플 없음'}), 403

    pet = Pet.query.get_or_404(pet_id)
    if pet.couple_id != current_user.couple_id:
        return jsonify({'error': '권한 없음'}), 403

    Pet.query.filter_by(couple_id=current_user.couple_id, is_active=True)\
             .update({'is_active': False})
    pet.is_active = True
    db.session.commit()

    return jsonify({'success': True, 'pet_id': pet.id})


@pet_bp.route('/<int:pet_id>/name', methods=['POST'])
@login_required
def rename(pet_id):
    """펫 이름 변경."""
    if not current_user.couple_id:
        return jsonify({'error': '커플 없음'}), 403

    pet = Pet.query.get_or_404(pet_id)
    if pet.couple_id != current_user.couple_id:
        return jsonify({'error': '권한 없음'}), 403

    new_name = request.form.get('name', '').strip()[:50]
    if new_name:
        pet.name = new_name
        db.session.commit()
        flash(f'펫 이름이 "{new_name}"(으)로 변경되었습니다!', 'success')

    return redirect(url_for('pet.collection'))


@pet_bp.route('/interaction-bonus', methods=['POST'])
@login_required
def interaction_bonus():
    """인터랙션 완수 보너스: 리롤권 2장 (중복 방지)."""
    # 간단한 쿨타임 체크: 하루 1회
    from app.models.attendance import Attendance
    from datetime import datetime
    today = datetime.utcnow().date()

    cache_key = f'interaction_{current_user.id}_{today}'
    # 세션 대신 DB 기반 중복 방지 (서버 사이드)
    from sqlalchemy import text
    result = db.session.execute(
        text("SELECT 1 FROM attendances WHERE user_id = :uid AND date = :d"),
        {'uid': current_user.id, 'd': today}
    ).fetchone()

    # 출석 체크를 한 날에만 인터랙션 보너스 가능 (이중 체크)
    if not result:
        return jsonify({'success': False, 'message': '먼저 오늘 출석 체크를 해주세요!'}), 400

    current_user.reroll_tickets = (current_user.reroll_tickets or 0) + 2
    db.session.commit()

    return jsonify({
        'success': True,
        'message': '인터랙션 보너스! 리롤권 2장 획득!',
        'tickets': current_user.reroll_tickets,
    })
