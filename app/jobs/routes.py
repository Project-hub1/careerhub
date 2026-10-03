from datetime import datetime, timedelta
from flask import Blueprint, jsonify, render_template, request, url_for, abort
from flask_login import current_user, login_required
from sqlalchemy import or_, and_, func, case
from ..extensions import db
from ..models import Job, Company, Skill, SavedJob, Application, JobView, JobReport, SavedSearch, CompanyReview, SearchHistory, SavedCompany

jobs_bp=Blueprint('jobs',__name__)

def active_query():
    return Job.query.filter(Job.status=='Active', Job.is_flagged.is_(False), Job.company.has(Company.approval_status=='approved'), or_(Job.deadline.is_(None), Job.deadline >= datetime.utcnow()))

def parse_float(name):
    try: return float(request.args.get(name)) if request.args.get(name) else None
    except ValueError: return None

def job_search_query():
    q=active_query(); keyword=request.args.get('q','').strip(); location=request.args.get('location','').strip()
    if keyword:
        # Smart keyword search: every meaningful word can match title, company, skills,
        # description or location. This makes queries such as "Python India" and
        # "React Maharashtra" work naturally without requiring separate filters.
        tokens=[t for t in keyword.split() if len(t) > 1]
        q=q.outerjoin(Job.company).outerjoin(Job.skills)
        for token in tokens or [keyword]:
            like=f'%{token}%'
            q=q.filter(or_(Job.title.ilike(like), Job.description.ilike(like),
                           Job.requirements.ilike(like), Job.responsibilities.ilike(like),
                           Job.location.ilike(like), Company.name.ilike(like), Skill.name.ilike(like)))
        q=q.distinct()
    if location:
        loc = ' '.join(location.split()).strip()
        loc_key = loc.casefold()
        # 'India' means the complete India-wide marketplace. A state means only that state.
        aliases = {
            'up':'Uttar Pradesh', 'uttar pradesh':'Uttar Pradesh',
            'mp':'Madhya Pradesh', 'madhya pradesh':'Madhya Pradesh',
            'wb':'West Bengal', 'west bengal':'West Bengal',
            'hp':'Himachal Pradesh', 'himachal pradesh':'Himachal Pradesh',
            'jk':'Jammu and Kashmir', 'j&k':'Jammu and Kashmir', 'jammu kashmir':'Jammu and Kashmir',
            'tn':'Tamil Nadu', 'tamil nadu':'Tamil Nadu', 'ka':'Karnataka',
            'kl':'Kerala', 'mh':'Maharashtra', 'rj':'Rajasthan', 'gj':'Gujarat',
            'hr':'Haryana', 'pb':'Punjab', 'br':'Bihar', 'jh':'Jharkhand',
            'od':'Odisha', 'or':'Odisha', 'tg':'Telangana', 'ts':'Telangana',
            'ap':'Andhra Pradesh', 'uk':'Uttarakhand', 'uttarakhand':'Uttarakhand',
            'ga':'Goa', 'as':'Assam', 'sikkim':'Sikkim', 'tripura':'Tripura',
            'manipur':'Manipur', 'meghalaya':'Meghalaya', 'mizoram':'Mizoram',
            'nagaland':'Nagaland', 'arunachal':'Arunachal Pradesh',
            'arunachal pradesh':'Arunachal Pradesh', 'chhattisgarh':'Chhattisgarh',
            'delhi':'Delhi', 'ncr':'Delhi', 'chandigarh':'Chandigarh',
            'ladakh':'Ladakh', 'puducherry':'Puducherry', 'pondicherry':'Puducherry',
            'andaman':'Andaman and Nicobar Islands',
            'andaman and nicobar islands':'Andaman and Nicobar Islands',
            'lakshadweep':'Lakshadweep',
            'dadra nagar haveli':'Dadra and Nagar Haveli and Daman and Diu',
            'dadra and nagar haveli and daman and diu':'Dadra and Nagar Haveli and Daman and Diu',
            'india':'India', 'pan india':'India', 'all india':'India'
        }
        canonical = aliases.get(loc_key, loc)
        if canonical.casefold() == 'india':
            q = q.filter(Job.location.ilike('%India%'))
        elif canonical in aliases.values() and canonical.casefold() != 'india':
            q = q.filter(Job.location.ilike(f'%, {canonical}, India%'))
        else:
            q = q.filter(Job.location.ilike(f'%{loc}%'))
    company=request.args.get('company','').strip()
    if company: q=q.filter(Job.company.has(Company.name.ilike(f'%{company}%')))
    # Keep the original single experience selector for compatibility, and add a min/max range.
    exp=parse_float('experience')
    if exp is not None: q=q.filter(Job.experience_min <= exp, or_(Job.experience_max.is_(None),Job.experience_max >= exp))
    exp_min=parse_float('experience_min'); exp_max=parse_float('experience_max')
    if exp_min is not None: q=q.filter(or_(Job.experience_max.is_(None),Job.experience_max >= exp_min))
    if exp_max is not None: q=q.filter(Job.experience_min <= exp_max)
    min_salary=parse_float('salary_min'); max_salary=parse_float('salary_max')
    if min_salary is not None: q=q.filter(or_(Job.salary_max.is_(None),Job.salary_max >= min_salary*100000))
    if max_salary is not None: q=q.filter(or_(Job.salary_min.is_(None),Job.salary_min <= max_salary*100000))
    for field in ['job_type','work_mode']:
        value=request.args.get(field,'').strip()
        if value: q=q.filter(getattr(Job,field)==value)
    education=request.args.get('education','').strip()
    if education: q=q.filter(Job.education.ilike(f'%{education}%'))
    skill_filter=request.args.get('skills','').strip()
    if skill_filter:
        requested=[x.strip() for x in skill_filter.split(',') if x.strip()]
        for skill_name in requested:
            q=q.filter(Job.skills.any(Skill.name.ilike(skill_name)))
    level=request.args.get('level','').strip().lower()
    if level=='fresher': q=q.filter(Job.experience_min <= 0)
    elif level=='internship': q=q.filter(Job.job_type=='Internship')
    posted=request.args.get('date_posted','')
    if posted in {'1','7','30','90'}: q=q.filter(Job.created_at >= datetime.utcnow()-timedelta(days=int(posted)))
    return q, keyword

def sort_jobs(q, sort, keyword):
    if sort=='oldest': return q.order_by(Job.created_at.asc())
    if sort=='salary_high': return q.order_by(Job.salary_max.desc().nullslast(), Job.created_at.desc())
    if sort=='salary_low': return q.order_by(Job.salary_min.asc().nullslast(), Job.created_at.desc())
    if sort=='relevance' and keyword:
        like=f'%{keyword}%'; score=case((Job.title.ilike(like),5),else_=0)+case((Job.description.ilike(like),2),else_=0)+case((Job.requirements.ilike(like),1),else_=0)
        return q.order_by(score.desc(),Job.created_at.desc())
    return q.order_by(Job.created_at.desc())

@jobs_bp.get('/jobs')
def listing():
    q,keyword=job_search_query(); q=sort_jobs(q,request.args.get('sort','relevance'),keyword)
    page=max(request.args.get('page',1,type=int),1); pagination=q.paginate(page=page,per_page=20,error_out=False)
    if current_user.is_authenticated and current_user.role=='candidate' and request.args and any(v for k,v in request.args.items() if k != 'page'):
        query_string=request.query_string.decode('utf-8')[:1000]
        last=SearchHistory.query.filter_by(user_id=current_user.id).order_by(SearchHistory.created_at.desc()).first()
        if not last or last.query_string != query_string:
            db.session.add(SearchHistory(user_id=current_user.id,query_string=query_string))
            db.session.commit()
    saved_ids=set()
    if current_user.is_authenticated and current_user.role=='candidate': saved_ids={x.job_id for x in SavedJob.query.filter_by(user_id=current_user.id).all()}
    return render_template('jobs/list.html',jobs=pagination.items,pagination=pagination,saved_ids=saved_ids,query=request.args)

@jobs_bp.get('/jobs/<int:job_id>')
def detail(job_id):
    job=Job.query.get_or_404(job_id)
    if not job.is_active_public: abort(404)
    # Count a genuine page view. Recruiters use this for lightweight analytics.
    viewer_id=current_user.id if current_user.is_authenticated else None
    db.session.add(JobView(job_id=job.id, viewer_id=viewer_id)); db.session.commit()
    similar=active_query().filter(Job.id!=job.id).filter(or_(Job.location==job.location,Job.industry==job.industry)).order_by(Job.created_at.desc()).limit(6).all()
    saved=False; already_applied=False
    if current_user.is_authenticated and current_user.role=='candidate':
        saved=SavedJob.query.filter_by(user_id=current_user.id,job_id=job.id).first() is not None
        from ..models import Application
        already_applied=Application.query.filter_by(candidate_id=current_user.id,job_id=job.id).first() is not None
    reviews=CompanyReview.query.filter_by(company_id=job.company_id).order_by(CompanyReview.created_at.desc()).limit(8).all()
    avg=(sum(r.rating for r in reviews)/len(reviews)) if reviews else 0
    return render_template('jobs/detail.html',job=job,similar=similar,saved=saved,already_applied=already_applied,reviews=reviews,review_avg=avg)

@jobs_bp.post('/jobs/<int:job_id>/save')
@login_required
def save_job(job_id):
    if current_user.role!='candidate': return jsonify(ok=False,message='Only candidates can save jobs.'),403
    job=Job.query.get_or_404(job_id)
    if not job.is_active_public: return jsonify(ok=False,message='This job is no longer active.'),404
    saved=SavedJob.query.filter_by(user_id=current_user.id,job_id=job.id).first()
    if saved: db.session.delete(saved); state=False
    else: db.session.add(SavedJob(user_id=current_user.id,job_id=job.id)); state=True
    db.session.commit(); return jsonify(ok=True,saved=state)

@jobs_bp.get('/companies')
def companies():
    q=request.args.get('q','').strip(); query=Company.query.filter_by(approval_status='approved')
    if q: query=query.filter(or_(Company.name.ilike(f'%{q}%'),Company.industry.ilike(f'%{q}%'),Company.location.ilike(f'%{q}%')))
    pagination=query.order_by(Company.name.asc()).paginate(page=max(request.args.get('page',1,type=int),1),per_page=12,error_out=False)
    open_job_counts={c.id: Job.query.filter(Job.company_id==c.id, Job.status=='Active', Job.is_flagged.is_(False), or_(Job.deadline.is_(None), Job.deadline >= datetime.utcnow())).count() for c in pagination.items}
    return render_template('companies/list.html',companies=pagination.items,pagination=pagination,query=request.args,open_job_counts=open_job_counts)

@jobs_bp.get('/companies/<int:company_id>')
def company_detail(company_id):
    company=Company.query.get_or_404(company_id)
    if company.approval_status!='approved': abort(404)
    jobs=active_query().filter(Job.company_id==company.id).order_by(Job.created_at.desc()).all()
    saved_company=False
    if current_user.is_authenticated and current_user.role=='candidate':
        saved_company=SavedCompany.query.filter_by(user_id=current_user.id,company_id=company.id).first() is not None
    return render_template('companies/detail.html',company=company,jobs=jobs,saved_company=saved_company)


@jobs_bp.post('/jobs/<int:job_id>/report')
@login_required
def report_job(job_id):
    if current_user.role != 'candidate': return jsonify(ok=False, message='Only candidates can report jobs.'), 403
    job=Job.query.get_or_404(job_id)
    reason=request.form.get('reason','Other').strip()
    if reason not in {'Fake job','Spam','Incorrect information','Scam','Other'}: reason='Other'
    db.session.add(JobReport(job_id=job.id, reporter_id=current_user.id, reason=reason, details=request.form.get('details','').strip()[:2000]))
    db.session.commit()
    return jsonify(ok=True,message='Thanks. The job has been reported to the CareerHub moderation team.')

@jobs_bp.post('/jobs/<int:job_id>/review')
@login_required
def review_company(job_id):
    if current_user.role != 'candidate': abort(403)
    job=Job.query.get_or_404(job_id)
    applied=Application.query.filter_by(job_id=job.id,candidate_id=current_user.id).first()
    if not applied: return jsonify(ok=False,message='Apply to the job before reviewing the company.'), 400
    rating=request.form.get('rating',type=int) or 0
    if rating not in range(1,6): return jsonify(ok=False,message='Rating must be between 1 and 5.'),400
    existing=CompanyReview.query.filter_by(company_id=job.company_id,user_id=current_user.id).first()
    if existing:
        existing.rating=rating; existing.title=request.form.get('title','').strip()[:160]; existing.body=request.form.get('body','').strip()[:3000]
    else:
        db.session.add(CompanyReview(company_id=job.company_id,user_id=current_user.id,rating=rating,title=request.form.get('title','').strip()[:160],body=request.form.get('body','').strip()[:3000]))
    db.session.commit(); return jsonify(ok=True,message='Company review saved.')

@jobs_bp.post('/saved-searches')
@login_required
def save_search():
    if current_user.role!='candidate': abort(403)
    import json
    name=request.form.get('name','My job search').strip()[:120]
    filters={k:v for k,v in request.form.items() if k not in {'name','csrf_token'}}
    db.session.add(SavedSearch(user_id=current_user.id,name=name,query=request.form.get('q','').strip(),location=request.form.get('location','').strip(),filters_json=json.dumps(filters)))
    db.session.commit(); return jsonify(ok=True,message='Search saved.')
