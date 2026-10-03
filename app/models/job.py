from datetime import datetime
from ..extensions import db

job_skills = db.Table('job_skills',
    db.Column('job_id', db.Integer, db.ForeignKey('jobs.id'), primary_key=True),
    db.Column('skill_id', db.Integer, db.ForeignKey('skills.id'), primary_key=True))

class Skill(db.Model):
    __tablename__ = 'skills'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    jobs = db.relationship('Job', secondary=job_skills, back_populates='skills')

class Job(db.Model):
    __tablename__ = 'jobs'
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False, index=True)
    recruiter_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    title = db.Column(db.String(180), nullable=False, index=True)
    slug = db.Column(db.String(220), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    responsibilities = db.Column(db.Text, default='')
    requirements = db.Column(db.Text, default='')
    education = db.Column(db.String(180), default='')
    benefits = db.Column(db.Text, default='')
    location = db.Column(db.String(120), nullable=False, index=True)
    work_mode = db.Column(db.String(30), default='On-site', index=True)
    job_type = db.Column(db.String(30), default='Full-time', index=True)
    experience_min = db.Column(db.Float, default=0, index=True)
    experience_max = db.Column(db.Float)
    salary_min = db.Column(db.Integer, index=True)
    salary_max = db.Column(db.Integer, index=True)
    industry = db.Column(db.String(120), default='Information Technology', index=True)
    status = db.Column(db.String(30), default='Active', nullable=False, index=True)
    deadline = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_flagged = db.Column(db.Boolean, default=False, nullable=False)
    company = db.relationship('Company', back_populates='jobs')
    recruiter = db.relationship('User', foreign_keys=[recruiter_id])
    skills = db.relationship('Skill', secondary=job_skills, back_populates='jobs')
    saved_by = db.relationship('SavedJob', back_populates='job', cascade='all, delete-orphan')
    applications = db.relationship('Application', back_populates='job', cascade='all, delete-orphan')
    @property
    def is_active_public(self):
        return self.status == 'Active' and (self.deadline is None or self.deadline >= datetime.utcnow()) and not self.is_flagged and bool(self.company) and self.company.approval_status == 'approved'

class SavedJob(db.Model):
    __tablename__ = 'saved_jobs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (db.UniqueConstraint('user_id','job_id', name='uq_saved_job_user_job'),)
    job = db.relationship('Job', back_populates='saved_by')

class JobAlert(db.Model):
    __tablename__ = 'job_alerts'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    keyword = db.Column(db.String(180))
    location = db.Column(db.String(120))
    experience_min = db.Column(db.Float)
    experience_max = db.Column(db.Float)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
