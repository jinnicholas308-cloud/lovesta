from datetime import datetime
from app.extensions import db


class Couple(db.Model):
    __tablename__ = 'couples'

    id = db.Column(db.Integer, primary_key=True)
    invite_code = db.Column(db.String(20), unique=True, nullable=False)
    anniversary = db.Column(db.Date, nullable=True)
    couple_name = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    members = db.relationship('User', backref='couple', lazy='dynamic',
                              foreign_keys='User.couple_id')
    memories = db.relationship('Memory', backref='couple', lazy='dynamic')

    @property
    def days_together(self):
        if self.anniversary:
            return (datetime.utcnow().date() - self.anniversary).days
        return None

    def __repr__(self):
        return f'<Couple {self.id}>'
