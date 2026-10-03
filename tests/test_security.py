def test_invalid_job_404(client): assert client.get('/jobs/99999').status_code==404
def test_invalid_company_404(client): assert client.get('/companies/99999').status_code==404
def test_safe_next(client,seed_db):
    r=client.post('/login?next=https://evil.example',data={'email':'candidate@test.com','password':'Password@123'}); assert r.status_code==302; assert 'evil.example' not in r.headers['Location']

def test_logged_out_admin_redirects_to_login(client):
    response = client.get('/admin/dashboard')
    assert response.status_code == 302
    assert '/login' in response.headers['Location']
