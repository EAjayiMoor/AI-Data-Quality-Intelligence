FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
COPY app ./app
COPY alembic ./alembic
COPY scripts ./scripts
COPY data ./data
COPY docs ./docs
COPY tests ./tests
COPY alembic.ini ./
COPY AGENTS.md ./
COPY README_SETUP.md ./
COPY .streamlit ./.streamlit

RUN pip install --upgrade pip && pip install .

EXPOSE 8000

CMD ["sh", "-c", "streamlit run app/main.py --server.address 0.0.0.0 --server.port ${PORT:-8000}"]
