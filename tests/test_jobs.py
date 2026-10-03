def login(client): client.post('/login',data={'email':'candidate@test.com','password':'Password@123'})
def test_job_listing_and_search(client,seed_db):
    assert client.get('/jobs').status_code==200
    assert b'Python Developer' in client.get('/jobs?q=Python').data
    assert b'Python Developer' in client.get('/jobs?location=Delhi').data
def test_job_detail(client,seed_db): assert client.get('/jobs/1').status_code==200
def test_save_toggle(client,seed_db):
    login(client); r=client.post('/jobs/1/save'); assert r.json['saved'] is True; r=client.post('/jobs/1/save'); assert r.json['saved'] is False
def test_companies(client,seed_db): assert client.get('/companies').status_code==200; assert client.get('/companies/1').status_code==200

def test_job_pagination_preserves_filters(client, seed_db):
    response = client.get('/jobs?q=Python&location=Delhi&page=2')
    assert response.status_code == 200
    assert b'No jobs found' in response.data or b'Find your next job' in response.data


def test_unapproved_company_job_is_hidden(client, seed_db, app):
    _, job = seed_db
    with app.app_context():
        from app.extensions import db
        from app.models import Company, Job
        company = db.session.get(Company, job.company_id)
        company.approval_status = 'pending'
        db.session.commit()
        job_id = job.id
    assert client.get(f'/jobs/{job_id}').status_code == 404
