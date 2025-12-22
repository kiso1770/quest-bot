FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir poetry && \
    pip install --no-cache-dir python-dotenv

COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --only main

COPY . .

CMD ["python", "main.py"]
