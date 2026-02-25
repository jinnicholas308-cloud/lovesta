import secrets
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Couple, User

couple_bp = Blueprint('couple', __name__, url_prefix='/couple')


@couple_bp.route('/setup', methods=['GET', 'POST'])
@login_required
def setup():
    if current_user.couple_id:
        return redirect(url_for('memories.feed'))

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'create':
            invite_code = secrets.token_urlsafe(8)
            couple_name = request.form.get('couple_name', '').strip()
            anniversary_str = request.form.get('anniversary', '')

            couple = Couple(invite_code=invite_code)
            if couple_name:
                couple.couple_name = couple_name
            if anniversary_str:
                try:
                    couple.anniversary = datetime.strptime(anniversary_str, '%Y-%m-%d').date()
                except ValueError:
                    pass

            db.session.add(couple)
            db.session.flush()

            current_user.couple_id = couple.id
            db.session.commit()

            flash(f'커플 코드가 생성되었습니다: {invite_code}', 'success')
            return redirect(url_for('memories.feed'))

        elif action == 'join':
            invite_code = request.form.get('invite_code', '').strip()
            couple = Couple.query.filter_by(invite_code=invite_code).first()

            if not couple:
                flash('유효하지 않은 커플 코드입니다.', 'error')
                return render_template('couple/setup.html')

            if couple.members.count() >= 2:
                flash('이미 2명이 연결된 커플 코드입니다.', 'error')
                return render_template('couple/setup.html')

            current_user.couple_id = couple.id
            db.session.commit()

            flash('파트너와 연결되었습니다!', 'success')
            return redirect(url_for('memories.feed'))

    return render_template('couple/setup.html')


@couple_bp.route('/info')
@login_required
def info():
    if not current_user.couple_id:
        return redirect(url_for('couple.setup'))

    couple = Couple.query.get(current_user.couple_id)
    members = couple.members.all()

    days_together = None
    if couple.anniversary:
        days_together = (datetime.utcnow().date() - couple.anniversary).days

    return render_template('couple/info.html', couple=couple, members=members,
                           days_together=days_together)
