"""
Attendance routes: daily check-in, streak display.
"""
from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from app.models.attendance import Attendance

attendance_bp = Blueprint('attendance', __name__, url_prefix='/attendance')


@attendance_bp.route('/check-in', methods=['POST'])
@login_required
def check_in():
    """일일 출석 체크 (서버 UTC 기준)."""
    success, message, tickets = Attendance.check_in(current_user)

    # 현재 주간 진행상황
    week = Attendance.get_week_progress(current_user.id)

    return jsonify({
        'success': success,
        'message': message,
        'tickets_earned': tickets,
        'total_tickets': current_user.reroll_tickets,
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
        'total_tickets': current_user.reroll_tickets or 0,
    })
