FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    UV_PROJECT_ENV=/opt/venv

WORKDIR /app

COPY pyproject.toml README.md uv.lock ./
RUN python -m pip install --no-cache-dir --upgrade pip -i https://mirrors.aliyun.com/pypi/simple/ \
    && python -m pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ uv \
    && uv venv /opt/venv \
    && uv export --frozen --no-dev -o /tmp/requirements.txt \
    && uv pip install --python /opt/venv/bin/python -r /tmp/requirements.txt \
    && uv pip install --python /opt/venv/bin/python . \
    && rm /tmp/requirements.txt

COPY . .

EXPOSE 8001

CMD ["/opt/venv/bin/gunicorn", "-k", "uvicorn.workers.UvicornWorker", "app.core.server:app", "-b", "0.0.0.0:8001", "--workers", "1"]
