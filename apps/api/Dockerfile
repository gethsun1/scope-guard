FROM python:3.12-slim
RUN groupadd -r scopeguard && useradd -r -g scopeguard -u 10001 scopeguard
WORKDIR /app
COPY pyproject.toml uv.lock* ./
RUN pip install --no-cache-dir uv && uv sync --frozen --no-dev
COPY apps/api ./apps/api
USER 10001:10001
ENV PATH="/app/.venv/bin:$PATH" PYTHONPATH=/app/apps/api
EXPOSE 8000
CMD ["uvicorn", "scope_guard.main:app", "--host", "0.0.0.0", "--port", "8000"]
