FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md LICENSE NOTICE.md ./
COPY src ./src
COPY samples/hosted-agent-fastapi ./samples/hosted-agent-fastapi

RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -e .[fastapi]

EXPOSE 8080

CMD ["python", "samples/hosted-agent-fastapi/app.py"]
