CREATE OR REPLACE PROCEDURE redistribute_patients(
    p_old_ward_id INTEGER,
    p_old_ward_name TEXT,
    p_old_ward_max_count INTEGER
) AS $$
DECLARE
    patient_record RECORD;
    ward_record RECORD;
    current_ward_id INT;
    current_ward_count INT := 0;
    current_ward_max INT;
    
    ward_diag INT;
    in_ward INT;
    with_diagnosis INT;
    diagnosis_max_all_wards INT;
BEGIN
    SELECT diagnosis_id INTO ward_diag
    FROM people
    WHERE ward_id = p_old_ward_id
    LIMIT 1;

    SELECT COUNT(*) INTO in_ward
    FROM people
    WHERE ward_id = p_old_ward_id;

    SELECT COUNT(*) INTO with_diagnosis
    FROM people
    WHERE diagnosis_id = ward_diag;

    SELECT SUM(max_count) INTO diagnosis_max_all_wards
    FROM wards
    WHERE diagnosis_id = ward_diag;

    IF (in_ward > 0 AND with_diagnosis > diagnosis_max_all_wards - p_old_ward_max_count) THEN
        RAISE EXCEPTION 'Невозможно удалить палату. Недостаточно мест для перераспределения пациентов.';
    END IF;

    CREATE TEMP TABLE available_wards AS
    SELECT 
        p.ward_id as id, 
        w.max_count as max_count, 
        COUNT(*) as current_count
    FROM people p
    LEFT JOIN wards w ON p.ward_id = w.id
    WHERE p.ward_id != p_old_ward_id 
      AND p.diagnosis_id = ward_diag
    GROUP BY p.ward_id, w.max_count;

    FOR patient_record IN (
        SELECT *
        FROM people 
        WHERE ward_id = p_old_ward_id
    ) LOOP
        current_ward_id := NULL;
        
        FOR ward_record IN SELECT * FROM available_wards LOOP
            IF (ward_record.current_count < ward_record.max_count) THEN 
                current_ward_id := ward_record.id;
                current_ward_max := ward_record.max_count;
                current_ward_count = ward_record.current_count
                EXIT;
            END IF;
        END LOOP;

        IF current_ward_id IS NULL THEN
            RAISE EXCEPTION 'No available wards for patient redistribution';
        END IF;

        -- Перемещаем пациента
        UPDATE people 
        SET ward_id = current_ward_id
        WHERE id = patient_record.id;

        -- Обновляем счетчик в временной таблице
        UPDATE available_wards 
        SET current_count = current_ward_count + 1
        WHERE id = current_ward_id;

        -- Удаляем заполненную палату из доступных
        IF (current_ward_count + 1) >= current_ward_max THEN
            DELETE FROM available_wards WHERE id = current_ward_id;
        END IF;
    END LOOP;

    DROP TABLE available_wards;
    
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION delete_from_wards_view()
RETURNS TRIGGER AS $$
BEGIN
    CALL redistribute_patients(OLD.id, OLD.name, OLD.max_count);
    DELETE FROM wards WHERE id = OLD.id;
    RETURN OLD;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE TRIGGER wards_view_delete_trigger
INSTEAD OF DELETE ON wards_view
FOR EACH ROW
EXECUTE FUNCTION delete_from_wards_view();

CREATE OR REPLACE FUNCTION insert_into_wards_view()
RETURNS TRIGGER AS $$
DECLARE
    diagnosis_exists BOOLEAN;
    diagnosis_id_val INTEGER;
BEGIN
    -- 1. Проверка уникальности имени палаты
    IF EXISTS (SELECT 1 FROM wards WHERE name = NEW.name) THEN
        RAISE EXCEPTION 'Палата с именем "%" уже существует', NEW.name;
    END IF;

    -- 2. Проверка размера имени (от 1 до 20 символов)
    IF NEW.name IS NULL OR LENGTH(NEW.name) = 0 THEN
        RAISE EXCEPTION 'Название палаты не может быть пустым';
    END IF;
    
    IF LENGTH(NEW.name) > 20 THEN
        RAISE EXCEPTION 'Название палаты не может превышать 20 символов';
    END IF;

    -- 3. Проверка максимального количества пациентов (от 1 до разумного предела)
    IF NEW.max_count IS NULL OR NEW.max_count < 1 THEN
        RAISE EXCEPTION 'Максимальное количество должно быть не менее 1';
    END IF;
    
    IF NEW.max_count > 20 THEN
        RAISE EXCEPTION 'Максимальное количество не может превышать 20';
    END IF;

    -- 4. Проверка существования диагноза
    IF NEW.diagnosis IS NOT NULL THEN
        SELECT EXISTS(SELECT 1 FROM diagnosis WHERE name = NEW.diagnosis) 
        INTO diagnosis_exists;
        
        IF NOT diagnosis_exists THEN
            RAISE EXCEPTION 'Диагноз "%" не существует', NEW.diagnosis;
        END IF;
        
        -- Получаем ID диагноза для вставки
        SELECT id INTO diagnosis_id_val FROM diagnosis WHERE name = NEW.diagnosis;
    ELSE
        RAISE EXCEPTION 'Диагноз не указан';
    END IF;

    -- 5. Вставляем данные в основную таблицу
    INSERT INTO wards (name, max_count, diagnosis_id) VALUES (NEW.name, NEW.max_count, diagnosis_id_val);

    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE TRIGGER wards_view_insert_trigger
INSTEAD OF INSERT ON wards_view
FOR EACH ROW
EXECUTE FUNCTION insert_into_wards_view();

CREATE OR REPLACE FUNCTION update_wards_view()
RETURNS TRIGGER AS $$
DECLARE
    diagnosis_exists BOOLEAN;
    diagnosis_id_val INTEGER;
    current_patient_count INTEGER;
BEGIN
    -- 1. Проверка уникальности имени палаты (если имя изменилось)
    IF NEW.name != OLD.name AND EXISTS (SELECT 1 FROM wards WHERE name = NEW.name) THEN
        RAISE EXCEPTION 'Палата с именем "%" уже существует', NEW.name;
    END IF;

    -- 2. Проверка размера имени (от 1 до 20 символов)
    IF NEW.name IS NULL OR LENGTH(NEW.name) = 0 THEN
        RAISE EXCEPTION 'Название палаты не может быть пустым';
    END IF;
    
    IF LENGTH(NEW.name) > 20 THEN
        RAISE EXCEPTION 'Название палаты не может превышать 20 символов';
    END IF;

    -- 3. Проверка максимального количества пациентов (от 1 до разумного предела)
    IF NEW.max_count IS NULL OR NEW.max_count < 1 THEN
        RAISE EXCEPTION 'Вместимость палаты должна быть не менее 1 человека';
    END IF;
    
    IF NEW.max_count > 20 THEN
        RAISE EXCEPTION 'Вместимость палаты не может превышать 20 человек';
    END IF;

    -- 4. Проверка что новая вместимость не меньше текущего числа пациентов
    IF NEW.max_count < OLD.max_count THEN
        SELECT COUNT(*) INTO current_patient_count 
        FROM people 
        WHERE ward_id = OLD.id;
        
        IF NEW.max_count < current_patient_count THEN
            RAISE EXCEPTION 'Невозможно уменьшить вместимость до %. В палате уже находится % пациентов', 
                NEW.max_count, current_patient_count;
        END IF;
    END IF;

    -- 5. Проверка существования диагноза
    IF NEW.diagnosis IS NOT NULL THEN
        SELECT EXISTS(SELECT 1 FROM diagnosis WHERE name = NEW.diagnosis) 
        INTO diagnosis_exists;
        
        IF NOT diagnosis_exists THEN
            RAISE EXCEPTION 'Диагноз "%" не существует', NEW.diagnosis;
        END IF;
        
        -- Получаем ID диагноза для обновления
        SELECT id INTO diagnosis_id_val FROM diagnosis WHERE name = NEW.diagnosis;
    ELSE
        diagnosis_id_val := NULL;
    END IF;

    IF OLD.diagnosis != NEW.diagnosis THEN
        CALL redistribute_patients(OLD.id, OLD.name, OLD.max_count);
    END IF;

    -- 6. Обновляем данные в основной таблице
    UPDATE wards 
    SET 
        name = NEW.name, 
        max_count = NEW.max_count, 
        diagnosis_id = diagnosis_id_val
    WHERE id = OLD.id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE TRIGGER wards_view_update_trigger
INSTEAD OF UPDATE ON wards_view
FOR EACH ROW
EXECUTE FUNCTION update_wards_view();
