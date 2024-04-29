FROM python:3.12-alpine
WORKDIR /usr/src/app

COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip python -m pip install -U pip && \
    pip install -r requirements.txt

COPY . .

ENTRYPOINT ["python", "."]
