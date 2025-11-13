CREATE DATABASE hospital;

\c hospital

CREATE TABLE IF NOT EXISTS diagnosis (
	id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	name VARCHAR(20) UNIQUE);

CREATE TABLE IF NOT EXISTS wards (
	id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	name VARCHAR(20) UNIQUE,
	max_count INTEGER,
	diagnosis_id INTEGER,
	CONSTRAINT fk_wards_diagnosis FOREIGN KEY (diagnosis_id) REFERENCES diagnosis (id) ON DELETE CASCADE);

CREATE TABLE IF NOT EXISTS people (
	id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	first_name VARCHAR(20),
	last_name VARCHAR(20),
	father_name VARCHAR(20),
	diagnosis_id INTEGER,
	ward_id INTEGER,
	CONSTRAINT fk_people_diagnosis FOREIGN KEY (diagnosis_id) REFERENCES diagnosis (id) ON DELETE CASCADE,
	CONSTRAINT fk_people_wards FOREIGN KEY (ward_id) REFERENCES wards (id) ON DELETE CASCADE);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(60) NOT NULL
);

CREATE OR REPLACE VIEW people_view AS (
    SELECT p.id id,
		   p.first_name first_name, 
		   p.last_name last_name, 
		   p.father_name father_name, 
		   d.name diagnosis, 
		   w.name ward
    FROM people p 
    LEFT JOIN wards w ON w.id = p.ward_id
    LEFT JOIN diagnosis d ON d.id = p.diagnosis_id
    ORDER BY id ASC);

CREATE OR REPLACE VIEW wards_view AS (
    SELECT w.id id, 
		   w.name name, 
		   w.max_count max_count,
		   d.name diagnosis
    FROM wards w 
    LEFT JOIN diagnosis d ON d.id = w.diagnosis_id
    ORDER BY id ASC);

CREATE OR REPLACE VIEW permissions_table AS
SELECT
    table_name,
    has_table_privilege('public.' || table_name, 'SELECT') as can_select,
    has_table_privilege('public.' || table_name, 'INSERT') as can_insert,
    has_table_privilege('public.' || table_name, 'UPDATE') as can_update,
    has_table_privilege('public.' || table_name, 'DELETE') as can_delete
FROM information_schema.tables
WHERE table_schema = 'public'
    AND table_type IN ('BASE TABLE', 'VIEW');


CREATE OR REPLACE VIEW ward_occupancy_report AS
SELECT 
    w.name as ward_name,
    d.name as diagnosis_name,
    w.max_count,
    COUNT(p.id) as current_patients,
    w.max_count - COUNT(p.id) as free_beds,
    ROUND(COUNT(p.id) * 100.0 / w.max_count, 2) as occupancy_percent
FROM wards w
LEFT JOIN people p ON w.id = p.ward_id
LEFT JOIN diagnosis d ON w.diagnosis_id = d.id
GROUP BY w.id, w.name, d.name, w.max_count
ORDER BY occupancy_percent DESC;

CREATE OR REPLACE VIEW diagnosis_statistics AS
WITH tmp AS (
SELECT d.id, SUM(COALESCE(w.max_count ,0)) as max_count
FROM diagnosis d
LEFT JOIN wards w ON w.diagnosis_id = d.id
GROUP BY d.id
)

SELECT 
    d.name as diagnosis_name,
    COUNT(DISTINCT p.id) as patient_count,
    COUNT(DISTINCT w.id) as wards_count,
	t.max_count as total_capacity, 
    t.max_count - COUNT(DISTINCT p.id) as free_beds,
    ROUND(COUNT(DISTINCT p.id) * 100.0 / NULLIF(t.max_count, 0), 2) as occupancy_percent, 
    ROUND(COUNT(DISTINCT p.id) * 100.0 / NULLIF((SELECT COUNT(*) FROM people),0), 2) as percentage_of_total
FROM diagnosis d
LEFT JOIN tmp t ON d.id = t.id
LEFT JOIN people p ON d.id = p.diagnosis_id
LEFT JOIN wards w ON p.ward_id = w.id
GROUP BY d.id, d.name, t.max_count
ORDER BY patient_count DESC;