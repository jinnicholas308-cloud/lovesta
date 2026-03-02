"""
CoupleMessage: 커플 멤버 간 메모/위치/생각 공유 (인스타 DM 스타일)
"""
from datetime import datetime
from app.extensions import db


class CoupleMessage(db.Model):
    __tablename__ = 'couple_messages'

    id = db.Column(db.Integer, primary_key=True)
    couple_id = db.Column(db.Integer, db.ForeignKey('couples.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # 메시지 타입: memo(메모), location(위치), thought(생각/감정), photo(사진)
    msg_type = db.Column(db.String(20), default='memo', nullable=False)

    content = db.Column(db.Text, nullable=False)

    # 위치 정보 (선택)
    location_name = db.Column(db.String(200), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)

    # 사진 (선택)
    image_path = db.Column(db.String(256), nullable=True)

    # 감정/무드 이모지 (선택)
    mood = db.Column(db.String(10), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    author = db.relationship('User', backref=db.backref('couple_messages', lazy='dynamic'))

    # 메시지 타입별 아이콘 매핑
    TYPE_ICONS = {
        'memo': '📝',
        'location': '📍',
        'thought': '💭',
        'photo': '📷',
    }

    TYPE_LABELS = {
        'memo': '메모',
        'location': '위치 공유',
        'thought': '오늘의 생각',
        'photo': '사진',
    }

    @property
    def type_icon(self):
        return self.TYPE_ICONS.get(self.msg_type, '📝')

    @property
    def type_label(self):
        return self.TYPE_LABELS.get(self.msg_type, '메모')

    def __repr__(self):
        return f'<CoupleMessage {self.id} type={self.msg_type}>'
