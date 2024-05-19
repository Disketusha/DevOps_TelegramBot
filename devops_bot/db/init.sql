CREATE TABLE IF NOT EXISTS Email_add(id SERIAL PRIMARY KEY, EmailAddr VARCHAR(255));
CREATE TABLE IF NOT EXISTS Ph_number(id SERIAL PRIMARY KEY, PhoneNumber VARCHAR(20));


ALTER SYSTEM SET wal_level = replica;
ALTER SYSTEM SET max_wal_senders = 10;
ALTER SYSTEM SET max_replication_slots = 10;
ALTER SYSTEM SET log_replication_commands=on;
ALTER SYSTEM SET hot_standby=on;
ALTER SYSTEM SET hot_standby_feedback=on;



CREATE USER rpUSER WITH REPLICATION ENCRYPTED PASSWORD 'rpPASSWORD';
SELECT pg_create_physical_replication_slot('replication_slot');


COPY (SELECT 'local all postgres trust' UNION ALL
    SELECT 'host replication repl_user 0.0.0.0/0 md5' UNION ALL
    SELECT 'host all all 0.0.0.0/0 md5') TO '/var/lib/postgresql/data/pg_hba.conf' (FORMAT text);
SELECT pg_reload_conf();
