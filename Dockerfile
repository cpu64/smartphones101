FROM cpu64/python3.13_postgresql

RUN apt-get update && \
    apt-get install -y \
    postgresql-15-cron \
    && rm -rf /var/lib/apt/lists/*

RUN echo "shared_preload_libraries = 'pg_cron'" >> /usr/share/postgresql/15/postgresql.conf.sample
RUN echo "cron.database_name = 'smartphonesioi'" >> /usr/share/postgresql/15/postgresql.conf.sample

WORKDIR /app

COPY ./app/requirements.txt .

RUN MAKEFLAGS="-j$(nproc)" pip install --prefer-binary --no-cache-dir --break-system-packages --root-user-action ignore -r ./requirements.txt

COPY ./app/ .

ENV PGDATABASE=smartphonesioi \
    PGUSER=postgres \
    PGPASSWORD=secure \
    PGHOST=localhost \
    PGPORT=5432 \
    FALSK_HOST=0.0.0.0 \
    FALSK_PORT=5000

CMD [ "python", "app.py"]
