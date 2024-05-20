CREATE TABLE IF NOT EXISTS Email_add(id SERIAL PRIMARY KEY, EmailAddr VARCHAR(255));
CREATE TABLE IF NOT EXISTS Ph_number(id SERIAL PRIMARY KEY, PhoneNumber VARCHAR(20));

ALTER SYSTEM SET wal_level = replica;
ALTER SYSTEM SET max_wal_senders = 10;
ALTER SYSTEM SET max_replication_slots = 10;
ALTER SYSTEM SET log_replication_commands=on;
ALTER SYSTEM SET hot_standby=on;
ALTER SYSTEM SET hot_standby_feedback=on;
ALTER SYSTEM SET archive_mode = on;
ALTER SYSTEM SET archive_command = 'cp %p /var/lib/postgresql/data/%f';

CREATE USER repl_user WITH REPLICATION ENCRYPTED PASSWORD 'Qq123456';
SELECT pg_create_physical_replication_slot('replication_slot');
