from pathlib import Path
p=Path('/mnt/data/careerhub_work/build_latest/seed.py')
s=p.read_text()
start=s.index('JOBS=[')
end=s.index('\n\ndef seed():', start)
roles=[
('Python Developer','Full-time','Hybrid',1,4,500000,950000,['Python','Flask','SQL','Git']),
('Java Developer','Full-time','Hybrid',1,4,550000,1000000,['Java','SQL','Git']),
('Frontend Developer','Full-time','Hybrid',0,3,450000,850000,['HTML','CSS','JavaScript','React']),
('React Developer','Full-time','Remote',1,4,600000,1100000,['React','JavaScript','HTML','CSS']),
('Data Analyst','Full-time','Hybrid',1,4,500000,950000,['Excel','SQL','Power BI']),
('Software Engineer','Full-time','On-site',1,4,550000,1000000,['Java','Python','Git','SQL']),
('QA Engineer','Full-time','Hybrid',1,3,450000,800000,['Java','SQL','Git']),
('DevOps Engineer','Full-time','Hybrid',2,6,800000,1600000,['Docker','AWS','Git','Python']),
('Business Analyst','Full-time','Hybrid',1,5,600000,1100000,['Excel','SQL','Power BI']),
('UI/UX Designer','Full-time','Hybrid',1,4,450000,900000,['Figma','HTML','CSS']),
('Technical Support Engineer','Full-time','On-site',0,3,350000,700000,['SQL','JavaScript','Git']),
('Digital Marketing Executive','Full-time','On-site',0,3,300000,650000,['Excel','HTML']),
]
states=[
('Andhra Pradesh','Visakhapatnam'),('Arunachal Pradesh','Itanagar'),('Assam','Guwahati'),('Bihar','Patna'),('Chhattisgarh','Raipur'),('Goa','Panaji'),('Gujarat','Ahmedabad'),('Haryana','Gurugram'),('Himachal Pradesh','Shimla'),('Jharkhand','Ranchi'),('Karnataka','Bengaluru'),('Kerala','Kochi'),('Madhya Pradesh','Indore'),('Maharashtra','Mumbai'),('Manipur','Imphal'),('Meghalaya','Shillong'),('Mizoram','Aizawl'),('Nagaland','Kohima'),('Odisha','Bhubaneswar'),('Punjab','Chandigarh'),('Rajasthan','Jaipur'),('Sikkim','Gangtok'),('Tamil Nadu','Chennai'),('Telangana','Hyderabad'),('Tripura','Agartala'),('Uttar Pradesh','Noida'),('Uttarakhand','Dehradun'),('West Bengal','Kolkata'),('Delhi','New Delhi'),('Jammu and Kashmir','Srinagar'),('Ladakh','Leh'),('Puducherry','Puducherry'),('Chandigarh','Chandigarh'),('Andaman and Nicobar Islands','Port Blair'),('Dadra and Nagar Haveli and Daman and Diu','Silvassa'),('Lakshadweep','Kavaratti')]
rows=[]
idx=1
for state,city in states:
    for title,jtype,mode,emin,emax,smin,smax,skills in roles:
        # vary a few work modes/types while keeping realistic defaults
        jt='Internship' if title=='Digital Marketing Executive' and idx%7==0 else jtype
        wm='Remote' if idx%9==0 else mode
        rows.append((f'{title} — {city}',f'{city}, {state}, India',jt,wm,emin,emax,smin,smax,skills))
        idx+=1
# 36 states/UTs x 12 roles = 432 jobs
block='JOBS='+repr(rows)+'\n'
s=s[:start]+block+s[end:]
# append helpers before seed
marker='\ndef seed():'
helper=r'''

CITY_STATE = {
    'Bengaluru':'Karnataka','Noida':'Uttar Pradesh','Gurugram':'Haryana','Mumbai':'Maharashtra','Pune':'Maharashtra','Hyderabad':'Telangana','Chennai':'Tamil Nadu','Ahmedabad':'Gujarat','Jaipur':'Rajasthan','Kolkata':'West Bengal','Delhi':'Delhi','New Delhi':'Delhi','Lucknow':'Uttar Pradesh','Remote':'India'
}

def normalize_existing_job_locations():
    """Make legacy seeded/demo jobs searchable with the same City, State, India format."""
    for job in Job.query.all():
        loc=(job.location or '').strip()
        if not loc: continue
        if 'india' in loc.lower(): continue
        city=loc.split(',')[0].strip()
        state=CITY_STATE.get(city)
        if state:
            job.location=f'{city}, {state}, India'
        else:
            job.location=f'{loc}, India'
'''
s=s.replace(marker,helper+marker)
s=s.replace("        db.create_all()\n", "        db.create_all()\n        normalize_existing_job_locations()\n",1)
p.write_text(s)
print('seed updated', len(rows))
