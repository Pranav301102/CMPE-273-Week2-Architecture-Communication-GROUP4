FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Default to backlog recovery test, but can be overridden
# Usage: docker compose run --rm tests python run_idempotency_check.py
CMD ["python", "run_all_tests.py"]
