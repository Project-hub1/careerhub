import os
import uuid
from datetime import datetime
from flask import Blueprint, current_app, flash, redirect, render_template, request, send_from_directory, url_for, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from ..extensions import db
from ..models import Company
from ..models import SavedJob, Application, JobSeekerProfile, Education, Experience, JobAlert, Job, Notification, Skill, CandidateSkill, JobView, Certification, CandidateProject, CandidateLink, CandidateResume, SearchHistory, SavedCompany

candidate_bp=Blueprint('candidate',__name__,url_prefix='/candidate')

def candidate_only():
    return current_user.is_authenticated and current_user.role == 'candidate'

@candidate_bp.before_request
def guard():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login', next=request.full_path))
    if current_user.role != 'candidate': abort(403)

@candidate_bp.get('/dashboard')
@login_required
def dashboard():
    profile=current_user.candidate_profile
    applications=Application.query.filter_by(candidate_id=current_user.id).order_by(Application.updated_at.desc(),Application.applied_at.desc()).limit(8).all()
    saved_count=SavedJob.query.filter_by(user_id=current_user.id).count()
    resume_count=CandidateResume.query.filter_by(profile_id=profile.id).count()
    skill_count=CandidateSkill.query.filter_by(profile_id=profile.id).count()
    profile_completion=0
    checks=[bool(profile.full_name),bool(profile.headline),bool(profile.location),bool(profile.summary),bool(profile.skills_text),bool(profile.preferred_role),bool(profile.resume_filename or resume_count),bool(profile.education),bool(profile.experience),bool(skill_count),bool(profile.certifications),bool(profile.projects)]
    profile_completion=round(sum(checks)/len(checks)*100)
    terms=set((profile.preferred_role or '').lower().replace(',',' ').split()) | set((profile.skills_text or '').lower().replace(',',' ').split())
    recommended=Job.query.filter(Job.status=='Active',Job.is_flagged.is_(False),Job.company.has(Company.approval_status=='approved')).order_by(Job.created_at.desc()).limit(30).all()
    if terms:
        scored=[]
        for job in recommended:
            text=' '.join([job.title,job.description,job.requirements,' '.join(x.name for x in job.skills)]).lower()
            score=sum(1 for t in terms if len(t)>2 and t in text)
            scored.append((score,job.created_at,job))
        recommended=[x[2] for x in sorted(scored,key=lambda x:(x[0],x[1]),reverse=True)[:6]]
    else:
        recommended=recommended[:6]
    recent_views=JobView.query.filter_by(viewer_id=current_user.id).order_by(JobView.viewed_at.desc()).limit(6).all()
    return render_template('candidate/dashboard.html',profile=profile,applications=applications,saved_count=saved_count,profile_completion=profile_completion,recommended=recommended,recent_views=recent_views,resume_count=resume_count,skill_count=skill_count)

@candidate_bp.route('/profile', methods=['GET','POST'])
@login_required
def profile():
    p=current_user.candidate_profile
    if p.resume_filename and not CandidateResume.query.filter_by(profile_id=p.id).first():
        db.session.add(CandidateResume(profile_id=p.id,filename=p.resume_filename,original_name=p.resume_original_name or p.resume_filename,is_primary=True))
        db.session.commit()
    if request.method=='POST':
        p.full_name=request.form.get('full_name','').strip()[:120]
        p.headline=request.form.get('headline','').strip()[:180]
        p.location=request.form.get('location','').strip()[:120]
        p.phone=request.form.get('phone','').strip()[:30]
        p.summary=request.form.get('summary','').strip()
        p.skills_text=request.form.get('skills_text','').strip()[:2000]
        p.preferred_role=request.form.get('preferred_role','').strip()[:180]
        try:
            salary_lpa=float(request.form.get('expected_salary') or 0)
            p.expected_salary=int(salary_lpa*100000) if salary_lpa > 0 else None
        except ValueError:
            p.expected_salary=None
        db.session.commit(); flash('Profile updated successfully.','success'); return redirect(url_for('candidate.profile'))
    return render_template('candidate/profile.html',profile=p)

@candidate_bp.post('/photo')
@login_required
def upload_photo():
    f=request.files.get('photo')
    if not f or not f.filename: flash('Please choose a profile photo.','error'); return redirect(url_for('candidate.profile'))
    ext=f.filename.rsplit('.',1)[-1].lower() if '.' in f.filename else ''
    if ext not in {'jpg','jpeg','png','webp'}: flash('Use JPG, PNG or WEBP for your profile photo.','error'); return redirect(url_for('candidate.profile'))
    folder=os.path.join(current_app.instance_path,'uploads','profiles'); os.makedirs(folder,exist_ok=True)
    stored=f'{current_user.id}_{uuid.uuid4().hex}.{ext}'; f.save(os.path.join(folder,stored))
    item=current_user.candidate_profile.photo
    if item:
        old=os.path.join(folder,item.filename)
        if os.path.exists(old): os.remove(old)
        item.filename=stored
    else: db.session.add(CandidatePhoto(profile_id=current_user.candidate_profile.id,filename=stored))
    db.session.commit(); flash('Profile photo updated.','success'); return redirect(url_for('candidate.profile'))

@candidate_bp.post('/resume')
@login_required
def upload_resume():
    p=current_user.candidate_profile; f=request.files.get('resume')
    if not f or not f.filename: flash('Please choose a resume PDF/DOC/DOCX.','error'); return redirect(url_for('candidate.profile'))
    allowed={'pdf','doc','docx'}; ext=f.filename.rsplit('.',1)[-1].lower() if '.' in f.filename else ''
    if ext not in allowed: flash('Only PDF, DOC and DOCX files are allowed.','error'); return redirect(url_for('candidate.profile'))
    folder=os.path.join(current_app.instance_path,'uploads','resumes'); os.makedirs(folder,exist_ok=True)
    stored=f'{current_user.id}_{uuid.uuid4().hex}.{ext}'; f.save(os.path.join(folder,stored))
    original=secure_filename(f.filename)
    CandidateResume.query.filter_by(profile_id=p.id).update({CandidateResume.is_primary: False})
    db.session.add(CandidateResume(profile_id=p.id,filename=stored,original_name=original,is_primary=True))
    p.resume_filename=stored; p.resume_original_name=original; db.session.commit(); flash('Resume uploaded and set as your primary resume.','success'); return redirect(url_for('candidate.profile'))

@candidate_bp.get('/photo')
@login_required
def photo():
    item=current_user.candidate_profile.photo
    if not item: abort(404)
    return send_from_directory(os.path.join(current_app.instance_path,'uploads','profiles'),item.filename)

@candidate_bp.get('/resume')
@login_required
def resume():
    p=current_user.candidate_profile
    if not p.resume_filename: abort(404)
    return send_from_directory(os.path.join(current_app.instance_path,'uploads','resumes'),p.resume_filename,as_attachment=True,download_name=p.resume_original_name or p.resume_filename)

@candidate_bp.route('/education/add', methods=['POST'])
@login_required
def add_education():
    p=current_user.candidate_profile
    degree=request.form.get('degree','').strip(); institution=request.form.get('institution','').strip()
    if not degree or not institution: flash('Degree and institution are required.','error'); return redirect(url_for('candidate.profile'))
    year=request.form.get('year'); db.session.add(Education(profile_id=p.id,degree=degree[:160],institution=institution[:200],year=int(year) if year and year.isdigit() else None)); db.session.commit(); flash('Education added.','success'); return redirect(url_for('candidate.profile'))

@candidate_bp.post('/education/<int:item_id>/delete')
@login_required
def delete_education(item_id):
    item=db.session.get(Education,item_id)
    if item and item.profile_id==current_user.candidate_profile.id: db.session.delete(item); db.session.commit()
    return redirect(url_for('candidate.profile'))

@candidate_bp.post('/experience/add')
@login_required
def add_experience():
    p=current_user.candidate_profile; title=request.form.get('title','').strip(); company=request.form.get('company','').strip()
    if not title or not company: flash('Role and company are required.','error'); return redirect(url_for('candidate.profile'))
    try: years=float(request.form.get('years') or 0)
    except ValueError: years=0
    years=max(0, min(years, 60))
    db.session.add(Experience(profile_id=p.id,title=title[:160],company=company[:200],years=years)); db.session.commit(); flash('Experience added.','success'); return redirect(url_for('candidate.profile'))

@candidate_bp.post('/experience/<int:item_id>/delete')
@login_required
def delete_experience(item_id):
    item=db.session.get(Experience,item_id)
    if item and item.profile_id==current_user.candidate_profile.id: db.session.delete(item); db.session.commit()
    return redirect(url_for('candidate.profile'))

@candidate_bp.post('/companies/<int:company_id>/save')
@login_required
def save_company(company_id):
    company=db.session.get(Company,company_id)
    if not company or company.approval_status!='approved': abort(404)
    item=SavedCompany.query.filter_by(user_id=current_user.id,company_id=company_id).first()
    if item: db.session.delete(item); message='Company removed from saved list.'
    else: db.session.add(SavedCompany(user_id=current_user.id,company_id=company_id)); message='Company saved.'
    db.session.commit(); flash(message,'success'); return redirect(url_for('jobs.company_detail',company_id=company_id))

@candidate_bp.get('/saved-companies')
@login_required
def saved_companies():
    saved=SavedCompany.query.filter_by(user_id=current_user.id).order_by(SavedCompany.created_at.desc()).all()
    return render_template('candidate/saved_companies.html',saved=saved)

@candidate_bp.get('/saved')
@login_required
def saved_jobs():
    saved = SavedJob.query.filter_by(user_id=current_user.id).order_by(SavedJob.created_at.desc()).all()
    active_saved = [item for item in saved if item.job.is_active_public]
    return render_template('candidate/saved.html', saved=active_saved)


@candidate_bp.post('/applications/<int:application_id>/withdraw')
@login_required
def withdraw_application(application_id):
    item=db.session.get(Application,application_id)
    if not item or item.candidate_id!=current_user.id: abort(404)
    if item.status in {'Hired','Rejected','Withdrawn'}:
        flash('This application can no longer be withdrawn.','error')
    else:
        item.status='Withdrawn'; db.session.commit(); flash('Application withdrawn.','success')
    return redirect(url_for('candidate.applications'))

@candidate_bp.route('/applications')
@login_required
def applications():
    status=request.args.get('status','').strip(); q=Application.query.filter_by(candidate_id=current_user.id)
    if status: q=q.filter_by(status=status)
    apps=q.order_by(Application.applied_at.desc()).all(); return render_template('candidate/applications.html',applications=apps,status=status)

@candidate_bp.route('/apply/<int:job_id>', methods=['GET','POST'])
@login_required
def apply(job_id):
    job=db.session.get(Job,job_id)
    if not job or not job.is_active_public: abort(404)
    existing=Application.query.filter_by(job_id=job.id,candidate_id=current_user.id).first()
    if existing: flash('You have already applied to this job.','error'); return redirect(url_for('candidate.applications'))
    p=current_user.candidate_profile
    if request.method=='POST':
        cover=request.form.get('cover_letter','').strip(); info=request.form.get('additional_info','').strip()
        if not p.resume_filename: flash('Upload a resume before applying.','error'); return redirect(url_for('candidate.profile'))
        app=Application(job_id=job.id,candidate_id=current_user.id,status='Applied',cover_letter=cover,additional_info=info,resume_filename=p.resume_filename)
        db.session.add(app)
        db.session.flush()
        if job.recruiter_id:
            db.session.add(Notification(user_id=job.recruiter_id,title='New job application',message=f'{current_user.email} applied for {job.title}.',link=url_for('recruiter.applicants',job_id=job.id)))
        db.session.commit(); flash('Application submitted successfully.','success'); return redirect(url_for('candidate.applications'))
    return render_template('candidate/apply.html',job=job,profile=p)


@candidate_bp.route('/notifications')
@login_required
def notifications():
    items=Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(50).all()
    unread=Notification.query.filter_by(user_id=current_user.id,is_read=False).all()
    for item in unread: item.is_read=True
    db.session.commit()
    return render_template('candidate/notifications.html',notifications=items)

@candidate_bp.post('/saved/<int:job_id>/remove')
@login_required
def remove_saved(job_id):
    item=SavedJob.query.filter_by(user_id=current_user.id,job_id=job_id).first()
    if item: db.session.delete(item); db.session.commit()
    return redirect(url_for('candidate.saved_jobs'))

@candidate_bp.route('/alerts', methods=['GET','POST'])
@login_required
def alerts():
    if request.method=='POST':
        db.session.add(JobAlert(user_id=current_user.id,keyword=request.form.get('keyword','').strip(),location=request.form.get('location','').strip(),is_active=True)); db.session.commit(); flash('Job alert created.','success')
        return redirect(url_for('candidate.alerts'))
    alerts=JobAlert.query.filter_by(user_id=current_user.id).order_by(JobAlert.created_at.desc()).all(); return render_template('candidate/alerts.html',alerts=alerts)

@candidate_bp.post('/alerts/<int:alert_id>/delete')
@login_required
def delete_alert(alert_id):
    a=db.session.get(JobAlert,alert_id)
    if a and a.user_id==current_user.id: db.session.delete(a); db.session.commit()
    return redirect(url_for('candidate.alerts'))

@candidate_bp.get('/saved-searches')
@login_required
def saved_searches():
    import json, urllib.parse
    searches=current_user.saved_searches
    items=[]
    for item in searches:
        try: params=json.loads(item.filters_json or '{}')
        except (TypeError, ValueError): params={}
        query=urllib.parse.urlencode([(k,v) for k,v in params.items() if v not in ('',None)])
        items.append((item,query))
    return render_template('candidate/saved_searches.html', searches=items)

@candidate_bp.post('/saved-searches/<int:search_id>/delete')
@login_required
def delete_saved_search(search_id):
    item=db.session.get(__import__('app.models',fromlist=['SavedSearch']).SavedSearch,search_id)
    if item and item.user_id==current_user.id:
        db.session.delete(item); db.session.commit()
    return redirect(url_for('candidate.saved_searches'))

@candidate_bp.get('/messages')
@login_required
def messages():
    from ..models import Message
    items=Message.query.filter((Message.sender_id==current_user.id)|(Message.receiver_id==current_user.id)).order_by(Message.created_at.desc()).limit(100).all()
    for m in items:
        if m.receiver_id==current_user.id: m.is_read=True
    db.session.commit()
    return render_template('candidate/messages.html',messages=items)

@candidate_bp.post('/messages/<int:user_id>')
@login_required
def send_message(user_id):
    from ..models import Message, User
    receiver=db.session.get(User,user_id)
    if not receiver or receiver.id==current_user.id: abort(404)
    body=request.form.get('body','').strip()
    if not body: flash('Message cannot be empty.','error'); return redirect(url_for('candidate.messages'))
    db.session.add(Message(sender_id=current_user.id,receiver_id=receiver.id,subject=request.form.get('subject','CareerHub message').strip()[:180],body=body[:5000]))
    db.session.add(__import__('app.models',fromlist=['Notification']).Notification(user_id=receiver.id,title='New CareerHub message',message=f'You received a message from {current_user.email}.',link=url_for('recruiter.messages') if receiver.role=='recruiter' else url_for('candidate.messages')))
    db.session.commit(); flash('Message sent.','success'); return redirect(url_for('candidate.messages'))

@candidate_bp.get('/interviews')
@login_required
def interviews():
    from ..models import Interview
    items=Interview.query.join(Application).filter(Application.candidate_id==current_user.id).order_by(Interview.scheduled_at.asc()).all()
    return render_template('candidate/interviews.html',interviews=items)

@candidate_bp.post('/companies/<int:company_id>/review')
@login_required
def review_company_profile(company_id):
    from ..models import CompanyReview, Company
    company=db.session.get(Company,company_id)
    if not company: abort(404)
    rating=request.form.get('rating',type=int) or 0
    if rating not in range(1,6): flash('Rating must be 1 to 5.','error'); return redirect(url_for('jobs.company_detail',company_id=company_id))
    existing=CompanyReview.query.filter_by(company_id=company_id,user_id=current_user.id).first()
    if existing:
        existing.rating=rating; existing.title=request.form.get('title','').strip()[:160]; existing.body=request.form.get('body','').strip()[:3000]
    else:
        db.session.add(CompanyReview(company_id=company_id,user_id=current_user.id,rating=rating,title=request.form.get('title','').strip()[:160],body=request.form.get('body','').strip()[:3000]))
    db.session.commit(); flash('Company review saved.','success'); return redirect(url_for('jobs.company_detail',company_id=company_id))


@candidate_bp.post('/skills/add')
@login_required
def add_skill():
    name=request.form.get('skill','').strip()
    proficiency=request.form.get('proficiency','Intermediate').strip()
    try: years=max(0,min(float(request.form.get('years') or 0),60))
    except ValueError: years=0
    skill=Skill.query.filter(Skill.name.ilike(name)).first()
    if not skill and name:
        skill=Skill(name=name[:100]); db.session.add(skill); db.session.flush()
    if not skill: flash('Skill is required.','error'); return redirect(url_for('candidate.profile'))
    existing=CandidateSkill.query.filter_by(profile_id=current_user.candidate_profile.id,skill_id=skill.id).first()
    if existing: existing.proficiency=proficiency; existing.years=years
    else: db.session.add(CandidateSkill(profile_id=current_user.candidate_profile.id,skill_id=skill.id,proficiency=proficiency,years=years))
    db.session.commit(); flash('Skill added.','success'); return redirect(url_for('candidate.profile'))

@candidate_bp.post('/skills/<int:item_id>/delete')
@login_required
def delete_skill(item_id):
    item=db.session.get(CandidateSkill,item_id)
    if item and item.profile_id==current_user.candidate_profile.id: db.session.delete(item); db.session.commit()
    return redirect(url_for('candidate.profile'))

@candidate_bp.post('/certifications/add')
@login_required
def add_certification():
    name=request.form.get('name','').strip(); issuer=request.form.get('issuer','').strip(); url=request.form.get('credential_url','').strip()
    if not name: flash('Certification name is required.','error'); return redirect(url_for('candidate.profile'))
    year=request.form.get('issue_year'); db.session.add(Certification(profile_id=current_user.candidate_profile.id,name=name[:180],issuer=issuer[:180],issue_year=int(year) if year and year.isdigit() else None,credential_url=url[:500])); db.session.commit(); flash('Certification added.','success'); return redirect(url_for('candidate.profile'))

@candidate_bp.post('/certifications/<int:item_id>/delete')
@login_required
def delete_certification(item_id):
    item=db.session.get(Certification,item_id)
    if item and item.profile_id==current_user.candidate_profile.id: db.session.delete(item); db.session.commit()
    return redirect(url_for('candidate.profile'))

@candidate_bp.post('/projects/add')
@login_required
def add_project():
    name=request.form.get('name','').strip(); desc=request.form.get('description','').strip(); tech=request.form.get('technologies','').strip(); url=request.form.get('project_url','').strip()
    if not name: flash('Project name is required.','error'); return redirect(url_for('candidate.profile'))
    db.session.add(CandidateProject(profile_id=current_user.candidate_profile.id,name=name[:180],description=desc[:3000],technologies=tech[:500],project_url=url[:500])); db.session.commit(); flash('Project added.','success'); return redirect(url_for('candidate.profile'))

@candidate_bp.post('/projects/<int:item_id>/delete')
@login_required
def delete_project(item_id):
    item=db.session.get(CandidateProject,item_id)
    if item and item.profile_id==current_user.candidate_profile.id: db.session.delete(item); db.session.commit()
    return redirect(url_for('candidate.profile'))

@candidate_bp.post('/links')
@login_required
def save_links():
    p=current_user.candidate_profile; links=p.links or CandidateLink(profile_id=p.id)
    links.linkedin=request.form.get('linkedin','').strip()[:500]; links.github=request.form.get('github','').strip()[:500]; links.portfolio=request.form.get('portfolio','').strip()[:500]
    if not p.links: db.session.add(links)
    db.session.commit(); flash('Professional links saved.','success'); return redirect(url_for('candidate.profile'))

@candidate_bp.get('/resumes')
@login_required
def resumes():
    return render_template('candidate/resumes.html',resumes=CandidateResume.query.filter_by(profile_id=current_user.candidate_profile.id).order_by(CandidateResume.created_at.desc()).all())

@candidate_bp.get('/resumes/<int:resume_id>/download')
@login_required
def download_resume(resume_id):
    item=db.session.get(CandidateResume,resume_id)
    if not item or item.profile_id!=current_user.candidate_profile.id: abort(404)
    return send_from_directory(os.path.join(current_app.instance_path,'uploads','resumes'),item.filename,as_attachment=True,download_name=item.original_name)

@candidate_bp.post('/resumes/<int:resume_id>/primary')
@login_required
def primary_resume(resume_id):
    p=current_user.candidate_profile; item=db.session.get(CandidateResume,resume_id)
    if item and item.profile_id==p.id:
        CandidateResume.query.filter_by(profile_id=p.id).update({CandidateResume.is_primary:False}); item.is_primary=True; p.resume_filename=item.filename; p.resume_original_name=item.original_name; db.session.commit(); flash('Primary resume updated.','success')
    return redirect(url_for('candidate.resumes'))

@candidate_bp.post('/resumes/<int:resume_id>/delete')
@login_required
def delete_resume(resume_id):
    p=current_user.candidate_profile; item=db.session.get(CandidateResume,resume_id)
    if item and item.profile_id==p.id:
        if item.is_primary and CandidateResume.query.filter_by(profile_id=p.id).count() > 1: flash('Set another resume as primary before deleting this one.','error'); return redirect(url_for('candidate.resumes'))
        path=os.path.join(current_app.instance_path,'uploads','resumes',item.filename)
        if os.path.exists(path): os.remove(path)
        db.session.delete(item)
        if p.resume_filename==item.filename: p.resume_filename=None; p.resume_original_name=None
        db.session.commit(); flash('Resume removed.','success')
    return redirect(url_for('candidate.resumes'))

@candidate_bp.get('/search-history')
@login_required
def search_history():
    return render_template('candidate/search_history.html',history=SearchHistory.query.filter_by(user_id=current_user.id).order_by(SearchHistory.created_at.desc()).limit(50).all())

@candidate_bp.post('/search-history/clear')
@login_required
def clear_search_history():
    SearchHistory.query.filter_by(user_id=current_user.id).delete(); db.session.commit(); flash('Search history cleared.','success'); return redirect(url_for('candidate.search_history'))
