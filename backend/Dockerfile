FROM python:3.10-slim

WORKDIR /backend

COPY requirements.txt ./
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH=/backend

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
