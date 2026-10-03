from datetime import datetime
from ..extensions import db

class SavedSearch(db.Model):
    __tablename__ = 'saved_searches'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    query = db.Column(db.String(180), default='')
    location = db.Column(db.String(120), default='')
    filters_json = db.Column(db.Text, default='{}')
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    user = db.relationship('User', backref=db.backref('saved_searches', cascade='all, delete-orphan'))

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject = db.Column(db.String(180), default='CareerHub message')
    body = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    sender = db.relationship('User', foreign_keys=[sender_id])
    receiver = db.relationship('User', foreign_keys=[receiver_id])

class CompanyReview(db.Model):
    __tablename__ = 'company_reviews'
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(160), default='')
    body = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    company = db.relationship('Company', backref=db.backref('reviews', cascade='all, delete-orphan'))
    user = db.relationship('User', foreign_keys=[user_id])
    __table_args__ = (db.UniqueConstraint('company_id', 'user_id', name='uq_company_review_user'),)

class JobReport(db.Model):
    __tablename__ = 'job_reports'
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False)
    reporter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reason = db.Column(db.String(80), nullable=False)
    details = db.Column(db.Text, default='')
    status = db.Column(db.String(30), default='open', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    job = db.relationship('Job', backref=db.backref('reports', cascade='all, delete-orphan'))
    reporter = db.relationship('User', foreign_keys=[reporter_id])

class JobView(db.Model):
    __tablename__ = 'job_views'
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False)
    viewer_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    viewed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    job = db.relationship('Job', backref=db.backref('views', cascade='all, delete-orphan'))
