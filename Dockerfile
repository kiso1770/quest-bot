FROM python:3.11-slim

WORKDIR /app

# Устанавливаем Poetry
RUN pip install poetry==1.8.2

RUN poetry config virtualenvs.create false


COPY pyproject.toml poetry.lock ./


RUN poetry install --only=main --no-interaction --no-ansi

# Копируем остальной код
COPY . .

CMD ["python", "main.py"]