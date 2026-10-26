# Submission write-up

BookLeaf prioritizes a complete author-to-support workflow: a supplied-data import, isolated author accounts, accurate book and royalty views, ticket persistence, staff review, and visible replies. Django REST Framework owns authorization and business rules; React provides role-specific workflows through the same API. PostgreSQL is the deployment database, while a local SQLite fallback keeps tests easy to run.

The main trade-off is AI execution without paid queue infrastructure. A ticket is committed first; an authenticated second request asks Gemini for category and priority. Failed calls leave safe defaults and allow staff correction. Staff request reply drafts explicitly, review the relevant BookLeaf policy and book facts, edit the text, then send it themselves. The AI key never reaches React; schema validation, timeout, rate limiting, and a selected knowledge-base section keep the feature predictable and economical.

The deployment design uses Cloudflare Pages, Render Free, Neon Free PostgreSQL, and a free-tier Gemini model. It avoids persistent local files, payments, and background workers. A production evolution would add a durable job queue, httpOnly refresh cookies, broader audit logs, monitoring, optional secure attachments, and tests against a real PostgreSQL instance.
