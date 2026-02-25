"""
Comment routes: add and delete comments on memories.
"""
from flask import Blueprint, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Memory, Comment

comment_bp = Blueprint('comments', __name__)


@comment_bp.route('/memory/<int:memory_id>/comment', methods=['POST'])
@login_required
def add_comment(memory_id):
    memory = Memory.query.get_or_404(memory_id)
    if memory.couple_id != current_user.couple_id:
        return jsonify({'error': '권한 없음'}), 403

    content = request.form.get('content', '').strip()
    if not content:
        flash('댓글 내용을 입력해주세요.', 'error')
        return redirect(url_for('memories.detail', memory_id=memory_id))

    comment = Comment(content=content, user_id=current_user.id, memory_id=memory_id)
    db.session.add(comment)
    db.session.commit()
    return redirect(url_for('memories.detail', memory_id=memory_id))


@comment_bp.route('/memory/<int:memory_id>/comment/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(memory_id, comment_id):
    comment = Comment.query.get_or_404(comment_id)
    if comment.user_id != current_user.id:
        flash('삭제 권한이 없습니다.', 'error')
        return redirect(url_for('memories.detail', memory_id=memory_id))

    db.session.delete(comment)
    db.session.commit()
    return redirect(url_for('memories.detail', memory_id=memory_id))
