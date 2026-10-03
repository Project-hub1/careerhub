from datetime import datetime
from ..extensions import db
class Company(db.Model):
    __tablename__ = 'companies'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(180), unique=True, nullable=False, index=True)
    slug = db.Column(db.String(200), unique=True, nullable=False, index=True)
    industry = db.Column(db.String(120), default='Information Technology')
    location = db.Column(db.String(160), default='India')
    description = db.Column(db.Text, default='')
    website = db.Column(db.String(255), default='')
    employee_count = db.Column(db.Integer, default=50)
    approval_status = db.Column(db.String(30), default='approved', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    recruiters = db.relationship('RecruiterProfile', back_populates='company')
    jobs = db.relationship('Job', back_populates='company')
