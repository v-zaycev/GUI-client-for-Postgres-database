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

CREATE ROLE super_role;
REVOKE ALL ON SCHEMA public FROM super_role;
GRANT SELECT, INSERT, DELETE, UPDATE ON people_view, wards_view, diagnosis, users TO super_role;
GRANT SELECT ON permissions_table, ward_occupancy_report, diagnosis_statistics, roles_table TO super_role;

CREATE USER app_user WITH PASSWORD '159753';
GRANT waitroom_role TO app_user;
GRANT basic_role TO app_user;
GRANT advanced_role TO app_user;
GRANT super_role TO app_user;
ALTER USER app_user SET ROLE waitroom_role;
GRANT EXECUTE ON PROCEDURE set_role(VARCHAR(50)) TO app_user;

CREATE OR REPLACE PROCEDURE set_role(username_ VARCHAR(50))
LANGUAGE plpgsql
AS $$
DECLARE 
    user_role_ VARCHAR(20);
BEGIN
    SELECT user_role INTO user_role_
    FROM users 
    WHERE username = username_;
    IF (user_role_ = 'super_role') THEN
        SET ROLE super_role;
    ELSIF (user_role_ = 'advanced_role') THEN
        SET ROLE advanced_role;
    ELSIF (user_role_ = 'basic_role') THEN
        SET ROLE basic_role;
    ELSE
        RAISE EXCEPTION 'unknown login';
    END IF;
END;
$$;