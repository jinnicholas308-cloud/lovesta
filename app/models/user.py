from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=True)   # NULL = OAuth-only account
    profile_image = db.Column(db.String(256), default=None)
    google_id = db.Column(db.String(100), unique=True, nullable=True)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    couple_id = db.Column(db.Integer, db.ForeignKey('couples.id'), nullable=True)

    memories = db.relationship('Memory', backref='author', lazy='dynamic',
                               foreign_keys='Memory.user_id')
    comments = db.relationship('Comment', backref='author', lazy='dynamic')

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    @property
    def is_oauth_user(self) -> bool:
        return self.google_id is not None and self.password_hash is None

    def __repr__(self):
        return f'<User {self.username}>'
