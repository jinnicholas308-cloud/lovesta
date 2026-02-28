"""
Daily attendance tracking for reroll ticket rewards.
Server UTC time is the single source of truth to prevent client time manipulation.
"""
from datetime import datetime, date, timedelta
from app.extensions import db


class Attendance(db.Model):
    __tablename__ = 'attendances'

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date       = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'date', name='unique_attendance'),
    )

    @staticmethod
    def check_in(user):
        """
        출석 체크 (하루 1회, 서버 UTC 기준).
        리롤권 지급: 매일 1장 + 7일 연속 완성 시 보너스 3장.
        Returns (success: bool, message: str, tickets_earned: int)
        """
        today = datetime.utcnow().date()

        # 중복 방지 (Idempotency)
        existing = Attendance.query.filter_by(user_id=user.id, date=today).first()
        if existing:
            return False, '오늘은 이미 출석했어요!', 0

        att = Attendance(user_id=user.id, date=today)
        db.session.add(att)

        # 기본 리롤권 1장
        tickets = 1
        user.reroll_tickets = (user.reroll_tickets or 0) + 1

        # 7일 연속 출석 보너스 체크
        streak = Attendance.get_current_streak(user.id, today)
        if streak >= 6:  # 이번이 7일째 (이미 6일 있고 오늘 추가)
            user.reroll_tickets += 3
            tickets += 3

        db.session.commit()
        return True, f'출석 완료! 리롤권 {tickets}장 획득', tickets

    @staticmethod
    def get_current_streak(user_id, reference_date=None):
        """현재 연속 출석 일수 (오늘 포함하지 않은 과거 기준)."""
        if reference_date is None:
            reference_date = datetime.utcnow().date()

        streak = 0
        check_date = reference_date - timedelta(days=1)

        while True:
            att = Attendance.query.filter_by(user_id=user_id, date=check_date).first()
            if not att:
                break
            streak += 1
            check_date -= timedelta(days=1)

        return streak

    @staticmethod
    def get_week_progress(user_id):
        """이번 주(월~일) 출석 현황 반환."""
        today = datetime.utcnow().date()
        # 이번 주 월요일
        monday = today - timedelta(days=today.weekday())
        days = []
        for i in range(7):
            d = monday + timedelta(days=i)
            att = Attendance.query.filter_by(user_id=user_id, date=d).first()
            days.append({
                'date': d,
                'weekday': ['월', '화', '수', '목', '금', '토', '일'][i],
                'checked': att is not None,
                'is_today': d == today,
                'is_future': d > today,
            })
        checked_count = sum(1 for d in days if d['checked'])
        return {'days': days, 'count': checked_count, 'total': 7}

    @staticmethod
    def has_checked_today(user_id):
        today = datetime.utcnow().date()
        return Attendance.query.filter_by(user_id=user_id, date=today).first() is not None
