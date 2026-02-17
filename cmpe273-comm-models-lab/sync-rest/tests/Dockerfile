FROM python:3.11-slim
WORKDIR /tests
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Default to basic latency test, can override with run_all_scenarios.py
# Usage: docker compose run --rm tests python run_all_scenarios.py
CMD ["python", "run_latency_tests.py"]