def test_home(client): assert client.get('/').status_code==200
def test_register_login(client):
    r=client.post('/register',data={'email':'new@test.com','password':'Password@123','confirm_password':'Password@123','role':'candidate'},follow_redirects=True); assert r.status_code==200
    r=client.post('/login',data={'email':'new@test.com','password':'Password@123'},follow_redirects=True); assert b'Candidate Dashboard' in r.data
def test_role_protection(client,seed_db):
    assert client.get('/candidate/dashboard').status_code==302
    client.post('/login',data={'email':'candidate@test.com','password':'Password@123'}); assert client.get('/admin/dashboard').status_code==403
def test_logout_post_only(client,seed_db):
    client.post('/login',data={'email':'candidate@test.com','password':'Password@123'}); assert client.get('/logout').status_code==405; assert client.post('/logout').status_code==302
