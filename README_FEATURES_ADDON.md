# CareerHub — Candidate & Advanced Search Add-on

This build adds only the requested feature areas on top of the existing CareerHub portal:

## Candidate features
- Profile photo
- Rich candidate profile and completion tracking
- Skills with proficiency and years of experience
- Education and experience
- Certifications
- Projects and portfolio links
- LinkedIn, GitHub and portfolio links
- Multiple resumes with primary-resume selection
- Saved jobs and saved companies
- Job alerts and saved searches
- Search history
- Recently viewed jobs
- Profile-based job recommendations
- Application tracking with stage timeline
- Application withdrawal for non-final applications
- Existing cover letter / additional information during applications

## Advanced job search
- Keyword search across job content, skills and company
- Location search
- Company filter
- Skill filter (comma-separated, all requested skills must match)
- Fresher / internship filter
- Job type
- Work mode
- Minimum/maximum experience
- Minimum/maximum salary in LPA
- Education / qualification
- Date posted
- Relevance/newest/oldest/salary sorting
- Combined filters
- Clear filters
- Saved searches preserve all active filters
- Search history
- Server-side pagination preserving filters

## India-wide Job Dataset & Smart Search

The seed data now generates 432 demo jobs across all 36 Indian States/Union Territories, with locations stored as `City, State, India`. This is based on the current Government of India's 28 states + 8 UT listing.

Search behavior:
- `India`, `All India`, or `Pan India` in the location field => all India-wide jobs.
- A state name such as `Maharashtra` => only jobs whose location is in Maharashtra.
- A city such as `Mumbai` => matching city jobs.
- Common state abbreviations such as `MH`, `UP`, `KA`, `TN`, etc. are supported.
- The main keyword box also understands location terms, so `Python India`, `React Maharashtra`, or `Java Delhi` work naturally.
- Search remains compatible with the existing filters, sorting, saved searches, and pagination.
