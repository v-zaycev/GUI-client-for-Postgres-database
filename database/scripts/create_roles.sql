CREATE ROLE waitroom_role;
REVOKE ALL ON SCHEMA public FROM waitroom_role;
GRANT SELECT ON users TO waitroom_role;

CREATE ROLE basic_role;
REVOKE ALL ON SCHEMA public FROM basic_role;
GRANT SELECT ON people_view, wards_view, diagnosis, permissions_table TO basic_role;
GRANT INSERT, UPDATE, DELETE ON people_view TO basic_role;
GRANT SELECT ON permissions_table, ward_occupancy_report, diagnosis_statistics TO basic_role;

CREATE ROLE advanced_role;
REVOKE ALL ON SCHEMA public FROM advanced_role;
GRANT SELECT, INSERT, DELETE, UPDATE ON people_view, wards_view, diagnosis TO advanced_role;
GRANT SELECT ON permissions_table, ward_occupancy_report, diagnosis_statistics TO advanced_role;

CREATE USER app_user WITH PASSWORD '159753';
GRANT waitroom_role TO app_user;
GRANT basic_role TO app_user;
GRANT advanced_role TO app_user;
ALTER USER app_user SET ROLE waitroom_role;

-- CREATE OR REPLACE PROCEDURE set_role(username VARCHAR(50))
-- LANGUAGE plpgsql
-- AS $$
-- BEGIN
--     IF (username = 'advanced_user') THEN
--         SET ROLE advanced_role;
--     ELSIF (username = 'basic_user') THEN
--         SET ROLE basic_role;
--     END IF;
-- END;
-- $$;