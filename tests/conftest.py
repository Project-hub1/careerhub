import pytest
from app import create_app
from app.extensions import db
from app.models import User, Job, Company
class TestConfig:
    TESTING=True; SECRET_KEY='test'; SQLALCHEMY_DATABASE_URI='sqlite:///:memory:'; SQLALCHEMY_TRACK_MODIFICATIONS=False; WTF_CSRF_ENABLED=False; DEV_SHOW_RESET_LINK=True
@pytest.fixture()
def app():
    app=create_app(TestConfig)
    with app.app_context(): db.create_all(); yield app; db.session.remove(); db.drop_all()
@pytest.fixture()
def client(app): return app.test_client()
@pytest.fixture()
def seed_db(app):
    with app.app_context():
        c=Company(name='Test Co',slug='test-co',industry='IT',location='Delhi',description='Test company'); u=User(email='candidate@test.com',role='candidate'); u.set_password('Password@123'); db.session.add_all([c,u]); db.session.flush(); j=Job(company_id=c.id,title='Python Developer',slug='python-developer-test',description='Python Flask SQL',responsibilities='Build APIs',requirements='Python',education='Diploma',benefits='Leave',location='Delhi',work_mode='Remote',job_type='Full-time',experience_min=0,experience_max=3,salary_min=400000,salary_max=700000,status='Active'); db.session.add(j); db.session.commit(); return u,j
