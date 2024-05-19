FROM postgres:16

ARG PGUSER
ARG PGPASSWORD

ENV POSTGRES_USER=${DB_USER} \
    POSTGRES_DB=${DB_DATABASE} \
    POSTGRES_PASSWORD=${DB_PASSWORD} \
    POSTGRES_HOST_AUTH_METHOD="scram-sha-256\nhost replication all 0.0.0.0/0 scram-sha-256" \
    POSTGRES_INITDB_ARGS="--auth-host=scram-sha-256"

RUN apt-get update && apt-get install -y sed

COPY init.sql /init.sql
RUN sed -i 's/rpUSER/'"$PGUSER"'/g' /init.sql
RUN sed -i 's/rpPASSWORD/'"$PGPASSWORD"'/g' /init.sql
RUN mv /init.sql /docker-entrypoint-initdb.d/init.sql

CMD ["postgres"]
