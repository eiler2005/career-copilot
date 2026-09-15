FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# DejaVu provides the Unicode (Cyrillic) glyphs for plan PDF exports.
RUN apt-get update \
    && apt-get install --yes --no-install-recommends fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY src ./src
RUN pip install --no-cache-dir "uv==0.11.6" "hatchling==1.27.0" \
    && uv export --frozen --no-dev --no-emit-project --output-file /tmp/requirements.txt \
    && pip install --no-cache-dir -r /tmp/requirements.txt \
    && pip install --no-cache-dir --no-build-isolation --no-deps . \
    && pip uninstall --yes uv hatchling \
    && rm -f /tmp/requirements.txt \
    && groupadd --gid 10001 dashboard \
    && useradd --uid 10001 --gid dashboard --create-home --shell /usr/sbin/nologin dashboard

USER dashboard:dashboard
EXPOSE 8100
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8100/healthz', timeout=2).read()"
ENTRYPOINT ["ajh-dashboard"]
CMD ["--home", "/data/workspace", "--host", "0.0.0.0", "--port", "8100"]
