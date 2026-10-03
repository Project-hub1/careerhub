from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from ..extensions import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='candidate', index=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_login_at = db.Column(db.DateTime)
    candidate_profile = db.relationship('JobSeekerProfile', back_populates='user', uselist=False, cascade='all, delete-orphan')
    recruiter_profile = db.relationship('RecruiterProfile', back_populates='user', uselist=False, cascade='all, delete-orphan')
    def set_password(self, password): self.password_hash = generate_password_hash(password)
    def check_password(self, password): return check_password_hash(self.password_hash, password)

class JobSeekerProfile(db.Model):
    __tablename__ = 'job_seeker_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    full_name = db.Column(db.String(120), default='')
    headline = db.Column(db.String(180), default='')
    location = db.Column(db.String(120), default='')
    phone = db.Column(db.String(30), default='')
    summary = db.Column(db.Text, default='')
    skills_text = db.Column(db.Text, default='')
    preferred_role = db.Column(db.String(180), default='')
    expected_salary = db.Column(db.Integer)
    resume_filename = db.Column(db.String(255))
    resume_original_name = db.Column(db.String(255))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user = db.relationship('User', back_populates='candidate_profile')
    education = db.relationship('Education', back_populates='profile', cascade='all, delete-orphan')
    experience = db.relationship('Experience', back_populates='profile', cascade='all, delete-orphan')

class RecruiterProfile(db.Model):
    __tablename__ = 'recruiter_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    full_name = db.Column(db.String(120), default='')
    designation = db.Column(db.String(120), default='Recruiter')
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'))
    user = db.relationship('User', back_populates='recruiter_profile')
    company = db.relationship('Company', back_populates='recruiters')

class Education(db.Model):
    __tablename__ = 'education'
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('job_seeker_profiles.id'), nullable=False)
    degree = db.Column(db.String(160), nullable=False)
    institution = db.Column(db.String(200), nullable=False)
    year = db.Column(db.Integer)
    profile = db.relationship('JobSeekerProfile', back_populates='education')

class Experience(db.Model):
    __tablename__ = 'experience'
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('job_seeker_profiles.id'), nullable=False)
    title = db.Column(db.String(160), nullable=False)
    company = db.Column(db.String(200), nullable=False)
    years = db.Column(db.Float, default=0)
    profile = db.relationship('JobSeekerProfile', back_populates='experience')
