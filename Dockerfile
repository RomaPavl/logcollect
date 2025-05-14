FROM python:3.11-alpine AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt
FROM python:3.11-alpine
RUN addgroup -S app && adduser -S -G app app
WORKDIR /app
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels
COPY . .
RUN mkdir -p instance logs && chown -R app:app instance logs
USER app
EXPOSE 5000
CMD ["python", "logcollect.py"]