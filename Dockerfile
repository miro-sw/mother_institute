# Single-container for both Django (Gunicorn) and Streamlit (for demo/prototype).
# Suitable for small deployments or testing. For production prefer separate services.
FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Install runtime deps
COPY requirements.txt /app/
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev build-essential supervisor curl \
    && pip install --upgrade pip \
    && pip install -r requirements.txt \
    && apt-get remove -y gcc build-essential \
    && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

# Copy project
COPY . /app

# Collect static files
RUN python manage.py collectstatic --noinput || true

# Supervisor config
COPY deploy/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

EXPOSE 8000 8501

CMD ["/usr/bin/supervisord", "-n", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
