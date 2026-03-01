"""
In-app notification system.
Types: memory_upload, comment, like, inquiry_reply, attendance_reminder, system
"""
from datetime import datetime
from app.extensions import db


NOTIFICATION_TYPES = {
    'memory_upload':  {'icon': '+', 'label': '새 추억'},
    'comment':        {'icon': '"', 'label': '댓글'},
    'like':           {'icon': '♥', 'label': '좋아요'},
    'inquiry_reply':  {'icon': '>', 'label': '문의 답변'},
    'attendance':     {'icon': '!', 'label': '출석'},
    'gacha':          {'icon': '*', 'label': '가챠'},
    'system':         {'icon': 'i', 'label': '시스템'},
}


class Notification(db.Model):
    __tablename__ = 'notifications'

    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type        = db.Column(db.String(30), default='system', nullable=False)
    title       = db.Column(db.String(200), nullable=False)
    body        = db.Column(db.Text, nullable=True)
    url         = db.Column(db.String(500), nullable=True)   # click destination
    is_read     = db.Column(db.Boolean, default=False, nullable=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('notifications', lazy='dynamic'))

    @property
    def type_info(self):
        return NOTIFICATION_TYPES.get(self.type, NOTIFICATION_TYPES['system'])

    @property
    def icon(self):
        return self.type_info['icon']

    @property
    def time_ago(self):
        diff = datetime.utcnow() - self.created_at
        seconds = diff.total_seconds()
        if seconds < 60:
            return '방금 전'
        elif seconds < 3600:
            return f'{int(seconds // 60)}분 전'
        elif seconds < 86400:
            return f'{int(seconds // 3600)}시간 전'
        elif seconds < 604800:
            return f'{int(seconds // 86400)}일 전'
        else:
            return self.created_at.strftime('%m월 %d일')

    @staticmethod
    def send(user_id, type, title, body=None, url=None):
        """Create and save a notification."""
        n = Notification(user_id=user_id, type=type, title=title, body=body, url=url)
        db.session.add(n)
        return n

    @staticmethod
    def send_to_couple_partner(user, type, title, body=None, url=None):
        """Send notification to all couple members EXCEPT the given user."""
        if not user.couple_id:
            return
        from app.models.user import User
        partners = User.query.filter(
            User.couple_id == user.couple_id,
            User.id != user.id
        ).all()
        for partner in partners:
            Notification.send(partner.id, type, title, body, url)

    @staticmethod
    def unread_count(user_id):
        return Notification.query.filter_by(user_id=user_id, is_read=False).count()

    def __repr__(self):
        return f'<Notification {self.id} {self.type}>'
