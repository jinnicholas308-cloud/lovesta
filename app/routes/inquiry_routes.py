"""
Inquiry routes: user submits Q&A, views own inquiries.
보안: 입력 길이 제한, 카테고리 화이트리스트, 레이트 리밋.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Inquiry
from app.models.inquiry import INQUIRY_CATEGORIES
from app.utils.email import send_inquiry_notification
from app.utils.security import rate_limit

inquiry_bp = Blueprint('inquiry', __name__, url_prefix='/inquiry')


@inquiry_bp.route('/')
@login_required
def list_inquiries():
    """내 문의 목록."""
    inquiries = Inquiry.query.filter_by(user_id=current_user.id)\
                             .order_by(Inquiry.created_at.desc()).all()
    return render_template('inquiry/list.html', inquiries=inquiries)


@inquiry_bp.route('/new', methods=['GET', 'POST'])
@login_required
@rate_limit(max_requests=5, window=60, scope='inquiry_new')
def new_inquiry():
    """새 문의 작성."""
    if request.method == 'POST':
        category = request.form.get('category', 'general')
        subject = request.form.get('subject', '').strip()[:200]     # 제목 200자 제한
        body = request.form.get('body', '').strip()[:5000]          # 본문 5000자 제한

        if not subject or not body:
            flash('제목과 내용을 모두 입력해주세요.', 'error')
            return render_template('inquiry/new.html', categories=INQUIRY_CATEGORIES)

        # 카테고리 화이트리스트 검증
        if category not in INQUIRY_CATEGORIES:
            category = 'general'

        inquiry = Inquiry(
            user_id=current_user.id,
            couple_id=current_user.couple_id,
            subject=subject,
            body=body,
            category=category,
        )
        db.session.add(inquiry)
        db.session.commit()

        send_inquiry_notification(inquiry)

        flash('문의가 접수되었습니다! 빠르게 답변 드릴게요 💕', 'success')
        return redirect(url_for('inquiry.list_inquiries'))

    return render_template('inquiry/new.html', categories=INQUIRY_CATEGORIES)


@inquiry_bp.route('/<int:inquiry_id>')
@login_required
def detail(inquiry_id):
    """문의 상세 보기."""
    inquiry = Inquiry.query.get_or_404(inquiry_id)
    if inquiry.user_id != current_user.id:
        flash('접근 권한이 없습니다.', 'error')
        return redirect(url_for('inquiry.list_inquiries'))

    return render_template('inquiry/detail.html', inquiry=inquiry)
