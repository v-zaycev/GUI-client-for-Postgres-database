COPY diagnosis (name) FROM 'C:\Users\VovaZ\GUI-client-for-Postgres-database\database\resources\diagnosis.txt' DELIMITER ',' ENCODING 'UTF8';
COPY wards (name, max_count, diagnosis_id) FROM 'C:\Users\VovaZ\GUI-client-for-Postgres-database\database\resources\wards.txt' DELIMITER ',' ENCODING 'UTF8';
COPY people (first_name, last_name, father_name, diagnosis_id, ward_id) FROM 'C:\Users\VovaZ\GUI-client-for-Postgres-database\database\resources\people.txt' DELIMITER ',' ENCODING 'UTF8';

INSERT INTO users (username, password_hash, user_role) VALUES ('basic_user', '$2b$12$tmkj48MYoZNnAZbsQ4tc1uyZLY/xwdwNgQq9G5JnlU900XWeSIe6G', 'basic_role');    --qwerty
INSERT INTO users (username, password_hash, user_role) VALUES ('advanced_user', '$2b$12$oIXeR7OnlssIOBuOh9X1kuRGZuuafwE8nTA7jAJwpPp7Eoja4nfG.', 'advanced_role'); --qwerty2
INSERT INTO users (username, password_hash, user_role) VALUES ('super_user', '$2b$12$oIXeR7OnlssIOBuOh9X1kuRGZuuafwE8nTA7jAJwpPp7Eoja4nfG.', 'super_role'); --qwerty2