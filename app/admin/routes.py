from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import login_required, current_user
from ..extensions import db
from ..models import User, Company, Job, Application, AdminLog
admin_bp=Blueprint('admin',__name__,url_prefix='/admin')
@admin_bp.before_request
def guard():
    if not current_user.is_authenticated: return redirect(url_for('auth.login', next=request.full_path))
    if current_user.role!='admin': abort(403)

def log(action): db.session.add(AdminLog(admin_id=current_user.id,action=action)); db.session.commit()
@admin_bp.get('/dashboard')
@login_required
def dashboard():
    stats={'users':User.query.count(),'candidates':User.query.filter_by(role='candidate').count(),'recruiters':User.query.filter_by(role='recruiter').count(),'companies':Company.query.count(),'jobs':Job.query.count(),'applications':Application.query.count()}
    return render_template('admin/dashboard.html',stats=stats)
@admin_bp.get('/users')
@login_required
def users(): return render_template('admin/users.html',users=User.query.order_by(User.created_at.desc()).all())
@admin_bp.post('/users/<int:user_id>/toggle')
@login_required
def toggle_user(user_id):
    u=db.session.get(User,user_id)
    if not u or u.id==current_user.id: abort(400)
    u.is_active=not u.is_active; db.session.commit(); log(f'Toggled user {u.email} to {u.is_active}'); return redirect(url_for('admin.users'))
@admin_bp.get('/companies')
@login_required
def companies(): return render_template('admin/companies.html',companies=Company.query.order_by(Company.created_at.desc()).all())
@admin_bp.post('/companies/<int:company_id>/approval')
@login_required
def company_approval(company_id):
    c=db.session.get(Company,company_id)
    if not c: abort(404)
    status=request.form.get('status','approved')
    if status not in {'pending','approved','rejected'}: abort(400)
    c.approval_status=status; db.session.commit(); log(f'Company {c.name} approval={c.approval_status}'); return redirect(url_for('admin.companies'))
@admin_bp.get('/jobs')
@login_required
def jobs(): return render_template('admin/jobs.html',jobs=Job.query.order_by(Job.created_at.desc()).all())
@admin_bp.post('/jobs/<int:job_id>/moderate')
@login_required
def moderate_job(job_id):
    j=db.session.get(Job,job_id)
    if not j: abort(404)
    action=request.form.get('action','')
    if action=='flag': j.is_flagged=True
    elif action=='unflag': j.is_flagged=False
    elif action=='close': j.status='Closed'
    elif action=='open': j.status='Active'
    else: abort(400)
    db.session.commit(); log(f'Job {j.id} moderation={action}'); return redirect(url_for('admin.jobs'))

@admin_bp.get('/reports')
@login_required
def reports():
    from ..models import JobReport
    reports=JobReport.query.order_by(JobReport.created_at.desc()).all()
    return render_template('admin/reports.html',reports=reports)

@admin_bp.post('/reports/<int:report_id>/status')
@login_required
def report_status(report_id):
    from ..models import JobReport
    r=db.session.get(JobReport,report_id)
    if not r: abort(404)
    status=request.form.get('status','reviewed')
    if status not in {'open','reviewed','resolved','dismissed'}: abort(400)
    r.status=status; db.session.commit(); log(f'Job report {r.id} status={status}'); return redirect(url_for('admin.reports'))
