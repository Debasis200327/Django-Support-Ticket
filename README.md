Django-Support-Ticket
# Support Ticket Intake and Triage Module

A Django app (`supportdesk`) for collecting support tickets from trainees.
Built with function-based views, Django Forms, templates, AJAX, cookies and
custom middleware. No database, ORM, DRF, sessions or authentication.

## Problems fixed
| Problem | Fix |
|---|---|
| Form lost input after validation failure | The bound form is passed back to the template, so values and errors are kept |
| Screenshot accepted without checks | Extension, real file signature and 2 MB size are validated |
| AJAX priority checker used GET | Now POST-only (`@require_POST`) with CSRF protection |
| No request tracking | `RequestAuditMiddleware` adds `request.audit_id` and an `X-Request-ID` header |
| Last category must be remembered | `last_ticket_category` cookie (no sessions) |

## Project structure
    ticketproject/
    ├── manage.py
    ├── tickets.jsonl                  # saved tickets (one JSON object per line)
    ├── media/ticket_screenshots/      # uploaded screenshots
    ├── ticketproject/                 # settings.py, urls.py
    └── supportdesk/
        ├── forms.py  views.py  urls.py  middleware.py  tests.py
        ├── templates/supportdesk/ticket_form.html, ticket_success.html
        └── static/supportdesk/ticket.js

## Run steps
1. Create and activate a virtual environment.
2. `pip install django`
3. `python manage.py runserver`
4. Open http://127.0.0.1:8000/
5. Optional: `python manage.py test`

No migrations are needed because no database is used.

## URLs
| URL | Name | Purpose |
|---|---|---|
| `/` | `supportdesk:ticket_create` | Show and submit the form |
| `/success/` | `supportdesk:ticket_success` | Success page with request ID |
| `/priority-check/` | `supportdesk:priority_checker` | AJAX POST, returns JSON |

## Validation rules
- Name: at least 2 characters. Email: valid format.
- Description: at least 20 characters.
- Category and severity: must be from the allowed lists.
- Screenshot (optional): `.png`, `.jpg` or `.jpeg`, real file signature must match, max 2 MB.

## How it works
- **Storage:** a valid ticket is appended to `tickets.jsonl` as one JSON line,
  then the user is redirected with `redirect(reverse(...))`.
- **AJAX:** `ticket.js` sends severity and description with the
  `X-CSRFToken` header. The view returns JSON with `suggested_priority`
  (Low→Low, Medium→Normal, High→High, Critical→Urgent) and keeps a preview in
  the in-memory dictionary `priority_previews`.
- **Cookie:** after a successful submission `last_ticket_category` is set
  (30 days, HttpOnly, SameSite=Lax). On the next GET it pre-selects the category.
- **Middleware:** generates a UUID per request, stores it in `request.audit_id`,
  and shows it in the template footer and the `X-Request-ID` header.
- **Media:** screenshots are saved with `default_storage` under a random UUID
  filename, and served by Django only when `DEBUG=True`.

## Test evidence
Add your browser screenshots in `screenshots/`:
1. `valid_submission.png`: filled form and success page
2. `invalid_form.png`: errors shown with input preserved
3. `ajax_response.png`: "Suggested Priority: Urgent"
4. `jsonl_line.png`: `tickets.jsonl` open in VS Code
5. `cookie.png`: DevTools → Application → Cookies

Results from my test run (curl against the running server):

| Test | Result |
|---|---|
| Valid POST | 302 → `/success/?ref=<id>`, cookie `last_ticket_category=Django` set |
| Bad email + short description | 200, errors shown, name/category/severity kept |
| PDF screenshot | "Only PNG, JPG and JPEG files are allowed." |
| PNG over 2 MB | "Screenshot must not exceed 2 MB." |
| PNG renamed to .jpg | "File content is not a valid JPEG image." |
| Form POST without CSRF token | 403 |
| `GET /priority-check/` | 405 |
| AJAX POST without token | 403 |
| AJAX POST with token (Critical) |
