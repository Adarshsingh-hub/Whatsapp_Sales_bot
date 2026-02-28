FROM python:3.11

WORKDIR /app

ENV PYTHONPATH=/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . . 

RUN mkdir -p /app/data /app/chroma_db

EXPOSE 8000

CMD ["uvicorn", "src.webhook:app","--host", "0.0.0.0","--port", "8000"]