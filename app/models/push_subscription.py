"""
PushSubscription: 브라우저 푸시 구독 정보 저장.
한 유저가 여러 디바이스(폰, 노트북 등)에서 구독 가능.
"""
from datetime import datetime
from app.extensions import db


class PushSubscription(db.Model):
    __tablename__ = 'push_subscriptions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    endpoint = db.Column(db.Text, nullable=False)
    p256dh = db.Column(db.String(200), nullable=False)
    auth = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('push_subscriptions', lazy='dynamic'))

    def to_webpush_dict(self):
        """pywebpush 호출용 포맷."""
        return {
            "endpoint": self.endpoint,
            "keys": {
                "p256dh": self.p256dh,
                "auth": self.auth,
            }
        }

    def __repr__(self):
        return f'<PushSubscription {self.id} user={self.user_id}>'
