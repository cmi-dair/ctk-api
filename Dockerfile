FROM python:3.11-bullseye

EXPOSE 8000

WORKDIR /app

COPY --from=pandoc/minimal:latest /pandoc /usr/bin/pandoc
COPY . .

RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev --no-interaction --no-ansi && \
    rm -rf /root/.cache

CMD ["uvicorn", "ctk_api.main:app", "--host", "0.0.0.0", "--port", "8000", "--app-dir", "src"]
