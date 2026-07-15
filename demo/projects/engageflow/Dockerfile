FROM python:3.12-alpine
RUN addgroup -S demo && adduser -S -G demo -u 10001 demo
WORKDIR /app
COPY demo/projects/engageflow/app.py .
USER 10001:10001
EXPOSE 8201
CMD ["python", "app.py"]

