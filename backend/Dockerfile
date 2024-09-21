FROM python:3.10-slim

WORKDIR /backend

COPY requirements.txt ./
COPY . .

RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    libreoffice \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

RUN pip install --upgrade pip

ENV PYTHONPATH=/backend

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
