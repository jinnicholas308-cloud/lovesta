"""
Memory routes: feed, upload, detail, delete, like toggle.
Comment routes are separated in comment_routes.py.
"""
from datetime import datetime
from flask import (Blueprint, render_template, redirect, url_for, flash,
                   request, jsonify, send_from_directory, current_app)
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Memory, Like, Couple
from app.utils.file_handler import save_image, delete_image
from app.utils.validators import is_allowed_image

memories_bp = Blueprint('memories', __name__)


@memories_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('memories.feed'))
    return redirect(url_for('auth.login'))


@memories_bp.route('/feed')
@login_required
def feed():
    if not current_user.couple_id:
        return redirect(url_for('couple.setup'))

    page = request.args.get('page', 1, type=int)
    memories = (Memory.query
                .filter_by(couple_id=current_user.couple_id)
                .order_by(Memory.created_at.desc())
                .paginate(page=page, per_page=9, error_out=False))

    couple = Couple.query.get(current_user.couple_id)
    return render_template('memories/feed.html', memories=memories, couple=couple)


@memories_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if not current_user.couple_id:
        return redirect(url_for('couple.setup'))

    if request.method == 'POST':
        caption = request.form.get('caption', '').strip()
        location = request.form.get('location', '').strip()
        memory_date_str = request.form.get('memory_date', '')
        file = request.files.get('image')

        if not caption:
            flash('캡션을 입력해주세요.', 'error')
            return render_template('memories/upload.html')

        image_filename = None
        if file and file.filename:
            if not is_allowed_image(file.filename):
                flash('PNG, JPG, GIF, WEBP 파일만 업로드 가능합니다.', 'error')
                return render_template('memories/upload.html')
            image_filename = save_image(file)

        memory_date = None
        if memory_date_str:
            try:
                memory_date = datetime.strptime(memory_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass

        memory = Memory(
            caption=caption,
            image_path=image_filename,
            location=location or None,
            memory_date=memory_date,
            user_id=current_user.id,
            couple_id=current_user.couple_id,
        )
        db.session.add(memory)
        db.session.commit()

        flash('추억이 업로드되었습니다!', 'success')
        return redirect(url_for('memories.detail', memory_id=memory.id))

    return render_template('memories/upload.html')


@memories_bp.route('/memory/<int:memory_id>')
@login_required
def detail(memory_id):
    from app.models import Comment
    memory = Memory.query.get_or_404(memory_id)
    if memory.couple_id != current_user.couple_id:
        flash('접근 권한이 없습니다.', 'error')
        return redirect(url_for('memories.feed'))

    comments = memory.comments.order_by(Comment.created_at.asc()).all()
    return render_template('memories/detail.html', memory=memory, comments=comments)


@memories_bp.route('/memory/<int:memory_id>/delete', methods=['POST'])
@login_required
def delete(memory_id):
    memory = Memory.query.get_or_404(memory_id)
    if memory.user_id != current_user.id:
        flash('삭제 권한이 없습니다.', 'error')
        return redirect(url_for('memories.feed'))

    delete_image(memory.image_path)
    db.session.delete(memory)
    db.session.commit()
    flash('추억이 삭제되었습니다.', 'info')
    return redirect(url_for('memories.feed'))


@memories_bp.route('/memory/<int:memory_id>/like', methods=['POST'])
@login_required
def toggle_like(memory_id):
    memory = Memory.query.get_or_404(memory_id)
    if memory.couple_id != current_user.couple_id:
        return jsonify({'error': '권한 없음'}), 403

    existing = Like.query.filter_by(user_id=current_user.id, memory_id=memory_id).first()
    if existing:
        db.session.delete(existing)
        liked = False
    else:
        db.session.add(Like(user_id=current_user.id, memory_id=memory_id))
        liked = True

    db.session.commit()
    return jsonify({'liked': liked, 'count': memory.like_count()})


@memories_bp.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)
