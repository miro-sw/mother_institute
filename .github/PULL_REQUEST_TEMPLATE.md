## Summary

This PR adds:
- Streamlit prototype frontend (`streamlit_app.py`)
- Minimal DRF endpoint and CORS config (`institute/api.py`, `settings.py`)
- Docker + supervisord + docker-compose for a demo single-container run
- CI workflows: `ci.yml` (checks) and `docker-publish.yml` (build/publish)
- Deployment instructions in `DEPLOYMENT.md`

## How to test
1. Run the CI locally (see README). Or run the included smoke commands:
   - `python -m venv .venv; . \.venv\Scripts\Activate.ps1; pip install -r requirements.txt`
   - `python manage.py migrate; python manage.py runserver 8000`
   - `streamlit run streamlit_app.py --server.port 8501`
2. Visit Streamlit UI → it should call `/institute/api/info/` and show JSON.

## Deployment
- Recommended: Streamlit Cloud (frontend) + Render (Django API). See `DEPLOYMENT.md` for exact steps.

## Notes / security
- Remember to set `DJANGO_SECRET_KEY` and DB credentials in the host's secret store.
- This PR leaves DEBUG off by default for deployed environments via env vars.
