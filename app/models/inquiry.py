"""
Inquiry model: user → admin Q&A channel.
"""
from datetime import datetime
from app.extensions import db

INQUIRY_CATEGORIES = {
    'general':        '일반 문의',
    'increase_limit': '인원 증설 요청',
    'bug':            '버그 신고',
    'other':          '기타',
}

INQUIRY_STATUSES = {
    'pending':  '답변 대기',
    'answered': '답변 완료',
    'closed':   '종료',
}


class Inquiry(db.Model):
    __tablename__ = 'inquiries'

    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    couple_id   = db.Column(db.Integer, db.ForeignKey('couples.id'), nullable=True)
    subject     = db.Column(db.String(200), nullable=False)
    body        = db.Column(db.Text, nullable=False)
    category    = db.Column(db.String(30), default='general', nullable=False)
    status      = db.Column(db.String(20), default='pending', nullable=False)
    admin_reply = db.Column(db.Text, nullable=True)
    replied_at  = db.Column(db.DateTime, nullable=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    author = db.relationship('User', backref=db.backref('user_inquiries', lazy='dynamic'),
                             foreign_keys=[user_id])

    @property
    def category_label(self):
        return INQUIRY_CATEGORIES.get(self.category, self.category)

    @property
    def status_label(self):
        return INQUIRY_STATUSES.get(self.status, self.status)

    @property
    def status_color(self):
        return {
            'pending':  'bg-yellow-50 text-yellow-600 border-yellow-200',
            'answered': 'bg-green-50 text-green-600 border-green-200',
            'closed':   'bg-gray-50 text-gray-500 border-gray-200',
        }.get(self.status, 'bg-gray-50 text-gray-500 border-gray-200')

    def __repr__(self):
        return f'<Inquiry {self.id}>'
