from flask import Blueprint, render_template
from sqlalchemy import or_
from ..models import Job, Company, User
from ..extensions import db
from datetime import datetime

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    active_jobs = Job.query.filter(
        Job.status == 'Active',
        Job.is_flagged.is_(False),
        Job.company.has(Company.approval_status == 'approved'),
        or_(Job.deadline.is_(None), Job.deadline >= datetime.utcnow())
    )
    featured_jobs = active_jobs.order_by(Job.created_at.desc()).limit(6).all()
    return render_template(
        'home.html',
        job_count=active_jobs.count(),
        company_count=Company.query.filter_by(approval_status='approved').count(),
        candidate_count=User.query.filter_by(role='candidate', is_active=True).count(),
        featured_jobs=featured_jobs
    )
