# Метки в подготовленных шаблонах трудовых договоров

Подготовленные шаблоны:
- `isb_standard_v1_prepared.docx`
- `gefest_standard_v1_prepared.docx`

## Основные метки

### Договор
- `{{contract_number}}` — номер договора
- `{{contract_date_human}}` — дата договора в человекочитаемом виде
- `{{contract_end_date_human}}` — дата окончания договора
- `{{document_city}}` — город подписания

### Работодатель
- `{{employer_name}}` — полное наименование работодателя
- `{{employer_display_name}}` — отображаемое краткое наименование в тексте
- `{{employer_bin}}` — БИН
- `{{employer_legal_address}}` — юридический адрес
- `{{employer_iik}}` — ИИК
- `{{employer_bank}}` — наименование банка
- `{{employer_bik}}` — БИК
- `{{employer_director_name}}` — ФИО руководителя
- `{{employer_director_short_name}}` — краткое ФИО руководителя
- `{{employer_director_position}}` — должность руководителя
- `{{employer_director_position_lower}}` — должность руководителя в нижнем регистре
- `{{employer_sign_basis}}` — основание подписи

### Работник
- `{{employee_full_name}}` — полное ФИО
- `{{employee_short_name}}` — короткое ФИО
- `{{employee_position}}` — должность
- `{{employee_iin}}` — ИИН
- `{{employee_id_doc_type}}` — тип документа
- `{{employee_id_doc_number}}` — номер документа
- `{{employee_id_doc_issuer}}` — кем выдан документ
- `{{employee_id_doc_issue_date_human}}` — дата выдачи документа
- `{{employee_address}}` — адрес проживания

### Условия работы
- `{{employment_start_date_human}}` — дата начала работы
- `{{employment_type}}` — основная работа / совместительство
- `{{work_location}}` — место выполнения работы
- `{{work_conditions}}` — условия труда
- `{{probation_months}}` — испытательный срок

### Оплата
- `{{employee_salary}}` — сумма оклада
- `{{employee_salary_words}}` — сумма оклада прописью

## Принцип

- Банковские реквизиты вынесены в нижний блок подписи работодателя.
- В основном тексте договора оставлены только данные работодателя, которые нужны для идентификации.
- Пустые поля работника, например адрес, могут оставаться пустыми без поломки шаблона.
