from app import db
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone, timedelta, UTC
from app import app
from werkzeug.security import generate_password_hash, check_password_hash


def get_ist_time():
    IST = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(IST)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True, nullable=False)
    passhash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    name = db.Column(db.String(32), nullable=False)
    dob = db.Column(db.Date, nullable=True)
    qualification = db.Column(db.String(32), nullable=True)
    scores = db.relationship('Scores', backref='user', cascade='all, delete-orphan')#User.scores

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False)
    desc = db.Column(db.String(256), nullable=True)
    chapters = db.relationship('Chapter', backref='subject', cascade='all, delete-orphan')#Subject.chapters

class Chapter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False)
    desc = db.Column(db.String(256), nullable=True)
    sub_id = db.Column(db.Integer, db.ForeignKey('subject.id', ondelete='CASCADE'), nullable=False)
    quizzes = db.relationship('Quiz', backref='chapter', cascade='all, delete-orphan')#Chapter.quizzes

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False)
    chap_id = db.Column(db.Integer, db.ForeignKey('chapter.id', ondelete='CASCADE'), nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    pub_date = db.Column(db.Date, nullable=False, default=lambda: datetime.now(UTC))
    questions = db.relationship('Question', backref='quiz', cascade='all, delete-orphan')#Quiz.questions
    scores = db.relationship('Scores', backref='quiz', cascade='all, delete-orphan')#Quiz.scores
    #lazy = True?

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False)
    q_statement = db.Column(db.String(256), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id', ondelete='CASCADE'), nullable=False)
    opt1 = db.Column(db.String(32), nullable=False)
    opt2 = db.Column(db.String(32), nullable=False)
    opt3 = db.Column(db.String(32), nullable=False)
    opt4 = db.Column(db.String(32), nullable=False)
    ans = db.Column(db.Integer, nullable=False)

class Scores(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id', ondelete='CASCADE'), nullable=False)
    total_score = db.Column(db.Integer, nullable=False)
    datetime = db.Column(db.DateTime, nullable=False)
    #time_stamp = db.Column(db.DateTime(timezone=True), nullable=False, default=get_ist_time)
    #if switching to postgres or another database, store in utc and display in ist

with app.app_context():
    db.create_all()
    admin = User.query.filter_by(is_admin=True).first()
    if not admin:
        password_hash = generate_password_hash('admin')
        admin = User(username='admin', passhash=password_hash, name='Admin', is_admin=True)
        db.session.add(admin)
        db.session.commit()