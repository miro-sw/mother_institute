This document shows three deployment options: (A) Streamlit Cloud + Render (recommended split), (B) single Docker image that runs both services (prototype), and (C) quick local smoke test.

A — Streamlit Cloud (frontend) + Render (Django API)
1. Push your repo to GitHub.
2. Streamlit Cloud (frontend):
   - Create a new app on https://share.streamlit.io and point it to the repo and `streamlit_app.py`.
   - In Streamlit app settings add a secret: `API_URL` → `https://<your-django-host>/institute/api/info/`.
   - Deploy (Streamlit will install requirements from `requirements.txt`).
3. Render (Django API):
   - Create a new Web Service on Render (or Railway). Choose Python environment or Docker.
   - If using Render's Python service: set the start command to `gunicorn mother_institute.wsgi:application --bind 0.0.0.0:$PORT`.
   - Set env vars in the service dashboard: `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=False`, `DJANGO_ALLOWED_HOSTS=yourdomain.com`.
   - Add build command: `pip install -r requirements.txt` and post-deploy: `python manage.py migrate`.
4. Confirm: Streamlit UI calls the public Django API. Monitor logs on both platforms.

B — Single Docker image (both services in one container) — good for demos
1. Build locally: `docker build -t mother_institute:latest .`
2. Run: `docker run -e DJANGO_SECRET_KEY=change-me -p 8000:8000 -p 8501:8501 mother_institute:latest`
3. The container serves Django on :8000 and Streamlit on :8501.
4. To deploy a single container to Render (or any container host): push image to a registry and create a service that uses that image.

C — Quick local smoke test (no Docker)
1. Create a venv and install deps: `python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt`
2. Run Django: `set DJANGO_DEBUG=False; set DJANGO_SECRET_KEY=dev; python manage.py migrate; python manage.py runserver 8000`
3. Run Streamlit: `streamlit run streamlit_app.py --server.port 8501`
4. Visit http://localhost:8501 and verify the app shows API JSON.

Troubleshooting
- CORS errors: add the origin to `CORS_ALLOWED_ORIGINS` or set `CORS_ALLOWED_ORIGIN_REGEXES`.
- 500 errors with DEBUG=False: check the server logs; use `python manage.py check --deploy`.
- Static 404s: ensure `python manage.py collectstatic` ran and STATICFILES_STORAGE is configured.

Security notes
- Do NOT commit secrets. Set `DJANGO_SECRET_KEY` and DB credentials in the host's secret store.
- For production, use a managed DB (Postgres), HTTPS, and separate frontend/backend services.
