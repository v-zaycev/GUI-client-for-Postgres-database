COPY diagnosis (name) FROM 'C:\pgsql\resources\diagnosis.txt' DELIMITER ',' ENCODING 'UTF8';
COPY wards (name, max_count, diagnosis_id) FROM 'C:\pgsql\resources\wards.txt' DELIMITER ',' ENCODING 'UTF8';
COPY people (first_name, last_name, father_name, diagnosis_id, ward_id) FROM 'C:\pgsql\resources\people.txt' DELIMITER ',' ENCODING 'UTF8';

INSERT INTO users (username, password_hash) VALUES ('basic_user', '$2b$12$tmkj48MYoZNnAZbsQ4tc1uyZLY/xwdwNgQq9G5JnlU900XWeSIe6G');    --qwerty
INSERT INTO users (username, password_hash) VALUES ('advanced_user', '$2b$12$oIXeR7OnlssIOBuOh9X1kuRGZuuafwE8nTA7jAJwpPp7Eoja4nfG.'); --qwerty2