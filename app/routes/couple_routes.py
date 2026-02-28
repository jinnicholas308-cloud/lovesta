"""
Couple management routes: create/join couple, view couple info.
"""
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
            couple_name = request.form.get('couple_name', '').strip()
            anniversary_str = request.form.get('anniversary', '')

            couple = Couple(invite_code=secrets.token_urlsafe(8))
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

            flash(f'커플 코드: {couple.invite_code}', 'success')
            return redirect(url_for('memories.feed'))

        elif action == 'join':
            invite_code = request.form.get('invite_code', '').strip()
            couple = Couple.query.filter_by(invite_code=invite_code).first()

            if not couple:
                flash('유효하지 않은 커플 코드입니다.', 'error')
                return render_template('couple/setup.html')
            if couple.members.count() >= 2:
                flash('이미 2명이 연결된 코드입니다.', 'error')
                return render_template('couple/setup.html')

            current_user.couple_id = couple.id
            db.session.commit()
            flash('파트너와 연결되었습니다!', 'success')
            return redirect(url_for('memories.feed'))

    return render_template('couple/setup.html')


@couple_bp.route('/info', methods=['GET', 'POST'])
@login_required
def info():
    if not current_user.couple_id:
        return redirect(url_for('couple.setup'))

    couple = Couple.query.get(current_user.couple_id)

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'update_anniversary':
            anniversary_str = request.form.get('anniversary', '').strip()
            couple_name_str = request.form.get('couple_name', '').strip()

            if anniversary_str:
                try:
                    couple.anniversary = datetime.strptime(anniversary_str, '%Y-%m-%d').date()
                except ValueError:
                    flash('날짜 형식이 올바르지 않습니다.', 'error')
                    return redirect(url_for('couple.info'))
            else:
                couple.anniversary = None

            if couple_name_str:
                couple.couple_name = couple_name_str

            db.session.commit()
            flash('커플 정보가 업데이트되었습니다! 💕', 'success')
            return redirect(url_for('couple.info'))

    members = couple.members.all()
    return render_template('couple/info.html', couple=couple, members=members,
                           days_together=couple.days_together)
