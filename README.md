# Project Access Finland: Survey Analytics Pipeline

End-to-end pipeline that collects university-application plans and outcomes from Project Access Finland students through three Typeform surveys, stores them in SQLite, and serves an aggregate-only analytics dashboard. Built for the 2026 bootcamp cohort, designed to roll forward to any future year with no code changes.

**This repository contains code only.** No student data, names, emails, candidate IDs, databases or secrets are included. The live public dashboard shows group totals only.

## Architecture

Typeform (3 surveys) -> typeform_sync.py -> SQLite -> Flask API -> dashboard (vanilla JS + Chart.js)
SQLite -> publish.py -> static aggregate JSON -> public GitHub Pages site

- **Surveys:** Survey 1 (pre-bootcamp plans), Survey 2 (mid-process changes), Survey 3 (outcomes). Each student gets a personal link carrying a hidden candidate_id field.
- **Ingestion (scripts/typeform_sync.py):** pulls responses via the Typeform Responses API, maps question refs to columns, and stores them per year. Students may resubmit within a window: the latest submission wins and the history is kept. Multi-choice answers are stored with a " | " separator; free-text answers are counted but never charted.
- **Database (SQLite):** table names drive everything. Tracked years have candidate_mapping_YYYY and pre_/mid_/post_bootcamp_YYYY; historical years have bootcampers_YYYY and applications_YYYY. Years, labels and the live/historical split are derived from the tables, never hardcoded. Raw originals are kept in *_raw columns next to cleaned values.
- **Cleaning:** school/city normalisation, university aliases, field categories, and Finnish-to-English translation, all rule-driven (api/utils/translations.py, scripts/normalize_schools.py).
- **API (Flask):** GET /api/multi-year/year/{year}/dashboard, /range/dashboard?start_year=&end_year=, /years/available, /health, plus config. The response format is a fixed contract. Applicants feed only schools and cities; bootcampers feed universities, fields, destinations and acceptance rate.
- **Acceptance rate (api/models/acceptance.py):** computed per wave of students (by expected university start year) as offers / bootcampers, from 2026 onward. A wave counts once its Survey 3 window has closed or all its members have replied. Ranges combine only counted waves and are labelled with their real span. Earlier years show retrospective outcomes only.
- **Survey emailing (scripts/send_surveys.py):** finds every student whose personal send window is open and emails their link. Dry-run by default, --send to send, automatic reminders (every 7 days, max 2), pause switch, opt-out, daily scheduling via Windows Task Scheduler. SMTP credentials come from environment variables.
- **Dashboard:** gold/cream theme, year and range selectors, survey tabs for tracked years, top-N plus "Other" grouping for fields.

## Privacy and anonymity by design

- Student identity is separated from answers: candidate_mapping_* (private) links people to opaque candidate IDs; answer tables hold only the ID.
- The public site is a static export of aggregates (scripts/publish.py): minimum group size of 2, and an automated scan that blocks the push if any email or candidate-ID pattern appears in the output.
- Secrets (Typeform token, admin password, SMTP login) are read only from environment variables.
- The development database and raw CSVs live only on a private machine and are git-ignored.

## Testing

- scripts/e2e_test.py: end-to-end test from simulated Typeform responses to API output.
- scripts/test_acceptance.py: acceptance-rate logic across years and ranges.
- scripts/test_send_surveys.py: send windows, reminders, resubmission, opt-out, pause, next-year pickup.

## Running locally

    pip install flask flask-cors requests
    $env:TYPEFORM_API_TOKEN="..."
    python run_api.py
    python scripts/nocache_server.py

You need your own SQLite database following the table naming above and your own Typeform forms. index.html and survey1.html use https://YOUR-API-HOST as the deployed API placeholder.

## Stack

Python, Flask, SQLite, Typeform API, vanilla JavaScript, Chart.js 3.9, GitHub Pages, Windows Task Scheduler.
