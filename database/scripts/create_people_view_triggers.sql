CREATE OR REPLACE FUNCTION delete_from_people_view()
RETURNS TRIGGER AS $$
BEGIN
    DELETE FROM people WHERE id = OLD.id;
    RETURN OLD;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE TRIGGER people_view_delete_trigger
INSTEAD OF DELETE ON people_view
FOR EACH ROW
EXECUTE FUNCTION delete_from_people_view();

CREATE OR REPLACE FUNCTION insert_into_people_view()
RETURNS TRIGGER AS $$
DECLARE
    ward_id_nmb INTEGER;
    ward_diagnosis_id INTEGER;
    actual_diagnosis_id INTEGER;
    current_patient_count INTEGER;
    ward_max_count INTEGER;
BEGIN
    -- 1. Проверка уникальности ФИО и непустоты
    IF NEW.first_name IS NULL OR NEW.first_name = '' OR NEW.last_name IS NULL OR NEW.last_name = '' THEN
        RAISE EXCEPTION 'Имя и фамилия не могут быть пустыми';
    END IF;

    IF EXISTS (
        SELECT 1 FROM people 
        WHERE first_name = NEW.first_name 
          AND last_name = NEW.last_name 
          AND father_name = NEW.father_name
    ) THEN
        RAISE EXCEPTION 'Пациент с таким ФИО уже существует: % % %', 
            NEW.first_name, NEW.last_name, NEW.father_name;
    END IF;

     -- 2. Получаем ID диагноза по имени
    SELECT id INTO actual_diagnosis_id 
    FROM diagnosis 
    WHERE name = NEW.diagnosis;
    
    IF actual_diagnosis_id IS NULL THEN
        RAISE EXCEPTION 'Диагноз "%" не найден', NEW.diagnosis;
    END IF;

    -- 3. Получаем ID палаты по имени и проверяем её диагноз
    SELECT w.id, w.diagnosis_id, w.max_count 
    INTO ward_id_nmb, ward_diagnosis_id, ward_max_count
    FROM wards w 
    WHERE w.name = NEW.ward;
    
    IF ward_diagnosis_id IS NULL THEN
        RAISE EXCEPTION 'Палата "%" не найдена', NEW.ward;
    END IF;

    -- 4. Проверяем совместимость диагноза палаты и пациента
    IF ward_diagnosis_id IS NULL OR ward_diagnosis_id != new_diagnosis_id THEN
        RAISE EXCEPTION 'Палата "%" предназначена для другого диагноза', NEW.ward;
    END IF;

    -- 5. Проверяем наличие свободных мест в палате
    SELECT COUNT(*) INTO current_patient_count
    FROM people p
    WHERE p.ward_id = ward_id_nmb;
    
    IF current_patient_count >= ward_max_count THEN
        RAISE EXCEPTION 'В палате "%" нет свободных мест (максимум: %)', 
            NEW.ward, ward_max_count;
    END IF;

    -- 6. Вставляем данные в основную таблицу
    INSERT INTO people (first_name, last_name, father_name, diagnosis_id, ward_id)
    VALUES (
        NEW.first_name, 
        NEW.last_name, 
        NEW.father_name, 
        actual_diagnosis_id,
        ward_id_nmb
    );

    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE TRIGGER people_view_insert_trigger
INSTEAD OF INSERT ON people_view
FOR EACH ROW
EXECUTE FUNCTION insert_into_people_view();

CREATE OR REPLACE FUNCTION update_people_view()
RETURNS TRIGGER AS $$
DECLARE
    patient_exists BOOLEAN;
    ward_diagnosis_id INTEGER;
    new_diagnosis_id INTEGER;
    current_patient_count INTEGER;
    ward_max_count INTEGER;
    target_ward_id INTEGER;
    target_diagnosis_id INTEGER;
BEGIN
    -- 1. Проверяем существование пациента
    SELECT EXISTS(SELECT 1 FROM people WHERE id = OLD.id) INTO patient_exists;
    IF NOT patient_exists THEN
        RAISE EXCEPTION 'Пациент с ID % не существует', OLD.id;
    END IF;

    -- 2. Проверяем заполненность обязательных полей
    IF NEW.diagnosis IS NULL OR NEW.diagnosis = '' THEN
        RAISE EXCEPTION 'Диагноз не может быть пустым';
    END IF;

    IF NEW.ward IS NULL OR NEW.ward = '' THEN
        RAISE EXCEPTION 'Палата не может быть пустой';
    END IF;

    -- 3. Получаем ID диагноза по имени
    SELECT id INTO new_diagnosis_id 
    FROM diagnosis 
    WHERE name = NEW.diagnosis;
    
    IF new_diagnosis_id IS NULL THEN
        RAISE EXCEPTION 'Диагноз "%" не найден', NEW.diagnosis;
    END IF;

    -- 4. Получаем ID палаты по имени и проверяем её диагноз
    SELECT w.id, w.diagnosis_id, w.max_count 
    INTO target_ward_id, ward_diagnosis_id, ward_max_count
    FROM wards w 
    WHERE w.name = NEW.ward;
    
    IF target_ward_id IS NULL THEN
        RAISE EXCEPTION 'Палата "%" не найдена', NEW.ward;
    END IF;

    -- 5. Проверяем совместимость диагноза палаты и пациента
    IF ward_diagnosis_id IS NULL OR ward_diagnosis_id != new_diagnosis_id THEN
        RAISE EXCEPTION 'Палата "%" предназначена для другого диагноза', NEW.ward;
    END IF;

    -- 6. Проверяем наличие свободных мест в палате (если палата изменилась)
    IF OLD.ward != NEW.ward THEN
        SELECT COUNT(*) INTO current_patient_count
        FROM people 
        WHERE ward_id = target_ward_id;
        
        IF current_patient_count >= ward_max_count THEN
            RAISE EXCEPTION 'В палате "%" нет свободных мест (максимум: %)', 
                NEW.ward, ward_max_count;
        END IF;
    END IF;

    UPDATE people 
    SET 
        diagnosis_id = new_diagnosis_id,
        ward_id = target_ward_id
    WHERE id = OLD.id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE TRIGGER people_view_update_trigger
INSTEAD OF UPDATE ON people_view
FOR EACH ROW
EXECUTE FUNCTION update_people_view();