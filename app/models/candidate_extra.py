from datetime import datetime
from ..extensions import db

class CandidateSkill(db.Model):
    __tablename__ = 'candidate_skills'
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('job_seeker_profiles.id'), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.id'), nullable=False)
    proficiency = db.Column(db.String(30), default='Intermediate', nullable=False)
    years = db.Column(db.Float, default=0)
    skill = db.relationship('Skill')
    profile = db.relationship('JobSeekerProfile', backref=db.backref('skill_profiles', cascade='all, delete-orphan'))
    __table_args__ = (db.UniqueConstraint('profile_id', 'skill_id', name='uq_candidate_skill'),)

class Certification(db.Model):
    __tablename__ = 'certifications'
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('job_seeker_profiles.id'), nullable=False)
    name = db.Column(db.String(180), nullable=False)
    issuer = db.Column(db.String(180), default='')
    issue_year = db.Column(db.Integer)
    credential_url = db.Column(db.String(500), default='')
    profile = db.relationship('JobSeekerProfile', backref=db.backref('certifications', cascade='all, delete-orphan'))

class CandidateProject(db.Model):
    __tablename__ = 'candidate_projects'
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('job_seeker_profiles.id'), nullable=False)
    name = db.Column(db.String(180), nullable=False)
    description = db.Column(db.Text, default='')
    technologies = db.Column(db.String(500), default='')
    project_url = db.Column(db.String(500), default='')
    profile = db.relationship('JobSeekerProfile', backref=db.backref('projects', cascade='all, delete-orphan'))

class CandidateLink(db.Model):
    __tablename__ = 'candidate_links'
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('job_seeker_profiles.id'), nullable=False, unique=True)
    linkedin = db.Column(db.String(500), default='')
    github = db.Column(db.String(500), default='')
    portfolio = db.Column(db.String(500), default='')
    profile = db.relationship('JobSeekerProfile', backref=db.backref('links', uselist=False, cascade='all, delete-orphan'))

class CandidateResume(db.Model):
    __tablename__ = 'candidate_resumes'
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('job_seeker_profiles.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_name = db.Column(db.String(255), nullable=False)
    is_primary = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    profile = db.relationship('JobSeekerProfile', backref=db.backref('resumes', cascade='all, delete-orphan'))

class SearchHistory(db.Model):
    __tablename__ = 'search_history'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    query_string = db.Column(db.String(1000), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    user = db.relationship('User', backref=db.backref('search_history', cascade='all, delete-orphan'))

class SavedCompany(db.Model):
    __tablename__ = 'saved_companies'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    company = db.relationship('Company')
    __table_args__ = (db.UniqueConstraint('user_id', 'company_id', name='uq_saved_company_user'),)

class CandidatePhoto(db.Model):
    __tablename__ = 'candidate_photos'
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('job_seeker_profiles.id'), nullable=False, unique=True)
    filename = db.Column(db.String(255), nullable=False)
    profile = db.relationship('JobSeekerProfile', backref=db.backref('photo', uselist=False, cascade='all, delete-orphan'))
