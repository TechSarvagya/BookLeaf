# BookLeaf — Author Support & Communication Portal

A Django REST API and React portal for authors to review their books, sales, and royalties, and for staff to handle support tickets with optional Gemini assistance. The supplied JSON is the source of demo author and book records. No cloud service or payment integration is created by this repository.

## Features

- Author login, book and royalty details, dashboard, general or book-specific tickets, threaded messages, and automatic eight-second ticket polling while the tab is visible.
- Staff dashboard, searchable and paginated queue, status/category/priority/date filters, priority and age sorting, assignment, internal notes, and controlled ticket lifecycle.
- Gemini classification and priority in one request after a ticket has been saved; staff-only AI reply suggestions that must be edited or accepted and sent manually. Failure leaves the ticket available for staff review.
- Server-side role and ownership enforcement, short-lived JWT access tokens, rotating refresh tokens, logout blacklisting, AI throttling, and reply idempotency keys.

## Architecture

```mermaid
flowchart LR
  A[Author browser] --> R[React + TanStack Query]
  S[Staff browser] --> R
  R -->|JWT /api/v1| D[Django REST API]
  D --> P[(PostgreSQL)]
  D -->|explicit AI actions| G[Gemini API]
  D --> K[Local policy knowledge base]
```

The browser never accesses PostgreSQL or Gemini directly. Django apps are grouped by `accounts`, `books`, `tickets`, `ai_services`, and `core`. See [ARCHITECTURE.md](ARCHITECTURE.md) for design decisions and the API contract.

## Local installation (Windows PowerShell)

1. Use Python 3.12+, Node 22+, and a PostgreSQL database. Create a virtual environment at the repository root:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
   npm ci --prefix frontend
   ```

2. Set a random `SECRET_KEY` and keep `BOOKLEAF_DEBUG=True` locally. A blank `DATABASE_URL` uses local SQLite by default; to use PostgreSQL locally, set it to a valid connection string such as `postgres://user:password@localhost:5432/bookleaf`. Deployed mode requires PostgreSQL.
3. Copy `frontend/.env.example` to `frontend/.env`; set `VITE_API_URL=http://localhost:8000/api/v1`.
4. Run migrations and import the unchanged sample dataset:

   ```powershell
   cd backend
   ..\.venv\Scripts\python.exe manage.py migrate
   ..\.venv\Scripts\python.exe manage.py seed_bookleaf_data --file '..\FULLSTACK-SAMPLEDATA (1) (1) (1).json'
   ..\.venv\Scripts\python.exe manage.py runserver
   ```

5. In another terminal run `npm run dev --prefix frontend` and open `http://localhost:5173`.

The seed command upserts the exact external author/book IDs and preserves existing passwords. It imports 10 authors and 18 books, including null publication dates/MRPs, zero sales and royalties, and empty distribution lists. Disposable logins are in [DEMO_ACCOUNTS.md](DEMO_ACCOUNTS.md). The supplied ISBN strings are retained as sample IDs even when they contain `XXXX`.

To remove demo conversations locally, run `manage.py reset_bookleaf_demo --file <dataset path> --confirm`; this deletes tickets/messages/notes for authors named in the dataset and is disabled when `BOOKLEAF_DEBUG=False`. Authors/books remain. A re-seed does not erase conversations.

## Environment variables

| Variable | Purpose |
| --- | --- |
| `SECRET_KEY` | Random Django signing secret; required in deployed mode. |
| `BOOKLEAF_DEBUG` | `True` only for local development; `False` in Render. |
| `DATABASE_URL` | PostgreSQL URL, with `sslmode=require` for Neon. Required in deployed mode. |
| `ALLOWED_HOSTS` | Comma-separated API hostnames, no scheme. |
| `CORS_ALLOWED_ORIGINS` | Exact browser origins, including scheme. |
| `GEMINI_API_KEY` | Optional free-tier API key, never sent to React. |
| `GEMINI_MODEL` | Model identifier; default `gemini-3.5-flash-lite`. |
| `GEMINI_TIMEOUT_MS` | Per-request timeout, default 10000. |
| `VITE_API_URL` | Frontend-only base URL ending in `/api/v1`. |

The frontend keeps JWT tokens in `sessionStorage` and refreshes expired access tokens once per request burst. This avoids persistent login across browser sessions, but JavaScript-readable tokens remain vulnerable to script injection; a production system should use an httpOnly cookie refresh flow and a dedicated CSRF design.

## AI design

Ticket creation returns immediately with `PENDING` AI status. The author UI starts a second authenticated classification request; staff can retry if it fails. Classification and priority share one schema-validated Gemini call. Bad output, quota failure, missing credentials, and timeouts keep the safe `General Inquiry`/`Medium` defaults and retain the ticket. Staff overrides are preserved on retries.

Staff request reply suggestions explicitly. The prompt includes only the relevant [policy section](backend/ai_services/knowledge_base.py), the necessary book figures, and recent conversation context. It treats ticket text as untrusted, forbids unverified action claims, and stores a draft only for staff. The editor loads the suggestion into an editable response; the actual author-facing message is a separate send action. Usage metadata and latency are recorded when available, and AI endpoints are throttled to 10 requests per user per hour.

The configured `gemini-3.5-flash-lite` uses Google's Interactions API and is listed with free input and output tokens on the [official pricing page](https://ai.google.dev/gemini-api/docs/pricing). Free-tier rate limits vary by account and model; check [your current limits](https://ai.google.dev/gemini-api/docs/rate-limits) before the demo. The project never enables paid billing or switches models automatically. Without a key, all manual support features remain available.

## API and tests

- OpenAPI JSON: `http://localhost:8000/api/schema/`
- Swagger UI: `http://localhost:8000/api/docs/`
- Health: `http://localhost:8000/api/v1/health/`
- Backend: `cd backend; ..\.venv\Scripts\python.exe manage.py test`
- Frontend: `npm run test --prefix frontend`
- Production build/typecheck: `npm run build --prefix frontend`

Key API flows: `POST /api/v1/auth/login/`, `POST /api/v1/tickets/`, `POST /api/v1/tickets/{id}/ai/classify/`, `GET /api/v1/admin/tickets/`, `POST /api/v1/admin/tickets/{id}/ai/draft/`, `POST /api/v1/admin/tickets/{id}/reply/`, `POST /api/v1/auth/logout/`. `POST /reply/` accepts an `Idempotency-Key` header. The browser generates one key per send attempt and reuses it for retries.

Manual smoke test: sign in as a seeded author, open My Books, create a royalty ticket, confirm its number, sign in as admin, filter/open the ticket, generate a suggestion, edit and send it, resolve the ticket, then return as author and observe the reply/status update within eight seconds. Automated backend tests exercise the same persisted API boundaries with Gemini mocked.

## ₹0 demo deployment preparation

Deployment requires your approval; this repository only prepares it.

1. Create a Neon Free PostgreSQL project. Copy its connection string into Render's `DATABASE_URL` and ensure `sslmode=require`. Neon listed [1 GB storage and 100 CU-hours per free project](https://neon.com/blog/neon-free-plan-1-gb-per-project) in October 2026; check the dashboard before creating a project.
2. Create a Render Free web service from [render.yaml](render.yaml). Fill in `DATABASE_URL`, `ALLOWED_HOSTS` (for example `bookleaf-api.onrender.com`), and `CORS_ALLOWED_ORIGINS` (the exact Cloudflare Pages URL). Render starts with migration and idempotent demo seeding, then Gunicorn. It has [idle spin-down after 15 minutes and ephemeral local storage](https://render.com/docs/free), so persistent records belong in Neon. Monitor its monthly free-hour/bandwidth limits and do not add a payment method if strict ₹0 is required.
3. Deploy `frontend` as a Cloudflare Pages project: root directory `frontend`, build command `npm run build`, output `dist`, environment `VITE_API_URL=https://<render-host>/api/v1`. Pages provides [default SPA route fallback](https://developers.cloudflare.com/pages/configuration/serving-pages/) and its free plan currently includes [500 builds/month](https://developers.cloudflare.com/pages/platform/limits/).
4. Optionally set a free-tier Gemini key in Render. Verify the chosen model is available for your account. Avoid enabling billing.
5. Verify `/api/v1/health/`, the login, a persisted ticket, a staff reply, and an author polling update after a Render cold start.

All provider quotas can change. No live deployment or paid resource was created or tested here. Local tests use a disposable SQLite database unless you set `DATABASE_URL` to PostgreSQL; run migrations/tests against PostgreSQL before submission if available.

## Limitations and next steps

There is no attachment storage or payment processing integration. Polling provides near-real-time updates while views are active. Render's cold start can briefly delay requests. A production version should add durable background AI jobs, more audit events, SSO/MFA, token cookie handling, observability, and a larger test matrix against live PostgreSQL. Never use the disposable demo credentials for real customer accounts.
