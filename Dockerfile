FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir poetry && \
    pip install --no-cache-dir python-dotenv

COPY pyproject.toml poetry.lock README.md main.py ./

RUN poetry install --no-interaction --no-root


CMD ["python", "main.py"]
