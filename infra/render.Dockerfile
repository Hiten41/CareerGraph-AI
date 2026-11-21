FROM node:24-bookworm-slim AS web
WORKDIR /web
COPY apps/web/package*.json ./
RUN npm ci
COPY apps/web/ ./
ENV API_INTERNAL_URL=http://127.0.0.1:8000
RUN npm run build

FROM python:3.12-slim-bookworm
WORKDIR /srv
RUN apt-get update && apt-get install -y --no-install-recommends libstdc++6 libgomp1 && rm -rf /var/lib/apt/lists/*
COPY --from=web /usr/local/bin/node /usr/local/bin/node
COPY apps/api/requirements.txt /tmp/requirements.txt
RUN sed '/^sentence-transformers/d' /tmp/requirements.txt > /tmp/requirements-render.txt \
    && pip install --no-cache-dir -r /tmp/requirements-render.txt 'onnxruntime>=1.20,<2' 'tokenizers>=0.20,<1' 'numpy>=1.26,<3'
COPY apps/api apps/api
COPY scripts scripts
COPY infra/render-start.sh /usr/local/bin/render-start
COPY --from=web /web/.next/standalone /web
COPY --from=web /web/.next/static /web/.next/static
RUN sed -i 's/\r$//' /usr/local/bin/render-start && chmod 755 /usr/local/bin/render-start \
    && useradd --uid 10001 --create-home careergraph && mkdir -p /srv/docs && chown careergraph /srv/docs

ARG MODEL_REVISION=1110a243fdf4706b3f48f1d95db1a4f5529b4d41
RUN python -c "from pathlib import Path; from urllib.request import urlretrieve; p=Path('/srv/minilm'); p.mkdir(); u='https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/resolve/${MODEL_REVISION}/'; urlretrieve(u+'tokenizer.json',p/'tokenizer.json'); urlretrieve(u+'onnx/model_quint8_avx2.onnx',p/'minilm.onnx')"
ENV PYTHONPATH=/srv/apps/api MINI_LM_ASSETS=/srv/minilm COOKIE_SECURE=true DB_POOL_SIZE=2 DB_MAX_OVERFLOW=1
USER careergraph
CMD ["/usr/local/bin/render-start"]

