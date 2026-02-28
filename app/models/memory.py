from datetime import datetime
from app.extensions import db


class Memory(db.Model):
    __tablename__ = 'memories'

    id = db.Column(db.Integer, primary_key=True)
    caption = db.Column(db.Text, nullable=False)
    image_path = db.Column(db.String(256), nullable=True)
    media_type = db.Column(db.String(10), default='image', nullable=False)
    location = db.Column(db.String(200), nullable=True)
    memory_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    couple_id = db.Column(db.Integer, db.ForeignKey('couples.id'), nullable=False)

    comments = db.relationship('Comment', backref='memory', lazy='dynamic',
                               cascade='all, delete-orphan')
    likes = db.relationship('Like', backref='memory', lazy='dynamic',
                            cascade='all, delete-orphan')

    def like_count(self):
        return self.likes.count()

    def is_liked_by(self, user):
        if user.is_anonymous:
            return False
        return self.likes.filter_by(user_id=user.id).first() is not None

    def __repr__(self):
        return f'<Memory {self.id}>'


class Comment(db.Model):
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    memory_id = db.Column(db.Integer, db.ForeignKey('memories.id'), nullable=False)

    def __repr__(self):
        return f'<Comment {self.id}>'


class Like(db.Model):
    __tablename__ = 'likes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    memory_id = db.Column(db.Integer, db.ForeignKey('memories.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('user_id', 'memory_id', name='unique_like'),)
