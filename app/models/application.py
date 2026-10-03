from datetime import datetime
from ..extensions import db
class Application(db.Model):
    __tablename__ = 'applications'
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False)
    candidate_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(40), default='Applied', nullable=False, index=True)
    cover_letter = db.Column(db.Text, default='')
    additional_info = db.Column(db.Text, default='')
    resume_filename = db.Column(db.String(255))
    applied_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    job = db.relationship('Job', back_populates='applications')
    candidate = db.relationship('User', foreign_keys=[candidate_id])
    __table_args__ = (db.UniqueConstraint('job_id','candidate_id', name='uq_application_job_candidate'),)
class Interview(db.Model):
    __tablename__ = 'interviews'
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id'), nullable=False)
    scheduled_at = db.Column(db.DateTime)
    mode = db.Column(db.String(40))
    meeting_link = db.Column(db.String(500))
    notes = db.Column(db.Text)
    application = db.relationship('Application')
