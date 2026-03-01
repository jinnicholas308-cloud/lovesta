"""
Attendance routes: daily check-in, streak display.
Tickets are stored on the couple (not the user).
보안: 레이트 리밋, couple 유효성 검증.
"""
from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from app.models.attendance import Attendance
from app.utils.security import rate_limit

attendance_bp = Blueprint('attendance', __name__, url_prefix='/attendance')


def _couple_tickets():
    """커플 통합 리롤권 반환."""
    if current_user.couple:
        return getattr(current_user.couple, 'reroll_tickets', 0) or 0
    return getattr(current_user, 'reroll_tickets', 0) or 0


@attendance_bp.route('/check-in', methods=['POST'])
@login_required
@rate_limit(max_requests=5, window=60, scope='attendance_checkin')
def check_in():
    """일일 출석 체크 (서버 UTC 기준)."""
    success, message, tickets = Attendance.check_in(current_user)
    week = Attendance.get_week_progress(current_user.id)

    return jsonify({
        'success': success,
        'message': message,
        'tickets_earned': tickets,
        'total_tickets': _couple_tickets(),
        'week_progress': week,
    })


@attendance_bp.route('/status')
@login_required
def status():
    """출석 현황 조회."""
    week = Attendance.get_week_progress(current_user.id)
    checked_today = Attendance.has_checked_today(current_user.id)

    return jsonify({
        'checked_today': checked_today,
        'week_progress': week,
        'total_tickets': _couple_tickets(),
    })
