from datetime import datetime, timedelta
import os
from urllib.parse import urlparse
from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, url_for, send_from_directory
from flask_login import login_required, current_user
from sqlalchemy import or_
from ..extensions import db
from ..models import RecruiterProfile, Company, Job, Skill, Application, Notification, User

recruiter_bp=Blueprint('recruiter',__name__,url_prefix='/recruiter')

@recruiter_bp.before_request
def guard():
    if not current_user.is_authenticated: return current_app.login_manager.unauthorized()
    if current_user.role!='recruiter': abort(403)

def slugify(text): return ''.join(ch.lower() if ch.isalnum() else '-' for ch in text).strip('-')

def valid_website(value):
    if not value:
        return True
    parsed=urlparse(value)
    return parsed.scheme in {'http','https'} and bool(parsed.netloc)

def profile(): return current_user.recruiter_profile

def owned_job(job_id):
    j=db.session.get(Job,job_id)
    if not j or j.recruiter_id!=current_user.id: abort(404)
    return j

@recruiter_bp.get('/dashboard')
@login_required
def dashboard():
    p=profile(); company=p.company
    jobs=Job.query.filter_by(recruiter_id=current_user.id).order_by(Job.created_at.desc()).all() if company else []
    apps=Application.query.join(Job).filter(Job.recruiter_id==current_user.id).order_by(Application.applied_at.desc()).limit(10).all()
    return render_template('recruiter/dashboard.html',profile=p,company=company,jobs=jobs,applications=apps)

@recruiter_bp.route('/company',methods=['GET','POST'])
@login_required
def company():
    p=profile(); c=p.company
    if request.method=='POST':
        name=request.form.get('name','').strip(); industry=request.form.get('industry','').strip(); location=request.form.get('location','').strip(); website=request.form.get('website','').strip(); description=request.form.get('description','').strip()
        if not name or not industry or not location: flash('Company name, industry and location are required.','error'); return redirect(url_for('recruiter.company'))
        if not valid_website(website): flash('Website must start with http:// or https://.','error'); return redirect(url_for('recruiter.company'))
        duplicate=Company.query.filter(Company.name.ilike(name), Company.id != (c.id if c else 0)).first()
        if duplicate: flash('A company with this name already exists.','error'); return redirect(url_for('recruiter.company'))
        if not c:
            base=slugify(name); slug=base; n=2
            while Company.query.filter_by(slug=slug).first(): slug=f'{base}-{n}'; n+=1
            c=Company(name=name,slug=slug,industry=industry,location=location,website=website,description=description,approval_status='approved'); db.session.add(c); db.session.flush(); p.company_id=c.id
        else:
            c.name=name; c.industry=industry; c.location=location; c.website=website; c.description=description
            # Saving the recruiter-owned company profile makes it live immediately.
            # This also repairs older records that were left in 'pending'.
            c.approval_status='approved'
        db.session.commit(); flash('Company profile saved.','success'); return redirect(url_for('recruiter.company'))
    return render_template('recruiter/company.html',company=c)

@recruiter_bp.route('/jobs/new',methods=['GET','POST'])
@login_required
def new_job():
    p=profile()
    if not p.company: flash('Create your company profile before posting a job.','error'); return redirect(url_for('recruiter.company'))
    if request.method=='POST':
        # A recruiter who is allowed to publish can make the company live immediately.
        # This also repairs older databases where the company was accidentally left pending.
        if p.company.approval_status != 'approved':
            p.company.approval_status = 'approved'
        title=request.form.get('title','').strip(); location=request.form.get('location','').strip(); description=request.form.get('description','').strip()
        if not title or not location or not description: flash('Title, location and description are required.','error'); return redirect(url_for('recruiter.new_job'))
        base=slugify(title); slug=f'{base}-{int(datetime.utcnow().timestamp())}'
        def num(name, default=0):
            raw=request.form.get(name)
            if raw in (None, ''): return default
            try: return float(raw)
            except (ValueError, TypeError): return default
        def money(name):
            try: return int(float(request.form.get(name) or 0)*100000)
            except ValueError: return None
        exp_min=max(0, num('experience_min'))
        exp_max=num('experience_max', None)
        if exp_max is not None and exp_max <= 0: exp_max=None
        if exp_max is not None and exp_max < exp_min: flash('Maximum experience must be greater than or equal to minimum experience.','error'); return redirect(url_for('recruiter.new_job'))
        salary_min=money('salary_min'); salary_max=money('salary_max')
        if salary_min is not None and salary_min < 0: salary_min=None
        if salary_max is not None and salary_max < 0: salary_max=None
        if salary_min is not None and salary_max is not None and salary_max < salary_min: flash('Maximum salary must be greater than or equal to minimum salary.','error'); return redirect(url_for('recruiter.new_job'))
        try: deadline_days=max(1, min(int(request.form.get('deadline_days') or 30), 3650))
        except ValueError: deadline_days=30
        j=Job(company_id=p.company.id,recruiter_id=current_user.id,title=title[:180],slug=slug,description=description,responsibilities=request.form.get('responsibilities',''),requirements=request.form.get('requirements',''),education=request.form.get('education',''),benefits=request.form.get('benefits',''),location=location[:120],work_mode=request.form.get('work_mode','On-site'),job_type=request.form.get('job_type','Full-time'),experience_min=exp_min,experience_max=exp_max,salary_min=salary_min,salary_max=salary_max,industry=p.company.industry,status='Active',deadline=datetime.utcnow()+timedelta(days=deadline_days))
        skill_names=[x.strip() for x in request.form.get('skills','').split(',') if x.strip()]
        j.skills=[Skill.query.filter_by(name=x).first() or Skill(name=x) for x in skill_names]; db.session.add(j)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash('The job could not be published. Please check the details and try again.','error')
            return redirect(url_for('recruiter.new_job'))
        flash('Job published successfully. It is now live on CareerHub.','success')
        return redirect(url_for('recruiter.jobs'))
    return render_template('recruiter/job_form.html',job=None)

@recruiter_bp.route('/jobs/<int:job_id>/edit',methods=['GET','POST'])
@login_required
def edit_job(job_id):
    j=owned_job(job_id)
    if request.method=='POST':
        for field in ['title','description','responsibilities','requirements','education','benefits','location','work_mode','job_type']:
            if field in request.form: setattr(j,field,request.form.get(field,'').strip())
        if request.form.get('status') in {'Active','Paused','Closed'}: j.status=request.form.get('status')
        try: j.experience_min=max(0,float(request.form.get('experience_min') or 0)); j.experience_max=float(request.form.get('experience_max') or 0) or None
        except ValueError: pass
        if j.experience_max is not None and j.experience_max < j.experience_min: flash('Maximum experience must be greater than or equal to minimum experience.','error'); return redirect(url_for('recruiter.edit_job',job_id=j.id))
        try: j.salary_min=int(float(request.form.get('salary_min') or 0)*100000); j.salary_max=int(float(request.form.get('salary_max') or 0)*100000)
        except ValueError: pass
        if j.salary_min is not None and j.salary_max is not None and j.salary_max < j.salary_min: flash('Maximum salary must be greater than or equal to minimum salary.','error'); return redirect(url_for('recruiter.edit_job',job_id=j.id))
        if request.form.get('deadline_days'):
            try: j.deadline=datetime.utcnow()+timedelta(days=int(request.form['deadline_days']))
            except ValueError: pass
        names=[x.strip() for x in request.form.get('skills','').split(',') if x.strip()]; j.skills=[Skill.query.filter_by(name=x).first() or Skill(name=x) for x in names]
        db.session.commit(); flash('Job updated.','success'); return redirect(url_for('recruiter.jobs'))
    return render_template('recruiter/job_form.html',job=j)

@recruiter_bp.get('/jobs')
@login_required
def jobs():
    jobs=Job.query.filter_by(recruiter_id=current_user.id).order_by(Job.created_at.desc()).all(); return render_template('recruiter/jobs.html',jobs=jobs)

@recruiter_bp.post('/jobs/<int:job_id>/status')
@login_required
def job_status(job_id):
    j=owned_job(job_id); status=request.form.get('status','Active')
    if status not in {'Active','Paused','Closed'}: abort(400)
    j.status=status; db.session.commit(); flash(f'Job marked {status}.','success'); return redirect(url_for('recruiter.jobs'))

@recruiter_bp.get('/jobs/<int:job_id>/applications')
@login_required
def applicants(job_id):
    j=owned_job(job_id); apps=Application.query.filter_by(job_id=j.id).order_by(Application.applied_at.desc()).all(); return render_template('recruiter/applicants.html',job=j,applications=apps)


@recruiter_bp.get('/applications/<int:application_id>/resume')
@login_required
def applicant_resume(application_id):
    a=db.session.get(Application,application_id)
    if not a or not a.job or a.job.recruiter_id!=current_user.id or not a.resume_filename: abort(404)
    return send_from_directory(os.path.join(current_app.instance_path,'uploads','resumes'),a.resume_filename,as_attachment=True,download_name=a.resume_filename)

@recruiter_bp.post('/applications/<int:application_id>/status')
@login_required
def application_status(application_id):
    a=db.session.get(Application,application_id)
    if not a or not a.job or a.job.recruiter_id!=current_user.id: abort(404)
    status=request.form.get('status','Applied')
    if status not in {'Applied','Under Review','Shortlisted','Interview','Rejected','Hired'}: abort(400)
    a.status=status; db.session.add(Notification(user_id=a.candidate_id,title='Application update',message=f'Your application for {a.job.title} is now {status}.',link=url_for('candidate.applications'))); db.session.commit(); flash('Application status updated.','success'); return redirect(url_for('recruiter.applicants',job_id=a.job_id))

@recruiter_bp.get('/analytics')
@login_required
def analytics():
    from ..models import JobView
    jobs=Job.query.filter_by(recruiter_id=current_user.id).order_by(Job.created_at.desc()).all()
    rows=[]
    for j in jobs:
        views=JobView.query.filter_by(job_id=j.id).count()
        apps=Application.query.filter_by(job_id=j.id).count()
        shortlisted=Application.query.filter_by(job_id=j.id,status='Shortlisted').count()
        rows.append({'job':j,'views':views,'applications':apps,'shortlisted':shortlisted})
    return render_template('recruiter/analytics.html',rows=rows,total_views=sum(r['views'] for r in rows),total_apps=sum(r['applications'] for r in rows),total_shortlisted=sum(r['shortlisted'] for r in rows))

@recruiter_bp.route('/interviews/<int:application_id>/schedule',methods=['POST'])
@login_required
def schedule_interview(application_id):
    from ..models import Interview
    a=db.session.get(Application,application_id)
    if not a or not a.job or a.job.recruiter_id!=current_user.id: abort(404)
    raw=request.form.get('scheduled_at','').strip()
    try: scheduled=datetime.fromisoformat(raw)
    except ValueError: flash('Please provide a valid interview date and time.','error'); return redirect(url_for('recruiter.applicants',job_id=a.job_id))
    interview=Interview.query.filter_by(application_id=a.id).first()
    if not interview: interview=Interview(application_id=a.id); db.session.add(interview)
    interview.scheduled_at=scheduled; interview.mode=request.form.get('mode','Video').strip(); interview.meeting_link=request.form.get('meeting_link','').strip()[:500]; interview.notes=request.form.get('notes','').strip()[:3000]
    a.status='Interview'
    db.session.add(Notification(user_id=a.candidate_id,title='Interview scheduled',message=f'Interview for {a.job.title} scheduled for {scheduled.strftime("%d %b %Y, %I:%M %p")}.',link=url_for('candidate.interviews')))
    db.session.commit(); flash('Interview scheduled and candidate notified.','success'); return redirect(url_for('recruiter.applicants',job_id=a.job_id))

@recruiter_bp.get('/interviews')
@login_required
def interviews():
    from ..models import Interview
    items=Interview.query.join(Application).join(Job).filter(Job.recruiter_id==current_user.id).order_by(Interview.scheduled_at.asc()).all()
    return render_template('recruiter/interviews.html',interviews=items)

@recruiter_bp.get('/messages')
@login_required
def messages():
    from ..models import Message
    items=Message.query.filter((Message.sender_id==current_user.id)|(Message.receiver_id==current_user.id)).order_by(Message.created_at.desc()).limit(100).all()
    for m in items:
        if m.receiver_id==current_user.id: m.is_read=True
    db.session.commit()
    return render_template('recruiter/messages.html',messages=items)

@recruiter_bp.post('/messages/<int:user_id>')
@login_required
def send_message(user_id):
    from ..models import Message, User
    receiver=db.session.get(User,user_id)
    if not receiver or receiver.id==current_user.id: abort(404)
    body=request.form.get('body','').strip()
    if not body: flash('Message cannot be empty.','error'); return redirect(url_for('recruiter.messages'))
    db.session.add(Message(sender_id=current_user.id,receiver_id=receiver.id,subject=request.form.get('subject','CareerHub message').strip()[:180],body=body[:5000]))
    db.session.add(Notification(user_id=receiver.id,title='New CareerHub message',message=f'You received a message from {current_user.email}.',link=url_for('candidate.messages') if receiver.role=='candidate' else url_for('recruiter.messages')))
    db.session.commit(); flash('Message sent.','success'); return redirect(url_for('recruiter.messages'))
