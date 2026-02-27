from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.models import User

profile_bp = Blueprint('profile', __name__, url_prefix='/profile')

MBTI_LIST = [
    'INTJ','INTP','ENTJ','ENTP',
    'INFJ','INFP','ENFJ','ENFP',
    'ISTJ','ISFJ','ESTJ','ESFJ',
    'ISTP','ISFP','ESTP','ESFP',
]


@profile_bp.route('/', methods=['GET', 'POST'])
@login_required
def me():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        bio = request.form.get('bio', '').strip()
        favorite_food = request.form.get('favorite_food', '').strip()
        mbti = request.form.get('mbti', '').strip().upper()

        birthday_str = request.form.get('birthday', '').strip()
        birthday = None
        if birthday_str:
            try:
                birthday = datetime.strptime(birthday_str, '%Y-%m-%d').date()
            except ValueError:
                flash('생일 형식이 올바르지 않습니다.', 'error')
                return redirect(url_for('profile.me'))

        # 유저명 중복 체크
        if username and username != current_user.username:
            if len(username) < 2 or len(username) > 20:
                flash('사용자명은 2~20자여야 합니다.', 'error')
                return redirect(url_for('profile.me'))
            if User.query.filter_by(username=username).first():
                flash('이미 사용 중인 사용자명입니다.', 'error')
                return redirect(url_for('profile.me'))
            current_user.username = username

        current_user.bio = bio or None
        current_user.favorite_food = favorite_food or None
        current_user.mbti = mbti if mbti in MBTI_LIST else None
        current_user.birthday = birthday

        # 펫 이름 (커플이 있으면)
        if current_user.couple:
            pet_name = request.form.get('pet_name', '').strip()
            if pet_name:
                current_user.couple.pet_name = pet_name[:20]
            else:
                current_user.couple.pet_name = None

        db.session.commit()
        flash('프로필이 저장됐어요 💕', 'success')
        return redirect(url_for('profile.me'))

    partner = None
    if current_user.couple:
        for m in current_user.couple.members:
            if m.id != current_user.id:
                partner = m
                break

    return render_template('profile/me.html',
                           partner=partner,
                           mbti_list=MBTI_LIST)
