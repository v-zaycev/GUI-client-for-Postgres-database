TRUNCATE TABLE wards RESTART IDENTITY CASCADE;
TRUNCATE TABLE diagnosis RESTART IDENTITY CASCADE;
TRUNCATE TABLE people RESTART IDENTITY;

COPY diagnosis (name) FROM 'C:\pgsql\resources\diagnosis.txt' DELIMITER ',' ENCODING 'UTF8';
COPY wards (name, max_count, diagnosis_id) FROM 'C:\pgsql\resources\wards.txt' DELIMITER ',' ENCODING 'UTF8';
COPY people (first_name, last_name, father_name, diagnosis_id, ward_id) FROM 'C:\pgsql\resources\people.txt' DELIMITER ',' ENCODING 'UTF8';
