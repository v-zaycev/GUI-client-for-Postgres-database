
CREATE OR REPLACE FUNCTION insert_into_diagnosis()
RETURNS TRIGGER AS $$
BEGIN
    -- 1. Проверка уникальности имени палаты
    IF EXISTS (SELECT 1 FROM diagnosis WHERE name = NEW.name) THEN
        RAISE EXCEPTION 'Диагноз "%" уже существует', NEW.name;
    END IF;

    -- 2. Проверка размера имени (от 1 до 20 символов)
    IF NEW.name IS NULL OR LENGTH(NEW.name) = 0 THEN
        RAISE EXCEPTION 'Название диагноза не может быть пустым';
    END IF;
    
    IF LENGTH(NEW.name) > 20 THEN
        RAISE EXCEPTION 'Название диагноза не может превышать 20 символов';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER diagnosis_insert_trigger
BEFORE INSERT ON diagnosis
FOR EACH ROW
EXECUTE FUNCTION insert_into_diagnosis();

CREATE OR REPLACE FUNCTION update_diagnosis()
RETURNS TRIGGER AS $$
BEGIN
    -- 1. Проверка уникальности имени палаты (если имя изменилось)
    IF NEW.name != OLD.name AND EXISTS (SELECT 1 FROM wards WHERE name = NEW.name) THEN
        RAISE EXCEPTION 'Диагноз "%" уже существует', NEW.name;
    END IF;

    -- 2. Проверка размера имени (от 1 до 20 символов)
    IF NEW.name IS NULL OR LENGTH(NEW.name) = 0 THEN
        RAISE EXCEPTION 'Название диагноза не может быть пустым';
    END IF;
    
    IF LENGTH(NEW.name) > 20 THEN
        RAISE EXCEPTION 'Название диагноза не может превышать 20 символов';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE TRIGGER diagnosis_update_trigger
BEFORE UPDATE ON diagnosis
FOR EACH ROW
EXECUTE FUNCTION update_diagnosis();