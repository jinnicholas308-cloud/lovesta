"""
In-app notification system + Web Push.
Types: memory_upload, comment, like, inquiry_reply, attendance, gacha, message, question, system
"""
import json
from datetime import datetime
from app.extensions import db


NOTIFICATION_TYPES = {
    'memory_upload':  {'icon': '+', 'label': '새 추억'},
    'comment':        {'icon': '"', 'label': '댓글'},
    'like':           {'icon': '♥', 'label': '좋아요'},
    'inquiry_reply':  {'icon': '>', 'label': '문의 답변'},
    'attendance':     {'icon': '!', 'label': '출석'},
    'gacha':          {'icon': '*', 'label': '가챠'},
    'message':        {'icon': '💬', 'label': '메시지'},
    'question':       {'icon': '❓', 'label': '데일리 질문'},
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
        """Send notification to all couple members EXCEPT the given user.
        Also sends web push to each partner.
        """
        if not user.couple_id:
            return
        from app.models.user import User
        partners = User.query.filter(
            User.couple_id == user.couple_id,
            User.id != user.id
        ).all()
        for partner in partners:
            Notification.send(partner.id, type, title, body, url)
            Notification.send_push_to_user(
                partner.id, title, body=body, url=url, tag=type
            )

    @staticmethod
    def send_push_to_user(user_id, title, body=None, url=None, tag=None):
        """Send web push notification to all subscriptions of a user."""
        from flask import current_app

        private_key = current_app.config.get('VAPID_PRIVATE_KEY')
        public_key = current_app.config.get('VAPID_PUBLIC_KEY')
        claims_email = current_app.config.get('VAPID_CLAIMS_EMAIL', 'mailto:admin@lovesta.app')

        if not private_key or not public_key:
            return  # VAPID 미설정 → skip

        from app.models.push_subscription import PushSubscription
        subscriptions = PushSubscription.query.filter_by(user_id=user_id).all()

        if not subscriptions:
            return

        try:
            from pywebpush import webpush, WebPushException
        except ImportError:
            current_app.logger.warning('[Push] pywebpush not installed')
            return

        payload = json.dumps({
            'title': title,
            'body': body or '',
            'url': url or '/',
            'tag': tag or 'lovesta-default',
        })

        for sub in subscriptions:
            try:
                webpush(
                    subscription_info=sub.to_webpush_dict(),
                    data=payload,
                    vapid_private_key=private_key,
                    vapid_claims={"sub": claims_email},
                )
            except WebPushException as e:
                # 410 Gone / 404 = 구독 만료 → 자동 삭제
                if '410' in str(e) or '404' in str(e):
                    db.session.delete(sub)
                    db.session.commit()
                current_app.logger.warning(f'[Push] Failed for sub {sub.id}: {e}')
            except Exception as e:
                current_app.logger.warning(f'[Push] Unexpected error for sub {sub.id}: {e}')

    @staticmethod
    def unread_count(user_id):
        return Notification.query.filter_by(user_id=user_id, is_read=False).count()

    def __repr__(self):
        return f'<Notification {self.id} {self.type}>'
