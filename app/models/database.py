from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from .. import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    telegram_id = db.Column(db.Integer, unique=True)
    username = db.Column(db.String(64))
    subscriptions = db.relationship('Subscription', backref='user', lazy='dynamic')
    ratings = db.relationship('Rating', backref='user', lazy='dynamic')

class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Major(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    semesters = db.relationship('Semester', backref='major', lazy='dynamic')

class Semester(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    major_id = db.Column(db.Integer, db.ForeignKey('major.id'))
    lessons = db.relationship('Lesson', backref='semester', lazy='dynamic')

class Lesson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    semester_id = db.Column(db.Integer, db.ForeignKey('semester.id'))
    teachers = db.relationship('Teacher', backref='lesson', lazy='dynamic')
    subscriptions = db.relationship('Subscription', backref='lesson', lazy='dynamic')

class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'))
    notes = db.relationship('Note', backref='teacher', lazy='dynamic')

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    author = db.Column(db.String(64), nullable=False)
    date_written = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text)
    file_path = db.Column(db.String(256), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'))
    rating_sum = db.Column(db.Integer, default=0)  # Sum of all ratings
    rating_count = db.Column(db.Integer, default=0)  # Number of ratings
    ratings = db.relationship('Rating', backref='note', lazy='dynamic')

    @property
    def average_rating(self):
        return self.rating_sum / self.rating_count if self.rating_count > 0 else 0

class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Integer, nullable=False)
    feedback = db.Column(db.Text)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    note_id = db.Column(db.Integer, db.ForeignKey('note.id'))

class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'))
    date_subscribed = db.Column(db.DateTime, default=datetime.utcnow) 