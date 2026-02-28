"""
Pet gacha system: breeds, rarity tiers, MBTI personalities, growth stages.
"""
from datetime import datetime
from app.extensions import db


# ── 희귀도 정의 (기하급수적 확률) ──
RARITIES = {
    'common':    {'label': '커먼',     'prob': 0.50,  'color': '#9ca3af', 'bg': 'bg-gray-100',    'text': 'text-gray-500',    'border': 'border-gray-300',   'glow': ''},
    'uncommon':  {'label': '언커먼',   'prob': 0.25,  'color': '#22c55e', 'bg': 'bg-green-50',    'text': 'text-green-500',   'border': 'border-green-300',  'glow': ''},
    'rare':      {'label': '레어',     'prob': 0.15,  'color': '#3b82f6', 'bg': 'bg-blue-50',     'text': 'text-blue-500',    'border': 'border-blue-400',   'glow': 'shadow-blue-200'},
    'epic':      {'label': '에픽',     'prob': 0.07,  'color': '#a855f7', 'bg': 'bg-purple-50',   'text': 'text-purple-500',  'border': 'border-purple-400', 'glow': 'shadow-purple-200'},
    'legendary': {'label': '레전더리', 'prob': 0.025, 'color': '#f59e0b', 'bg': 'bg-amber-50',    'text': 'text-amber-500',   'border': 'border-amber-400',  'glow': 'shadow-amber-300'},
    'mythic':    {'label': '미식',     'prob': 0.005, 'color': '#f43f5e', 'bg': 'bg-rose-50',     'text': 'text-rose-500',    'border': 'border-rose-400',   'glow': 'shadow-rose-400'},
}

RARITY_ORDER = ['common', 'uncommon', 'rare', 'epic', 'legendary', 'mythic']

# ── 종(Breed) 정의 ──
BREEDS = {
    'cat':      {'emoji': '🐱', 'name': '고양이'},
    'dog':      {'emoji': '🐶', 'name': '강아지'},
    'bunny':    {'emoji': '🐰', 'name': '토끼'},
    'hamster':  {'emoji': '🐹', 'name': '햄스터'},
    'panda':    {'emoji': '🐼', 'name': '판다'},
    'fox':      {'emoji': '🦊', 'name': '여우'},
    'unicorn':  {'emoji': '🦄', 'name': '유니콘'},
    'dragon':   {'emoji': '🐉', 'name': '드래곤'},
    'phoenix':  {'emoji': '🔥', 'name': '불사조'},
}

# ── MBTI 성격 매핑 ──
PERSONALITIES = {
    'INTJ': '전략가',  'INTP': '논리학자', 'ENTJ': '통솔자', 'ENTP': '변론가',
    'INFJ': '옹호자',  'INFP': '중재자',   'ENFJ': '선도자', 'ENFP': '활동가',
    'ISTJ': '현실주의', 'ISFJ': '수호자',  'ESTJ': '경영자', 'ESFJ': '집정관',
    'ISTP': '장인',    'ISFP': '모험가',   'ESTP': '사업가', 'ESFP': '연예인',
}
MBTI_LIST = list(PERSONALITIES.keys())

# ── 성장 단계 (couple.created_at 기준) ──
GROWTH_STAGES = [
    {'min': 0,   'max': 6,    'label': '알',    'emoji_override': '🥚', 'size': 'text-4xl'},
    {'min': 7,   'max': 29,   'label': '아기',   'emoji_override': None, 'size': 'text-4xl'},
    {'min': 30,  'max': 99,   'label': '아이',   'emoji_override': None, 'size': 'text-5xl'},
    {'min': 100, 'max': 364,  'label': '청소년', 'emoji_override': None, 'size': 'text-6xl'},
    {'min': 365, 'max': None, 'label': '어른',   'emoji_override': None, 'size': 'text-7xl'},
]

# ── 천장(Pity) 설정 ──
PITY_THRESHOLD = 50  # 50연차 안에 레어 이상 안 나오면 확정
TEN_PULL_GUARANTEE_INDEX = 9  # 10번째(인덱스 9) 카드는 레어 이상 확정


class Pet(db.Model):
    __tablename__ = 'pets'

    id         = db.Column(db.Integer, primary_key=True)
    couple_id  = db.Column(db.Integer, db.ForeignKey('couples.id'), nullable=False)
    breed      = db.Column(db.String(30), nullable=False)
    rarity     = db.Column(db.String(20), nullable=False)
    personality = db.Column(db.String(4), nullable=True)  # MBTI code
    name       = db.Column(db.String(50), nullable=True)
    is_active  = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    couple = db.relationship('Couple', backref=db.backref('pets', lazy='dynamic'))

    @property
    def breed_info(self):
        return BREEDS.get(self.breed, BREEDS['cat'])

    @property
    def rarity_info(self):
        return RARITIES.get(self.rarity, RARITIES['common'])

    @property
    def personality_label(self):
        return PERSONALITIES.get(self.personality, '')

    @property
    def display_emoji(self):
        return self.breed_info['emoji']

    @property
    def display_name(self):
        return self.name or self.breed_info['name']

    def __repr__(self):
        return f'<Pet {self.id} {self.breed}/{self.rarity}>'
