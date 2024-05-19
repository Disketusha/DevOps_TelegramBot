FROM postgres:16

ENV PGUSER=${DB_REPL_USER} \
    PGPASSWORD=${DB_REPL_PASSWORD}

CMD ["bash", "-c", "rm -rf /var/lib/postgres/data; mkdir /var/lib/postgres/data; initdb -D /var/lib/postgres/data; until pg_basebackup -v --pgdata=/var/lib/postgresql/data -R --slot=replication_slot --host=db --port=5432; do echo 'Waiting for primary to connect...'; sleep 1s; done; echo 'Backup done, starting replica...'; chmod 0700 /var/lib/postgresql/data; postgres"]
