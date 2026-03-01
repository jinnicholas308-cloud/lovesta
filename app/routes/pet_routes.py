"""
Pet gacha routes: single pull, 10-pull, collection, card image, interaction game.
Tickets are managed per-couple (not per-user).

보안: 가챠 레이트 리밋, XSS 방지, couple 권한 검증, SQL 파라미터 바인딩.
"""
import io
import re
from flask import Blueprint, render_template, redirect, url_for, flash, jsonify, request, send_file
from flask_login import login_required, current_user
from markupsafe import escape
from app.extensions import db
from app.models import Couple, Pet
from app.utils.pet_generator import do_gacha
from app.models.pet import RARITIES, RARITY_ORDER, BREEDS
from app.utils.security import rate_limit

pet_bp = Blueprint('pet', __name__, url_prefix='/pet')


def _get_couple_or_redirect():
    if not current_user.couple_id:
        return None, redirect(url_for('couple.setup'))
    couple = Couple.query.get(current_user.couple_id)
    if not couple:
        return None, redirect(url_for('couple.setup'))
    return couple, None


def _pet_to_dict(p):
    return {
        'id':             p.id,
        'breed':          p.breed,
        'emoji':          p.display_emoji,
        'breed_name':     p.breed_info['name'],
        'rarity':         p.rarity,
        'rarity_label':   p.rarity_info['label'],
        'rarity_color':   p.rarity_info['color'],
        'rarity_bg':      p.rarity_info['bg'],
        'rarity_text':    p.rarity_info['text'],
        'rarity_border':  p.rarity_info['border'],
        'rarity_glow':    p.rarity_info['glow'],
        'personality':    p.personality,
        'personality_label': p.personality_label,
        'is_active':      p.is_active,
    }


@pet_bp.route('/')
@login_required
def collection():
    """펫 컬렉션 보기."""
    couple, redir = _get_couple_or_redirect()
    if redir:
        return redir

    pets = Pet.query.filter_by(couple_id=couple.id)\
                    .order_by(Pet.created_at.desc()).all()

    tickets = getattr(couple, 'reroll_tickets', 0) or 0
    return render_template('pet/collection.html',
                           couple=couple, pets=pets, tickets=tickets,
                           rarities=RARITIES, rarity_order=RARITY_ORDER, breeds=BREEDS)


@pet_bp.route('/gacha', methods=['GET', 'POST'])
@login_required
@rate_limit(max_requests=20, window=60, scope='pet_gacha')
def gacha():
    """10연차 뽑기."""
    couple, redir = _get_couple_or_redirect()
    if redir:
        return redir

    tickets = getattr(couple, 'reroll_tickets', 0) or 0

    if request.method == 'POST':
        pull_type = request.form.get('pull_type', '10')
        pull_count = 1 if pull_type == '1' else 10

        success, message, pets = do_gacha(couple, pull_count=pull_count)
        if not success:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': message}), 400
            flash(message, 'error')
            return redirect(url_for('pet.collection'))

        pet_data = [_pet_to_dict(p) for p in pets]
        return jsonify({
            'success': True,
            'pets': pet_data,
            'tickets_remaining': couple.reroll_tickets,
            'pull_count': pull_count,
        })

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
    # XSS 방지: 특수문자 제거 (한글/영문/숫자/공백/이모지만 허용)
    new_name = re.sub(r'[<>&\"\';\\]', '', new_name)
    if new_name:
        pet.name = new_name
        db.session.commit()
        flash(f'펫 이름이 "{escape(new_name)}"(으)로 변경되었습니다!', 'success')

    return redirect(url_for('pet.collection'))


@pet_bp.route('/interaction', methods=['GET'])
@login_required
def interaction_game():
    """미니게임 페이지."""
    couple, redir = _get_couple_or_redirect()
    if redir:
        return redir
    tickets = getattr(couple, 'reroll_tickets', 0) or 0
    return render_template('pet/interaction.html', couple=couple, tickets=tickets)


@pet_bp.route('/interaction-bonus', methods=['POST'])
@login_required
@rate_limit(max_requests=5, window=60, scope='pet_interaction')
def interaction_bonus():
    """인터랙션 완수 보너스: 리롤권 2장 (중복 방지 — 1일 1회)."""
    from app.models.attendance import Attendance
    from datetime import datetime

    if not current_user.couple_id:
        return jsonify({'success': False, 'message': '커플 없음'}), 403

    couple = Couple.query.get(current_user.couple_id)
    today = datetime.utcnow().date()

    # 출석 체크를 한 날에만 인터랙션 보너스 가능
    if not Attendance.has_checked_today(current_user.id):
        return jsonify({'success': False, 'message': '먼저 오늘 출석 체크를 해주세요!'}), 400

    # 1일 1회 중복 방지 (세션 키 대신 DB 기반)
    from sqlalchemy import text
    already = db.session.execute(
        text("SELECT 1 FROM interaction_logs WHERE user_id = :uid AND date = :d"),
        {'uid': current_user.id, 'd': today}
    ).fetchone()

    if already:
        return jsonify({'success': False, 'message': '오늘 이미 인터랙션 보너스를 받았어요!'}), 400

    # 보너스 지급 (커플 통합 티켓)
    couple.reroll_tickets = (couple.reroll_tickets or 0) + 2
    db.session.execute(
        text("INSERT INTO interaction_logs (user_id, date) VALUES (:uid, :d)"),
        {'uid': current_user.id, 'd': today}
    )
    db.session.commit()

    return jsonify({
        'success': True,
        'message': '인터랙션 보너스! 리롤권 2장 획득!',
        'tickets': couple.reroll_tickets,
    })


@pet_bp.route('/<int:pet_id>/card.png')
@login_required
def pet_card_image(pet_id):
    """펫 카드 이미지 생성 (Pillow) — OG 공유 + 워터마크 다운로드용."""
    pet = Pet.query.get_or_404(pet_id)
    if not current_user.couple_id or pet.couple_id != current_user.couple_id:
        return jsonify({'error': '권한 없음'}), 403

    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return jsonify({'error': 'Pillow not installed'}), 500

    W, H = 400, 520
    rarity_info = pet.rarity_info
    color = rarity_info['color']

    # hex → RGB
    r_c = int(color[1:3], 16)
    g_c = int(color[3:5], 16)
    b_c = int(color[5:7], 16)

    img = Image.new('RGB', (W, H), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    # 상단 배경 그라데이션 영역
    for y in range(200):
        ratio = y / 200
        cr = int(255 * (1 - ratio * 0.15) + r_c * ratio * 0.15)
        cg = int(255 * (1 - ratio * 0.15) + g_c * ratio * 0.15)
        cb = int(255 * (1 - ratio * 0.15) + b_c * ratio * 0.15)
        draw.line([(0, y), (W, y)], fill=(min(cr, 255), min(cg, 255), min(cb, 255)))

    # 이모지 텍스트 (폰트 없으면 대체)
    try:
        font_lg = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 64)
        font_md = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
        font_sm = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
    except (IOError, OSError):
        font_lg = ImageFont.load_default()
        font_md = ImageFont.load_default()
        font_sm = ImageFont.load_default()

    # 이모지/이름은 ASCII 대체 (Pillow에서 이모지 렌더링 제한)
    breed_name = pet.breed_info['name']
    pet_name = pet.display_name

    # 중앙 원
    draw.ellipse([150, 60, 250, 160], fill=(255, 255, 255), outline=(r_c, g_c, b_c), width=3)
    draw.text((175, 85), pet.breed[:3].upper(), fill=(r_c, g_c, b_c), font=font_md)

    # 이름
    draw.text((W // 2 - len(pet_name) * 6, 220), pet_name, fill=(50, 50, 50), font=font_md, anchor=None)

    # 희귀도 배지
    label = rarity_info['label']
    draw.rounded_rectangle([W // 2 - 50, 260, W // 2 + 50, 290], radius=15, fill=(r_c, g_c, b_c))
    draw.text((W // 2 - 20, 265), label, fill=(255, 255, 255), font=font_sm)

    # 종 / 성격
    draw.text((W // 2 - 40, 310), f'{breed_name}', fill=(100, 100, 100), font=font_sm)
    if pet.personality:
        draw.text((W // 2 - 50, 340), f'{pet.personality} {pet.personality_label}', fill=(150, 100, 200), font=font_sm)

    # 하단 구분선
    draw.line([(40, 380), (W - 40, 380)], fill=(230, 230, 230), width=1)

    # 워터마크
    draw.text((W // 2 - 60, 400), 'Lovesta', fill=(200, 200, 200), font=font_md)
    draw.text((W // 2 - 25, 440), 'lovesta.app', fill=(210, 210, 210), font=font_sm)

    # 테두리
    draw.rectangle([0, 0, W - 1, H - 1], outline=(r_c, g_c, b_c), width=3)

    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return send_file(buf, mimetype='image/png', download_name=f'pet_{pet.id}.png')
