# CareerHub — Full Job Portal (Phases 1–3 + Platform Core)

CareerHub is a Flask + SQLAlchemy job marketplace with separate candidate, recruiter and admin workflows. It is designed to be a real functional application rather than a static UI.

## What is included

### Candidate
- Registration, login, logout, remember-me and password reset
- Professional profile with skills, education and experience
- Resume upload (PDF/DOC/DOCX, max 5 MB)
- Job search with keyword, location, experience, salary, type, work mode, education and date filters
- Relevance/newest/oldest/salary sorting and server-side pagination
- Save/unsave jobs and a dedicated Saved Jobs page
- Job applications with cover letter and application status tracking
- Job alerts and notifications with unread badge

### Recruiter
- Recruiter account and company profile
- Company approval workflow
- Create, edit, pause and close job postings
- Skills, salary, experience, location and work-mode fields
- Applicant management and application status updates
- Candidate resume access limited to the recruiter's own applications

### Admin
- Dashboard statistics
- User activation/deactivation
- Company approval/rejection
- Job flagging/opening/closing
- Audit log records

### Public marketplace
- Search across job title, description, requirements, responsibilities, skills and company name
- Active-job visibility checks including deadline, moderation and company approval
- Company directory and company detail pages
- Similar jobs
- Share/copy job link
- Responsive UI for desktop, tablet and mobile, including a mobile filter drawer
- XSS-safe Jinja rendering and safe external website validation for recruiter company profiles

## Windows setup

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
flask db upgrade
python seed.py
python run.py
```

Or run `setup.bat` once and then `start.bat`.

Open: `http://127.0.0.1:5000`

## Demo accounts

Candidate: `candidate@example.com` / `Candidate@123`

Recruiter: `recruiter@example.com` / `Recruiter@123`

Admin:
```powershell
flask create-admin
```

## Tests

```powershell
python -m pytest -q
```

## Troubleshooting

If an older CareerHub database is being reused, stop the server before running setup again. The development application creates its schema automatically and Flask-Migrate remains available for future schema changes.

If the browser appears to keep loading, check the PowerShell window for the server output. `http://127.0.0.1:5000/login` and `http://127.0.0.1:5000/jobs` are useful quick health checks.

## Validation performed for this package

- Python source compilation: passed.
- Jinja template syntax parsing: passed.
- Template endpoint-reference scan: no missing `url_for` endpoints detected.
- The earlier duplicate `page` keyword pagination bug has been removed.
- Full Flask/pytest execution could not be run in the packaging environment because external Python packages could not be downloaded due to unavailable network/DNS access. Run `python -m pytest -q` locally after installing `requirements.txt`.

## Production notes

Do not use the development `SECRET_KEY` in production. Use PostgreSQL, a strong secret, HTTPS, proper email delivery for password resets, and production WSGI hosting before deployment.
