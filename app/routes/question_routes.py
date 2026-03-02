"""
Daily Couple Questions: 커플 데일리 질문 (Sumone 스타일)
- 매일 새 질문 자동 생성
- 커스텀 질문 만들기
- 둘 다 답변해야 서로 볼 수 있음
"""
import random
from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models.daily_question import (
    DailyQuestion, QuestionAnswer, QuestionSchedule, DEFAULT_QUESTIONS
)

question_bp = Blueprint('questions', __name__, url_prefix='/questions')


def _get_or_create_today_question(couple_id):
    """오늘의 질문을 가져오거나 새로 생성"""
    today = date.today()

    # 오늘 질문이 있는지 확인
    question = DailyQuestion.query.filter_by(
        couple_id=couple_id,
        question_date=today
    ).first()

    if question:
        return question

    # 이전에 사용한 질문 텍스트 수집
    used_questions = [q.question_text for q in
                      DailyQuestion.query.filter_by(couple_id=couple_id)
                      .order_by(DailyQuestion.question_date.desc())
                      .limit(len(DEFAULT_QUESTIONS) - 5)
                      .all()]

    # 사용하지 않은 질문 우선 선택
    available = [q for q in DEFAULT_QUESTIONS if q not in used_questions]
    if not available:
        available = DEFAULT_QUESTIONS  # 모든 질문을 사용했으면 리셋

    question_text = random.choice(available)

    question = DailyQuestion(
        couple_id=couple_id,
        question_text=question_text,
        question_date=today,
        is_custom=False,
    )
    db.session.add(question)
    db.session.commit()

    return question


@question_bp.route('/')
@login_required
def index():
    """데일리 질문 메인 페이지"""
    if not current_user.couple_id:
        flash('먼저 커플을 연결해주세요!', 'warning')
        return redirect(url_for('couple.setup'))

    couple_id = current_user.couple_id

    # 오늘의 질문
    today_question = _get_or_create_today_question(couple_id)

    # 내 답변 확인
    my_answer = today_question.get_answer_by(current_user.id)

    # 파트너 찾기
    partner = None
    for m in current_user.couple.members:
        if m.id != current_user.id:
            partner = m
            break

    partner_answer = today_question.get_answer_by(partner.id) if partner else None
    both_answered = today_question.both_answered

    # 이전 질문 히스토리 (최근 14일)
    past_questions = DailyQuestion.query.filter(
        DailyQuestion.couple_id == couple_id,
        DailyQuestion.question_date < date.today()
    ).order_by(DailyQuestion.question_date.desc()).limit(14).all()

    # 스케줄 설정
    schedule = QuestionSchedule.query.filter_by(couple_id=couple_id).first()

    return render_template('couple/questions.html',
                           today_question=today_question,
                           my_answer=my_answer,
                           partner=partner,
                           partner_answer=partner_answer,
                           both_answered=both_answered,
                           past_questions=past_questions,
                           schedule=schedule)


@question_bp.route('/answer', methods=['POST'])
@login_required
def answer():
    """오늘의 질문에 답변"""
    if not current_user.couple_id:
        return redirect(url_for('couple.setup'))

    question_id = request.form.get('question_id', type=int)
    answer_text = request.form.get('answer_text', '').strip()

    if not question_id or not answer_text:
        flash('답변을 입력해주세요!', 'error')
        return redirect(url_for('questions.index'))

    question = DailyQuestion.query.get_or_404(question_id)

    # 본인 커플의 질문인지 확인
    if question.couple_id != current_user.couple_id:
        flash('접근 권한이 없습니다.', 'error')
        return redirect(url_for('questions.index'))

    # 이미 답변했는지 확인
    existing = question.get_answer_by(current_user.id)
    if existing:
        flash('이미 답변했어요! 답변은 수정할 수 없어요.', 'warning')
        return redirect(url_for('questions.index'))

    answer = QuestionAnswer(
        question_id=question.id,
        user_id=current_user.id,
        answer_text=answer_text[:1000],  # 1000자 제한
    )
    db.session.add(answer)
    db.session.commit()

    # 파트너에게 알림 (인앱 + 푸시)
    from app.models.notification import Notification
    Notification.send_to_couple_partner(
        current_user, 'question',
        f'{current_user.username}님이 오늘의 질문에 답변했어요!',
        body=question.question_text[:100],
        url=url_for('questions.index')
    )
    db.session.commit()

    flash('답변이 저장되었어요! 💕', 'success')
    return redirect(url_for('questions.index'))


@question_bp.route('/custom', methods=['POST'])
@login_required
def create_custom():
    """내일의 커스텀 질문 만들기"""
    if not current_user.couple_id:
        return redirect(url_for('couple.setup'))

    question_text = request.form.get('question_text', '').strip()
    target_date_str = request.form.get('target_date', '').strip()

    if not question_text:
        flash('질문을 입력해주세요!', 'error')
        return redirect(url_for('questions.index'))

    # 대상 날짜 (기본: 내일)
    if target_date_str:
        try:
            target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
        except ValueError:
            target_date = date.today() + timedelta(days=1)
    else:
        target_date = date.today() + timedelta(days=1)

    # 과거 날짜 방지
    if target_date <= date.today():
        target_date = date.today() + timedelta(days=1)

    # 이미 해당 날짜에 질문이 있는지 확인
    existing = DailyQuestion.query.filter_by(
        couple_id=current_user.couple_id,
        question_date=target_date
    ).first()

    if existing:
        # 기존 질문 교체
        existing.question_text = question_text[:500]
        existing.is_custom = True
        existing.created_by = current_user.id
    else:
        question = DailyQuestion(
            couple_id=current_user.couple_id,
            question_text=question_text[:500],
            question_date=target_date,
            is_custom=True,
            created_by=current_user.id,
        )
        db.session.add(question)

    db.session.commit()
    flash(f'{target_date.strftime("%m월 %d일")} 질문이 등록되었어요!', 'success')
    return redirect(url_for('questions.index'))


@question_bp.route('/history/<int:question_id>')
@login_required
def history_detail(question_id):
    """과거 질문 상세 보기"""
    question = DailyQuestion.query.get_or_404(question_id)

    if question.couple_id != current_user.couple_id:
        flash('접근 권한이 없습니다.', 'error')
        return redirect(url_for('questions.index'))

    partner = None
    for m in current_user.couple.members:
        if m.id != current_user.id:
            partner = m
            break

    my_answer = question.get_answer_by(current_user.id)
    partner_answer = question.get_answer_by(partner.id) if partner else None

    return jsonify({
        'question': question.question_text,
        'date': question.question_date.strftime('%Y년 %m월 %d일'),
        'is_custom': question.is_custom,
        'my_answer': my_answer.answer_text if my_answer else None,
        'partner_answer': partner_answer.answer_text if partner_answer and question.both_answered else None,
        'partner_name': partner.username if partner else None,
        'both_answered': question.both_answered,
    })


@question_bp.route('/schedule', methods=['POST'])
@login_required
def update_schedule():
    """질문 스케줄 설정 업데이트"""
    if not current_user.couple_id:
        return redirect(url_for('couple.setup'))

    notify_time = request.form.get('notify_time', '09:00').strip()
    is_active = request.form.get('is_active') == 'on'

    # 시간 형식 검증
    try:
        datetime.strptime(notify_time, '%H:%M')
    except ValueError:
        notify_time = '09:00'

    schedule = QuestionSchedule.query.filter_by(couple_id=current_user.couple_id).first()
    if schedule:
        schedule.notify_time = notify_time
        schedule.is_active = is_active
    else:
        schedule = QuestionSchedule(
            couple_id=current_user.couple_id,
            notify_time=notify_time,
            is_active=is_active,
        )
        db.session.add(schedule)

    db.session.commit()
    flash('설정이 저장되었어요!', 'success')
    return redirect(url_for('questions.index'))
