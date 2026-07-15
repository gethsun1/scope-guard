FROM python:3.12-alpine
RUN addgroup -S demo && adduser -S -G demo -u 10001 demo
WORKDIR /runner
COPY demo/scripts/runner.py .
USER 10001:10001
EXPOSE 9000
CMD ["python", "runner.py"]

