# Private-test MCP container. Do not expose for public use without OAuth and
# multi-user authorization. Startup fails closed without SIDA_MCP_BEARER_TOKEN.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    SIDA_MCP_MODE=http \
    SIDA_MCP_HOST=0.0.0.0

WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY scripts/ ./scripts/
COPY schemas/ ./schemas/
COPY simulation/ ./simulation/
COPY plugin_runtime/ ./plugin_runtime/
RUN python -m pip install --no-cache-dir ".[plugin]"

USER 10001:10001
EXPOSE 8000

CMD ["python", "-m", "plugin_runtime.server"]
