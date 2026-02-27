from datetime import datetime
from app.extensions import db


_PET_TYPES = [
    {'emoji': '🐱', 'name': '냥이',   'color': 'rose'},
    {'emoji': '🐶', 'name': '멍이',   'color': 'amber'},
    {'emoji': '🐰', 'name': '토순이', 'color': 'pink'},
    {'emoji': '🐹', 'name': '햄냥이', 'color': 'orange'},
    {'emoji': '🐼', 'name': '판다',   'color': 'gray'},
]

_PET_STAGES = [
    {'min': 0,   'max': 6,   'label': '알',    'size': 'text-4xl', 'emoji_override': '🥚'},
    {'min': 7,   'max': 29,  'label': '아기',   'size': 'text-4xl', 'emoji_override': None},
    {'min': 30,  'max': 99,  'label': '아이',   'size': 'text-5xl', 'emoji_override': None},
    {'min': 100, 'max': 364, 'label': '청소년', 'size': 'text-6xl', 'emoji_override': None},
    {'min': 365, 'max': None,'label': '어른',   'size': 'text-7xl', 'emoji_override': None},
]


class Couple(db.Model):
    __tablename__ = 'couples'

    id          = db.Column(db.Integer, primary_key=True)
    invite_code = db.Column(db.String(20), unique=True, nullable=False)
    anniversary = db.Column(db.Date, nullable=True)
    couple_name = db.Column(db.String(100), nullable=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    pet_name    = db.Column(db.String(50), nullable=True)

    members  = db.relationship('User',   backref='couple', lazy='dynamic',
                                foreign_keys='User.couple_id')
    memories = db.relationship('Memory', backref='couple', lazy='dynamic')

    @property
    def days_together(self):
        base = self.anniversary or self.created_at.date()
        return (datetime.utcnow().date() - base).days

    @property
    def pet_info(self):
        days = self.days_together or 0
        pet  = _PET_TYPES[self.id % len(_PET_TYPES)]

        stage = _PET_STAGES[-1]
        for s in _PET_STAGES:
            if s['max'] is None or days <= s['max']:
                stage = s
                break

        emoji = stage['emoji_override'] or pet['emoji']
        name  = self.pet_name or pet['name']
        return {
            'emoji':      emoji,
            'base_emoji': pet['emoji'],
            'name':       name,
            'stage':      stage['label'],
            'size':       stage['size'],
            'color':      pet['color'],
            'days':       days,
        }

    def __repr__(self):
        return f'<Couple {self.id}>'
