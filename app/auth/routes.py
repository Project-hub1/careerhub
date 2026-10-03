import hashlib, secrets
from datetime import datetime, timedelta
from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from ..extensions import db
from ..models import User, JobSeekerProfile, RecruiterProfile, PasswordResetToken
from .forms import LoginForm, RegisterForm, ForgotPasswordForm, ResetPasswordForm
from .utils import is_safe_next_url
auth_bp=Blueprint('auth',__name__)

def dashboard_for(user): return {'candidate':'candidate.dashboard','recruiter':'recruiter.dashboard','admin':'admin.dashboard'}[user.role]
@auth_bp.route('/login',methods=['GET','POST'])
def login():
    if current_user.is_authenticated: return redirect(url_for(dashboard_for(current_user)))
    form=LoginForm()
    if form.validate_on_submit():
        u=User.query.filter_by(email=form.email.data.strip().lower()).first()
        if not u or not u.check_password(form.password.data): flash('Invalid email or password.','error')
        elif not u.is_active: flash('Your account is inactive.','error')
        else:
            u.last_login_at=datetime.utcnow(); db.session.commit(); login_user(u,remember=form.remember.data)
            nxt=request.args.get('next'); return redirect(nxt if is_safe_next_url(nxt) else url_for(dashboard_for(u)))
    return render_template('auth/login.html',form=form)
@auth_bp.route('/register',methods=['GET','POST'])
def register():
    if current_user.is_authenticated: return redirect(url_for(dashboard_for(current_user)))
    form=RegisterForm()
    if form.validate_on_submit():
        email=form.email.data.strip().lower()
        if User.query.filter_by(email=email).first(): flash('An account with this email already exists.','error')
        else:
            u=User(email=email,role=form.role.data); u.set_password(form.password.data)
            db.session.add(u); db.session.flush()
            if u.role=='candidate': db.session.add(JobSeekerProfile(user_id=u.id,full_name=''))
            else: db.session.add(RecruiterProfile(user_id=u.id,full_name=''))
            db.session.commit(); flash('Account created. Please log in.','success'); return redirect(url_for('auth.login'))
    return render_template('auth/register.html',form=form)
@auth_bp.post('/logout')
@login_required
def logout(): logout_user(); flash('You have been logged out.','success'); return redirect(url_for('main.home'))
@auth_bp.route('/forgot-password',methods=['GET','POST'])
def forgot_password():
    form=ForgotPasswordForm(); reset_url=None
    if form.validate_on_submit():
        u=User.query.filter_by(email=form.email.data.strip().lower()).first()
        if u:
            PasswordResetToken.query.filter_by(user_id=u.id,used_at=None).update({'used_at':datetime.utcnow()})
            raw=secrets.token_urlsafe(32); token=PasswordResetToken(user_id=u.id,token_hash=hashlib.sha256(raw.encode()).hexdigest(),expires_at=datetime.utcnow()+timedelta(minutes=60)); db.session.add(token); db.session.commit()
            if current_app.config['DEV_SHOW_RESET_LINK']: reset_url=url_for('auth.reset_password',token=raw,_external=True)
        flash('If an account exists for that email, a password reset link has been generated.','success')
    return render_template('auth/forgot_password.html',form=form,reset_url=reset_url)
@auth_bp.route('/reset-password/<token>',methods=['GET','POST'])
def reset_password(token):
    h=hashlib.sha256(token.encode()).hexdigest(); t=PasswordResetToken.query.filter_by(token_hash=h).first()
    if not t or t.used_at or t.expires_at < datetime.utcnow(): flash('This reset link is invalid or expired.','error'); return redirect(url_for('auth.forgot_password'))
    form=ResetPasswordForm()
    if form.validate_on_submit():
        u=db.session.get(User,t.user_id); u.set_password(form.password.data); t.used_at=datetime.utcnow(); db.session.commit(); flash('Password reset successfully.','success'); return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html',form=form)
