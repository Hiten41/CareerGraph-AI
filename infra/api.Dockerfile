FROM python:3.12-slim
WORKDIR /srv
COPY apps/api/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r /tmp/requirements.txt
COPY apps/api apps/api
COPY scripts scripts
RUN mkdir -p docs
COPY tests tests
COPY pyproject.toml .
ENV PYTHONPATH=/srv/apps/api
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000"]
