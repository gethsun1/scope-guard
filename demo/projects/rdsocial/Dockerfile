FROM python:3.12-alpine
RUN addgroup -S demo && adduser -S -G demo -u 10001 demo
WORKDIR /app
COPY demo/projects/rdsocial/app.py .
USER 10001:10001
EXPOSE 8101
CMD ["python", "app.py"]

