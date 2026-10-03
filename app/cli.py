import click
from flask import current_app
from werkzeug.security import generate_password_hash
from .extensions import db
from .models import User, JobSeekerProfile, RecruiterProfile

def register_cli(app):
    @app.cli.command('create-admin')
    @click.option('--email', prompt='Admin email')
    @click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True)
    def create_admin(email, password):
        email = email.strip().lower()
        if User.query.filter_by(email=email).first():
            click.echo('A user with that email already exists.')
            return
        u = User(email=email, role='admin', password_hash=generate_password_hash(password))
        db.session.add(u); db.session.commit(); click.echo(f'Admin created: {email}')
