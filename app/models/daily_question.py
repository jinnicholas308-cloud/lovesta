"""
DailyQuestion & QuestionAnswer: 커플 데일리 질문 시스템 (Sumone 스타일)
- 매일 정해진 시간에 질문이 나옴
- 커플 각자가 답변을 작성
- 둘 다 답변해야 서로의 답변을 볼 수 있음
"""
from datetime import datetime, date
from app.extensions import db


# ──────────────────── 기본 질문 풀 ────────────────────
DEFAULT_QUESTIONS = [
    # 가벼운 일상
    "오늘 하루 중 가장 행복했던 순간은?",
    "요즘 가장 듣고 싶은 말이 있다면?",
    "상대방의 어떤 점이 가장 좋아?",
    "우리가 처음 만났을 때 첫인상은?",
    "함께 가고 싶은 여행지가 있다면?",
    "상대방에게 고마운 점 3가지는?",
    "요즘 가장 스트레스 받는 일은?",
    "내일 하루를 완전 자유롭게 보낸다면?",
    "우리의 10년 후 모습은 어떨까?",
    "상대방이 만들어준 음식 중 최고는?",
    # 깊은 대화
    "사랑한다는 걸 어떤 순간에 가장 많이 느껴?",
    "우리 관계에서 가장 소중한 것은?",
    "상대방에게 꼭 해주고 싶은 것은?",
    "가장 기억에 남는 우리의 추억은?",
    "서로에게 바라는 점이 있다면?",
    "요즘 나의 감정 상태를 색깔로 표현하면?",
    "상대방의 꿈을 얼마나 알고 있어?",
    "같이 늙어가는 것에 대해 어떻게 생각해?",
    "우리만의 특별한 루틴이 있다면?",
    "상대방이 힘들 때 내가 해줄 수 있는 것은?",
    # 재미있는 질문
    "상대방을 동물로 표현하면?",
    "우리 커플 노래를 정한다면 어떤 노래?",
    "상대방의 귀여운 습관 하나는?",
    "데이트할 때 가장 좋았던 곳은?",
    "상대방에게 별명을 새로 지어준다면?",
    "같이 도전해보고 싶은 것은?",
    "상대방의 패션 스타일 점수는 몇 점?",
    "우리 커플의 장점과 단점은?",
    "기념일에 가장 받고 싶은 선물은?",
    "상대방이 가장 잘하는 것은?",
    # 미래/꿈
    "함께 살게 된다면 어디에서 살고 싶어?",
    "같이 키우고 싶은 반려동물이 있다면?",
    "결혼식은 어떻게 하고 싶어?",
    "아이가 생긴다면 이름은 뭘로 지을래?",
    "은퇴 후에 같이 하고 싶은 것은?",
]


class DailyQuestion(db.Model):
    """커플 데일리 질문"""
    __tablename__ = 'daily_questions'

    id = db.Column(db.Integer, primary_key=True)
    couple_id = db.Column(db.Integer, db.ForeignKey('couples.id'), nullable=False)

    question_text = db.Column(db.Text, nullable=False)
    question_date = db.Column(db.Date, nullable=False)  # 이 질문이 해당하는 날짜
    is_custom = db.Column(db.Boolean, default=False)     # 커스텀 질문 여부
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # 커스텀 질문 작성자

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    answers = db.relationship('QuestionAnswer', backref='question', lazy='dynamic',
                              cascade='all, delete-orphan')
    creator = db.relationship('User', backref=db.backref('created_questions', lazy='dynamic'))

    __table_args__ = (
        db.UniqueConstraint('couple_id', 'question_date', name='unique_daily_question'),
    )

    @property
    def both_answered(self):
        """둘 다 답변했는지 확인"""
        return self.answers.count() >= 2

    @property
    def answer_count(self):
        return self.answers.count()

    def get_answer_by(self, user_id):
        return self.answers.filter_by(user_id=user_id).first()

    def __repr__(self):
        return f'<DailyQuestion {self.id} date={self.question_date}>'


class QuestionAnswer(db.Model):
    """질문에 대한 답변"""
    __tablename__ = 'question_answers'

    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('daily_questions.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    answer_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    author = db.relationship('User', backref=db.backref('question_answers', lazy='dynamic'))

    __table_args__ = (
        db.UniqueConstraint('question_id', 'user_id', name='unique_question_answer'),
    )

    def __repr__(self):
        return f'<QuestionAnswer {self.id}>'


class QuestionSchedule(db.Model):
    """커플별 질문 스케줄 설정"""
    __tablename__ = 'question_schedules'

    id = db.Column(db.Integer, primary_key=True)
    couple_id = db.Column(db.Integer, db.ForeignKey('couples.id'), nullable=False, unique=True)

    # 질문 알림 시간 (HH:MM 형식, 예: "09:00")
    notify_time = db.Column(db.String(5), default='09:00', nullable=False)

    # 활성화 여부
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    couple = db.relationship('Couple', backref=db.backref('question_schedule', uselist=False))

    def __repr__(self):
        return f'<QuestionSchedule couple={self.couple_id} time={self.notify_time}>'
