FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN python -m src.data_generation.generate_synthetic_data && python -m src.pipeline.run_all

EXPOSE 8000 8501

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
