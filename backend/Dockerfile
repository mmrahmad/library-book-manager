FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV LIBRARY_DB=/data/library.db
EXPOSE 5001
CMD ["sh", "-c", "python seed.py && gunicorn -b 0.0.0.0:5001 app:app"]
