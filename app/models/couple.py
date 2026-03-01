from datetime import datetime
from app.extensions import db


class Couple(db.Model):
    __tablename__ = 'couples'

    id           = db.Column(db.Integer, primary_key=True)
    invite_code  = db.Column(db.String(20), unique=True, nullable=False)
    anniversary  = db.Column(db.Date, nullable=True)
    couple_name  = db.Column(db.String(100), nullable=True)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    pet_name     = db.Column(db.String(50), nullable=True)
    max_members    = db.Column(db.Integer, default=2, nullable=False)
    pity_counter   = db.Column(db.Integer, default=0, nullable=False)
    reroll_tickets = db.Column(db.Integer, default=1, nullable=False)

    members  = db.relationship('User',   backref='couple', lazy='dynamic',
                                foreign_keys='User.couple_id')
    memories = db.relationship('Memory', backref='couple', lazy='dynamic')

    @property
    def days_together(self):
        """커플 D+ 카운터: anniversary(기념일) 또는 created_at 기준."""
        base = self.anniversary or self.created_at.date()
        return (datetime.utcnow().date() - base).days

    @property
    def days_since_join(self):
        """웹사이트 가입일(couple.created_at) 기준 일수 — 펫 성장용."""
        return (datetime.utcnow().date() - self.created_at.date()).days

    @property
    def active_pet(self):
        """현재 활성화된 펫 반환."""
        from app.models.pet import Pet
        return Pet.query.filter_by(couple_id=self.id, is_active=True)\
                        .order_by(Pet.created_at.desc()).first()

    @property
    def pet_info(self):
        """성장 정보 — couple.created_at(가입일) 기준으로 성장."""
        from app.models.pet import GROWTH_STAGES

        days = self.days_since_join
        pet = self.active_pet

        # 가챠 펫이 있으면 사용
        if pet:
            breed_info = pet.breed_info
            emoji = breed_info['emoji']
            name = pet.display_name
            rarity = pet.rarity
            rarity_info = pet.rarity_info
        else:
            # 레거시 fallback: couple id 기반 기본 펫
            _legacy_types = [
                {'emoji': '🐱', 'name': '냥이'},
                {'emoji': '🐶', 'name': '멍이'},
                {'emoji': '🐰', 'name': '토순이'},
                {'emoji': '🐹', 'name': '햄냥이'},
                {'emoji': '🐼', 'name': '판다'},
            ]
            legacy = _legacy_types[self.id % len(_legacy_types)]
            emoji = legacy['emoji']
            name = self.pet_name or legacy['name']
            rarity = 'common'
            rarity_info = {'color': '#9ca3af', 'bg': 'bg-gray-100', 'text': 'text-gray-500',
                           'border': 'border-gray-300', 'glow': '', 'label': '커먼'}

        # 성장 단계 (가입일 기준)
        stage = GROWTH_STAGES[-1]
        for s in GROWTH_STAGES:
            if s['max'] is None or days <= s['max']:
                stage = s
                break

        display_emoji = stage['emoji_override'] or emoji

        return {
            'emoji':       display_emoji,
            'base_emoji':  emoji,
            'name':        name,
            'stage':       stage['label'],
            'size':        stage['size'],
            'days':        days,
            'rarity':      rarity,
            'rarity_info': rarity_info,
            'has_custom':  pet is not None,
            'pet_obj':     pet,
        }

    def __repr__(self):
        return f'<Couple {self.id}>'
