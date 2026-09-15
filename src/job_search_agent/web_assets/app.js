"use strict";

// All journal values enter the document as text. No source HTML is executed.
(() => {
  const sections = ["overview", "pipeline", "vacancies", "resume", "companies", "documents", "activities", "preparations", "sources", "history"];
  const kinds = {documents: "packages", preparations: "learning", sources: "source_health", history: "events"};
  const icons = ["◫", "⇉", "↗", "✎", "▦", "▤", "◷", "◎", "⊞", "≡"];
  const copy = {
    ru: {
      overview: "Обзор", vacancies: "Вакансии", resume: "Резюме", resumeDesc: "Два master-резюме по трекам, версии под вакансии, предложения правок с решениями, предпросмотр PDF и импорт.", companies: "Компании", documents: "Документы", activities: "Активности", preparations: "Подготовка", sources: "Источники", history: "История",
      workspace: "РАБОЧЕЕ ПРОСТРАНСТВО", privateJournal: "Личный журнал", sidebarNote: "Факты, решения и следующий шаг — в одном месте.", skip: "К содержимому", refresh: "Обновить", footer: "Основано на вашем журнале. Неизвестное остаётся неизвестным.", loading: "Открываем рабочее пространство…", connected: "ЖУРНАЛ ПОДКЛЮЧЁН", updated: "Обновлено", overviewTitle: "Ваша следующая глава.", overviewDesc: "Поиск работы как последовательная работа: от первого источника до следующего разговора.", vacanciesDesc: "Роли, требования и решения. Откройте вакансию, чтобы увидеть детали и основания оценки.", companiesDesc: "Бизнес, продукты, масштаб и найм — с сохранёнными источниками.", documentsDesc: "Пакеты, версии и проверки. Готовность документа и отправка учитываются отдельно.", activitiesDesc: "Выполненная работа, фактические участники и следующие действия.", preparationsDesc: "Планы, практика и подтверждённый прогресс подготовки к интервью.", sourcesDesc: "Состояние источников, успешные проверки и ограничения доступа.", historyDesc: "Сохранённая история решений и действий в вашем журнале.", search: "Поиск по названию, компании и содержимому…", newest: "Сначала новые", alphabetical: "По алфавиту", country: "Страна", city: "Город", remote: "Формат", status: "Статус", track: "Направление", all: "Все", unknown: "Не указано", unknownStatus: "Неизвестно", reset: "Сбросить фильтры", found: "Найдено", records: "записей", open: "Подробнее", original: "Источник ↗", originalLocation: "Локация в источнике", latestVacancies: "Последние вакансии", viewAll: "Все записи ↗", nextSteps: "Следующие действия", focus: "В ФОКУСЕ", focusTitle: "Ясность перед следующим шагом.", focusDesc: "Вакансии с неизвестной доступностью требуют проверки источника. Оценка соответствия и актуальность найма — отдельные решения.", unknownAvailability: "вакансий требуют проверки доступности", companyNote: "сохранённые профили", vacancyNote: "сохранённые роли", documentNote: "пакеты и отдельные тексты", activityNote: "записи работы", noRecords: "Здесь пока нет записей", noRecordsDesc: "Раздел заполнится, когда соответствующие записи появятся в журнале.", noResults: "Ничего не найдено", noResultsDesc: "Попробуйте другой запрос или сбросьте фильтры.", noActions: "Следующие действия не записаны", noActionsDesc: "Зафиксированные следующие шаги появятся здесь.", error: "Не удалось открыть журнал", errorDesc: "Проверьте доступность сервера и повторите загрузку.", retry: "Повторить", previous: "← Назад", next: "Далее →", page: "Страница", of: "из", detailError: "Не удалось получить свежую запись. Показана версия из загруженного обзора.", detailLoading: "Загружаем полную запись…", recordFields: "Сведения", sourceFields: "Источники и материалы", evidenceFields: "Оценка и доказательства", versionFields: "Версии и файлы", related: "Связанные записи", technical: "Исходная запись JSON", yes: "Да", no: "Нет", empty: "Нет данных", remoteLabel: "Удалённо", hybrid: "Гибрид", onsite: "Офис", close: "Закрыть", relatedCompany: "Компания", relatedVacancies: "Вакансии компании", about: "О компании", size: "Масштаб", versions: "Версии", assessed: "Оценка", availability: "Доступность", registeredFile: "Открыть файл ↗", source: "Источник", activeFilters: "с учётом фильтров", current: "Текущая", showMore: "Показать ещё", unknownRecord: "Запись", privacy: "ЛИЧНОЕ ПРОСТРАНСТВО", countriesNote: "География указана по сохранённым данным.", readyNote: "Проверки и отправки — в карточках документов.", noDate: "Дата не указана"
    },
    en: {
      overview: "Overview", vacancies: "Vacancies", resume: "CV", resumeDesc: "Two master CVs by track, vacancy versions, proposed edits with decisions, PDF preview and import.", companies: "Companies", documents: "Documents", activities: "Activities", preparations: "Preparation", sources: "Sources", history: "History", workspace: "WORKSPACE", privateJournal: "Private journal", sidebarNote: "Facts, decisions and the next step, together.", skip: "Skip to content", refresh: "Refresh", footer: "Based on your journal. Unknowns stay unknown.", loading: "Opening your workspace…", connected: "JOURNAL CONNECTED", updated: "Updated", overviewTitle: "Your next chapter.", overviewDesc: "A deliberate job search: from the first source to your next conversation.", vacanciesDesc: "Roles, requirements and decisions. Open a vacancy to inspect its details and assessment evidence.", companiesDesc: "Business, products, scale and hiring, with retained sources.", documentsDesc: "Packages, versions and reviews. Document readiness and submission are separate.", activitiesDesc: "Recorded work, actual contributors and next actions.", preparationsDesc: "Plans, practice and demonstrated interview preparation progress.", sourcesDesc: "Source health, successful checks and access limitations.", historyDesc: "The retained history of decisions and actions in your journal.", search: "Search titles, companies and record contents…", newest: "Newest first", alphabetical: "Alphabetically", country: "Country", city: "City", remote: "Work mode", status: "Status", track: "Track", all: "All", unknown: "Not specified", unknownStatus: "Unknown", reset: "Reset filters", found: "Found", records: "records", open: "Details", original: "Source ↗", originalLocation: "Original location", latestVacancies: "Latest vacancies", viewAll: "View all ↗", nextSteps: "Next actions", focus: "IN FOCUS", focusTitle: "Clarity before the next step.", focusDesc: "Vacancies with unknown availability need a source check. Role fit and current hiring are separate decisions.", unknownAvailability: "vacancies need an availability check", companyNote: "retained profiles", vacancyNote: "retained roles", documentNote: "packages and standalone texts", activityNote: "work records", noRecords: "No records yet", noRecordsDesc: "This section will populate when records are added to the journal.", noResults: "No matching records", noResultsDesc: "Try another search or reset the filters.", noActions: "No next actions recorded", noActionsDesc: "Recorded next steps will appear here.", error: "Could not open the journal", errorDesc: "Check the server connection and try again.", retry: "Retry", previous: "← Previous", next: "Next →", page: "Page", of: "of", detailError: "Could not fetch the latest record. Showing the version from the loaded overview.", detailLoading: "Loading the full record…", recordFields: "Details", sourceFields: "Sources and materials", evidenceFields: "Assessment and evidence", versionFields: "Versions and files", related: "Related records", technical: "Original JSON record", yes: "Yes", no: "No", empty: "No data", remoteLabel: "Remote", hybrid: "Hybrid", onsite: "On-site", close: "Close", relatedCompany: "Company", relatedVacancies: "Company vacancies", about: "About", size: "Scale", versions: "Versions", assessed: "Assessment", availability: "Availability", registeredFile: "Open file ↗", source: "Source", activeFilters: "filtered", current: "Current", showMore: "Show more", unknownRecord: "Record", privacy: "PRIVATE WORKSPACE", countriesNote: "Geography follows the retained evidence.", readyNote: "Review and submission details are in document records.", noDate: "No date recorded"
    }
  };
  const labels = {
    name: ["Название", "Name"], title: ["Название", "Title"], id: ["Идентификатор", "ID"], company_id: ["Компания", "Company"], vacancy_id: ["Вакансия", "Vacancy"], about: ["О компании", "About"], description: ["Описание", "Description"], summary: ["Кратко", "Summary"], business_areas: ["Направления бизнеса", "Business areas"], products: ["Продукты", "Products"], markets: ["Рынки", "Markets"], customer_segments: ["Клиенты", "Customer segments"], size: ["Масштаб", "Scale"], metric: ["Метрика", "Metric"], value: ["Значение", "Value"], as_of: ["На дату", "As of"], scope: ["Область данных", "Scope"], source_url: ["Источник", "Source URL"], confidence: ["Уверенность", "Confidence"], reliability: ["Надёжность", "Reliability"], profile_sources: ["Источники профиля", "Profile sources"], url: ["Ссылка", "URL"], urls: ["Ссылки", "URLs"], sources: ["Источники", "Sources"], location: ["Локация в источнике", "Original location"], country: ["Страна", "Country"], city: ["Город", "City"], market: ["Рынок", "Market"], remote: ["Удалённая работа", "Remote work"], work_mode: ["Формат работы", "Work mode"], availability: ["Доступность вакансии", "Hiring availability"], status: ["Статус", "Status"], status_checked_on: ["Дата проверки статуса", "Status checked on"], role_family: ["Семейство роли", "Role family"], role_type: ["Тип роли", "Role type"], level: ["Уровень", "Level"], raw: ["Исходное значение", "Original value"], source: ["Источник", "Source"], requirements: ["Требования", "Requirements"], text: ["Текст", "Text"], mandatory: ["Обязательное", "Mandatory"], evidence_fact_ids: ["Подтверждающие факты", "Evidence facts"], evidence_reviewed: ["Доказательства проверены", "Evidence reviewed"], gap_type: ["Тип пробела", "Gap type"], tag: ["Тема", "Tag"], tags: ["Темы", "Tags"], decision: ["Решение", "Decision"], track: ["Направление", "Track"], tracks: ["Направления", "Tracks"], target_tracks: ["Целевые направления", "Target tracks"], next_action: ["Следующее действие", "Next action"], next_step: ["Следующий шаг", "Next step"], reason: ["Основание", "Reason"], language_gate: ["Проверка языка", "Language gate"], eligibility_gate: ["Допуск к работе", "Eligibility gate"], role_family_gate: ["Соответствие роли", "Role family gate"], role_family_gates: ["Соответствие роли по направлениям", "Role family gates"], seniority: ["Соответствие уровня", "Seniority"], minimum_years: ["Минимальный опыт, лет", "Minimum years"], authorization: ["Разрешение на работу", "Work authorization"], license: ["Лицензия", "License"], versions: ["Версии", "Versions"], current_version: ["Текущая версия", "Current version"], version_id: ["Версия", "Version"], files: ["Файлы", "Files"], artifacts: ["Материалы", "Artifacts"], reviews: ["Проверки", "Reviews"], review_status: ["Статус проверки", "Review status"], application_status: ["Статус отклика", "Application status"], pdf: ["PDF", "PDF"], markdown: ["Markdown", "Markdown"], source_path: ["Исходный файл", "Source file"], path: ["Файл", "File"], sha256: ["Контрольная сумма", "SHA-256"], bytes: ["Размер, байт", "Bytes"], author: ["Автор", "Author"], contributors: ["Участники", "Contributors"], actor: ["Исполнитель", "Actor"], model: ["Модель", "Model"], provider: ["Провайдер", "Provider"], skill: ["Навык", "Skill"], operation: ["Операция", "Operation"], started_at: ["Начало", "Started"], finished_at: ["Завершение", "Finished"], created_at: ["Создано", "Created"], updated_at: ["Обновлено", "Updated"], at: ["Дата", "Date"], date: ["Дата", "Date"], type: ["Тип", "Type"], note: ["Примечание", "Note"], notes: ["Примечания", "Notes"], details: ["Подробности", "Details"], inputs: ["Входные данные", "Inputs"], outputs: ["Результаты", "Outputs"], records: ["Записи", "Records"], result: ["Результат", "Result"], outcome: ["Итог", "Outcome"], objectives: ["Цели", "Objectives"], exercise: ["Упражнение", "Exercise"], findings: ["Выводы", "Findings"], feedback: ["Обратная связь", "Feedback"], evidence: ["Доказательства", "Evidence"], weeks: ["Недельный план", "Weekly plan"], week: ["Неделя", "Week"], hours_per_week: ["Часов в неделю", "Hours per week"], hours: ["Часы", "Hours"], gaps: ["Пробелы", "Gaps"], tasks: ["Задачи", "Tasks"], last_success: ["Последний успех", "Last success"], last_attempt: ["Последняя попытка", "Last attempt"], next_attempt: ["Следующая попытка", "Next attempt"], count: ["Количество", "Count"], error: ["Ошибка", "Error"], http_status: ["HTTP-статус", "HTTP status"], hiring: ["Найм", "Hiring"], hiring_info: ["Сведения о найме", "Hiring information"], salary: ["Вознаграждение", "Compensation"], compensation: ["Вознаграждение", "Compensation"], employees: ["Сотрудники", "Employees"], headcount: ["Численность", "Headcount"], revenue: ["Выручка", "Revenue"], currency: ["Валюта", "Currency"], period: ["Период", "Period"], interview_plans: ["Планы интервью", "Interview plans"], interview_practices: ["Практика интервью", "Interview practice"], interview_feedback: ["Обратная связь по интервью", "Interview feedback"], interview_progress: ["Прогресс подготовки", "Interview progress"], packages: ["Пакеты документов", "Document packages"], learning: ["Планы подготовки", "Learning plans"], source_health: ["Состояние источников", "Source health"], events: ["События", "Events"], assessments: ["Оценки", "Assessments"], current_assessments: ["Текущие оценки", "Current assessments"], company_dossiers: ["Досье компаний", "Company dossiers"], cover_letters: ["Сопроводительные письма", "Cover letters"], text_revisions: ["Редакции текста", "Text revisions"], submissions: ["Отправки", "Submissions"], employer_responses: ["Ответы работодателей", "Employer responses"], activity_events: ["События активностей", "Activity events"], observations: ["Наблюдения источников", "Source observations"]
  };
  const enums = {
    unknown: ["Неизвестно", "Unknown"], active: ["Активна", "Active"], open: ["Открыта", "Open"], closed: ["Закрыта", "Closed"], archived: ["В архиве", "Archived"], priority: ["Приоритет", "Priority"], needs_clarification: ["Нужно уточнить", "Needs clarification"], not_suitable: ["Не подходит", "Not suitable"], watch: ["Наблюдать", "Watch"], pending: ["Ожидает", "Pending"], pending_review: ["Ожидает проверки", "Pending review"], approved: ["Одобрено", "Approved"], ready: ["Готово", "Ready"], drafted: ["Черновик", "Drafted"], draft: ["Черновик", "Draft"], submitted: ["Отправлено", "Submitted"], running: ["В работе", "Running"], in_progress: ["В работе", "In progress"], completed: ["Завершено", "Completed"], failed: ["Ошибка", "Failed"], blocked: ["Заблокировано", "Blocked"], healthy: ["Доступен", "Healthy"], ok: ["Доступен", "OK"], success: ["Успешно", "Success"], partial: ["Частично", "Partial"], cooldown: ["Пауза запросов", "Cooldown"], pass: ["Пройдено", "Pass"], fail: ["Не пройдено", "Fail"], product: ["Продуктовое", "Product"], "technical-leadership": ["Техническое лидерство", "Technical leadership"], remote: ["Удалённо", "Remote"], hybrid: ["Гибрид", "Hybrid"], onsite: ["Офис", "On-site"], verified: ["Подтверждено", "Verified"], self_reported: ["Со слов кандидата", "Self-reported"], conflicting: ["Противоречие", "Conflicting"], employees: ["сотрудников", "employees"], headcount: ["сотрудников", "employees"], general: ["Общий план", "General plan"]
  };
  const extraCopy = {
    ru: {availabilityFilter: "Доступность", filters: "Фильтры", showUnknown: "Показать вакансии →", journalUpdated: "Журнал изменён", loadedAt: "загружено", refreshing: "Обновляем…", refreshFailed: "Не удалось обновить. Показаны ранее загруженные данные.", copyLink: "Скопировать ссылку", linkCopied: "Ссылка скопирована", recordMissing: "Запись по ссылке не найдена в текущем журнале.", decisionNote: "Решение", searchHint: "Нажмите / для поиска"},
    en: {availabilityFilter: "Availability", filters: "Filters", showUnknown: "Show vacancies →", journalUpdated: "Journal changed", loadedAt: "loaded", refreshing: "Refreshing…", refreshFailed: "Refresh failed. Showing previously loaded data.", copyLink: "Copy link", linkCopied: "Link copied", recordMissing: "The linked record is not in the current journal.", decisionNote: "Decision", searchHint: "Press / to search"}
  };
  Object.keys(copy).forEach((lang) => Object.assign(copy[lang], extraCopy[lang]));
  // Canonical English country names from the server projection → ISO 3166 codes for localized display.
  const countryCodes = {"Argentina": "AR", "Australia": "AU", "Austria": "AT", "Belarus": "BY", "Belgium": "BE", "Brazil": "BR", "Bulgaria": "BG", "Canada": "CA", "Chile": "CL", "China": "CN", "Colombia": "CO", "Croatia": "HR", "Cyprus": "CY", "Czech Republic": "CZ", "Denmark": "DK", "Estonia": "EE", "Finland": "FI", "France": "FR", "Germany": "DE", "Greece": "GR", "Hong Kong": "HK", "Hungary": "HU", "India": "IN", "Indonesia": "ID", "Ireland": "IE", "Israel": "IL", "Italy": "IT", "Japan": "JP", "Kazakhstan": "KZ", "Latvia": "LV", "Lithuania": "LT", "Luxembourg": "LU", "Malaysia": "MY", "Mexico": "MX", "Netherlands": "NL", "New Zealand": "NZ", "Norway": "NO", "Philippines": "PH", "Poland": "PL", "Portugal": "PT", "Romania": "RO", "Russia": "RU", "Serbia": "RS", "Singapore": "SG", "Slovakia": "SK", "Slovenia": "SI", "South Africa": "ZA", "South Korea": "KR", "Spain": "ES", "Sweden": "SE", "Switzerland": "CH", "Thailand": "TH", "Turkey": "TR", "Ukraine": "UA", "United Arab Emirates": "AE", "United Kingdom": "GB", "United States": "US", "Vietnam": "VN"};

  Object.assign(labels, {
    activity_id: ["Активность", "Activity"], after: ["После", "After"], aliases: ["Другие названия", "Aliases"], app_revision: ["Версия приложения", "App revision"], applications_sent: ["Отправлено откликов", "Applications sent"], assessment_id: ["Оценка", "Assessment"], audit: ["Аудит", "Audit"], author_model: ["Модель автора", "Author model"], author_session: ["Сессия автора", "Author session"], backup_snapshot: ["Снимок резервной копии", "Backup snapshot"], baseline_only: ["Только базовый план", "Baseline only"], before: ["До", "Before"], bigtech_company_ids: ["Компании Big Tech", "Big Tech companies"], bigtech_target: ["Цель по Big Tech", "Big Tech target"], board: ["Доска вакансий", "Job board"], branch: ["Ветка", "Branch"], change: ["Изменение", "Change"], checked_on: ["Дата проверки", "Checked on"], ci: ["CI", "CI"], clean_public_clone_verified: ["Чистый публичный клон проверен", "Clean public clone verified"], cli: ["CLI", "CLI"], commit: ["Коммит", "Commit"], company_levels: ["Уровни компаний", "Company levels"], company_name: ["Компания", "Company"], context: ["Контекст", "Context"], cost: ["Стоимость", "Cost"], counts: ["Количество", "Counts"], coverage: ["Покрытие", "Coverage"], covered: ["Покрыто", "Covered"], cv: ["Резюме", "CV"], cv_pdf: ["Резюме (PDF)", "CV PDF"], cv_source: ["Исходник резюме", "CV source"], cv_text: ["Текст резюме", "CV text"], delegated_models: ["Делегированные модели", "Delegated models"], deliverable: ["Результат", "Deliverable"], dictionary_and_gitleaks_history_checked: ["История проверена словарём и Gitleaks", "Dictionary and Gitleaks history checked"], done_requires: ["Критерий готовности", "Done requires"], enabled: ["Включён", "Enabled"], entity_ids: ["Связанные записи", "Related records"], environment: ["Окружение", "Environment"], event_id: ["Событие", "Event"], exclude: ["Исключения", "Exclude"], expected_result: ["Ожидаемый результат", "Expected result"], fact_count: ["Количество фактов", "Fact count"], file_count: ["Количество файлов", "File count"], first_seen: ["Впервые найдена", "First seen"], last_seen: ["Последний раз найдена", "Last seen"], git_histories_preserved: ["История Git сохранена", "Git histories preserved"], github_node_id: ["GitHub node ID", "GitHub node ID"], health: ["Состояние", "Health"], historical_artifacts_preserved: ["Исторические файлы сохранены", "Historical artifacts preserved"], historical_records_rewritten: ["Исторические записи переписаны", "Historical records rewritten"], include_title: ["Фильтр по названию", "Title filter"], infra_revision: ["Версия инфраструктуры", "Infrastructure revision"], input_sha256: ["SHA-256 входных данных", "Input SHA-256"], input_tokens: ["Входные токены", "Input tokens"], interests: ["Интересы", "Interests"], interval_seconds: ["Интервал, секунд", "Interval, seconds"], interview_date: ["Дата интервью", "Interview date"], kind: ["Тип записи", "Record kind"], language: ["Язык", "Language"], legacy_key: ["Ключ в старом журнале", "Legacy key"], letter: ["Письмо", "Letter"], letter_pdf: ["Письмо (PDF)", "Letter PDF"], letter_source: ["Исходник письма", "Letter source"], local_checkout: ["Локальная копия", "Local checkout"], manifest_sha256: ["SHA-256 манифеста", "Manifest SHA-256"], market_effort: ["Распределение усилий по рынкам", "Market effort"], masters: ["Мастер-резюме", "Master CVs"], max_pages: ["Максимум страниц", "Max pages"], method: ["Метод", "Method"], model_identity_note: ["Примечание о модели", "Model identity note"], new_url: ["Новая ссылка", "New URL"], old_url: ["Старая ссылка", "Old URL"], original_path: ["Исходный путь", "Original path"], output_tokens: ["Выходные токены", "Output tokens"], pages: ["Страницы", "Pages"], parent_activity_id: ["Родительская активность", "Parent activity"], pending_review_reason: ["Причина ожидания проверки", "Pending review reason"], plan: ["План", "Plan"], plan_artifact: ["Файл плана", "Plan artifact"], plan_id: ["План", "Plan"], policy: ["Правила", "Policy"], policy_reconciled_on: ["Правила сверены", "Policy reconciled on"], posting: ["Публикация вакансии", "Posting"], prior_inventory: ["Предыдущая инвентаризация", "Prior inventory"], private_data_moved: ["Личные данные перенесены", "Private data moved"], profile_checked_on: ["Профиль проверен", "Profile checked on"], proxy_allowed: ["Прокси разрешён", "Proxy allowed"], qa_files: ["Файлы контроля качества", "QA files"], read_only_replica: ["Реплика только для чтения", "Read-only replica"], receipt: ["Квитанция", "Receipt"], receipt_sha256: ["SHA-256 квитанции", "Receipt SHA-256"], record_type: ["Тип записи", "Record type"], registry_sha256: ["SHA-256 реестра", "Registry SHA-256"], related_vacancy_ids: ["Связанные вакансии", "Related vacancies"], renderer_version: ["Версия генератора", "Renderer version"], repository: ["Репозиторий", "Repository"], request: ["Запрос", "Request"], required_model: ["Требуемая модель", "Required model"], requirement_id: ["Требование", "Requirement"], requirements_note: ["Комментарий к требованиям", "Requirements note"], requires_flagship: ["Нужна флагманская модель", "Requires flagship"], research_scope: ["Глубина исследования", "Research scope"], resources: ["Материалы", "Resources"], result_sha256: ["SHA-256 результата", "Result SHA-256"], review: ["Проверка", "Review"], review_files: ["Файлы проверки", "Review files"], reviewed_on: ["Дата проверки", "Reviewed on"], reviewer_model: ["Модель проверяющего", "Reviewer model"], revision: ["Ревизия", "Revision"], russia_director_only: ["В России — только директорский уровень", "Russia: director level only"], schema_version: ["Версия схемы", "Schema version"], score: ["Оценка", "Score"], session: ["Сессия", "Session"], shared: ["Общие темы", "Shared"], snapshot: ["Снимок", "Snapshot"], source_verified_url: ["Проверенная ссылка источника", "Verified source URL"], submission: ["Отправка", "Submission"], suggested_facts: ["Подходящие факты", "Suggested facts"], target_track: ["Целевое направление", "Target track"], task: ["Задача", "Task"], telemetry: ["Телеметрия", "Telemetry"], tests_passed: ["Тесты пройдены", "Tests passed"], track_verdict: ["Вердикт по направлению", "Track verdict"], types: ["Типы", "Types"], unknowns: ["Неизвестные", "Unknowns"], vacancy_ids: ["Вакансии", "Vacancies"], verdict: ["Вердикт", "Verdict"], version: ["Версия", "Version"], warning: ["Предупреждение", "Warning"], watch_themes: ["Темы для наблюдения", "Watch themes"], work_authorization_default: ["Разрешение на работу по умолчанию", "Default work authorization"], focus: ["Фокус", "Focus"], dry_run: ["Пробный запуск", "Dry run"], missing: ["Отсутствует", "Missing"], legacy_files: ["Файлы старого журнала", "Legacy files"], imports: ["Импорт", "Import"], source_settings: ["Настройки источника", "Source settings"], vacancies: ["Вакансии", "Vacancies"], companies: ["Компании", "Companies"], activities: ["Активности", "Activities"], ru: ["Россия", "Russia"], intl: ["Международный рынок", "International"]
  });
  Object.assign(enums, {
    todo: ["К выполнению", "To do"], timeout: ["Превышено время", "Timed out"], expired_copy: ["Копия устарела", "Expired copy"], follow_up: ["Вернуться позже", "Follow up"], unassigned: ["Не распределена", "Unassigned"], monitor: ["Наблюдать", "Monitor"], not_priority: ["Не в приоритете", "Not a priority"], ranked: ["Ранжирована", "Ranked"], researched: ["Изучена", "Researched"], rejected: ["Отклонена", "Rejected"], lead: ["Наводка", "Lead"], legacy_unverified: ["Не проверено (старый журнал)", "Legacy, unverified"], passed: ["Пройдена", "Passed"], vacancy: ["Вакансия", "Vacancy"], evidence: ["Доказательства", "Evidence"], interview: ["Интервью", "Interview"], practice: ["Практика", "Practice"], structural: ["Структурный", "Structural"], intl: ["Международный", "International"], ru: ["Россия", "Russia"], not_disclosed: ["Не раскрыто", "Not disclosed"], not_disclosed_on_checked_page: ["Не раскрыто на проверенной странице", "Not disclosed on checked page"], reported: ["Сообщается", "Reported"], company_and_application: ["Компания и отклик", "Company and application"], target_screen: ["Целевой отбор", "Target screen"], vacancies_only: ["Только вакансии", "Vacancies only"], flag: ["Флаг", "Flag"], master: ["Мастер-резюме", "Master CV"], interview_plans: ["Планы интервью", "Interview plans"], interview_plan: ["План интервью", "Interview plan"], corporate: ["Корпоративный сайт", "Corporate site"], greenhouse: ["Greenhouse", "Greenhouse"], global: ["Глобально", "Global"], enabled: ["Включён", "Enabled"], disabled: ["Выключен", "Disabled"], never_checked: ["Ещё не проверялся", "Never checked"], unverified: ["Не проверена", "Unverified"], needs_check: ["Требует проверки", "Needs a check"], current: ["Актуальная", "Current"], superseded: ["Устарела", "Superseded"], expired: ["Истекла", "Expired"],
    activity_finished: ["Активность завершена", "Activity finished"], activity_output_registered: ["Результат активности зарегистрирован", "Activity output registered"], activity_started: ["Активность начата", "Activity started"], annotation_sources_preserved: ["Источники аннотаций сохранены", "Annotation sources preserved"], annotation_sources_verified: ["Источники аннотаций проверены", "Annotation sources verified"], backup_created: ["Создана резервная копия", "Backup created"], career_copilot_implemented: ["Career Copilot внедрён", "Career Copilot implemented"], company_policy_reconciled: ["Правила по компаниям сверены", "Company policy reconciled"], company_profile_reviewed: ["Профиль компании проверен", "Company profile reviewed"], dashboard_deployed: ["Дашборд развёрнут", "Dashboard deployed"], document_prepared: ["Документ подготовлен", "Document prepared"], document_reviewed: ["Документ проверен", "Document reviewed"], drafts_recorded: ["Черновики записаны", "Drafts recorded"], facts_imported: ["Факты импортированы", "Facts imported"], history_imported: ["История импортирована", "History imported"], learning_planned: ["План подготовки составлен", "Learning planned"], legacy_imported: ["Старый журнал импортирован", "Legacy imported"], packages_recorded: ["Пакеты документов записаны", "Packages recorded"], pipeline_repository_renamed: ["Репозиторий переименован", "Pipeline repository renamed"], public_project_pushed: ["Публичный проект опубликован", "Public project pushed"], requirements_annotated: ["Требования размечены", "Requirements annotated"], research_recorded: ["Исследование записано", "Research recorded"], rules_updated: ["Правила обновлены", "Rules updated"], search_policy_reconciled: ["Правила поиска сверены", "Search policy reconciled"], source_checked: ["Источник проверен", "Source checked"], vacancy_evaluated: ["Вакансия оценена", "Vacancy evaluated"], workflow_configured: ["Процесс настроен", "Workflow configured"], workflow_delivered: ["Процесс передан", "Workflow delivered"], workspace_consolidated: ["Рабочее пространство объединено", "Workspace consolidated"], dashboard_snapshot_artifact_aliased: ["Файл снимка дашборда связан с журналом", "Dashboard snapshot file linked"], greenhouse: ["Greenhouse", "Greenhouse"], linkedinsalaries: ["LinkedIn Salaries", "LinkedIn Salaries"], lever: ["Lever", "Lever"]
  });
  Object.assign(extraCopy.ru, {fullDescription: "Полное описание", showFullDescription: "Показать полное описание", noDescription: "Описание не сохранено — откройте вакансию по ссылке.", learningPlanLink: "План подготовки", descriptionTitle: "О вакансии", technicalDetails: "Технические детали: оценки, проверки, поля и связи", preparationTitle: "Подготовка к этой вакансии", download: "Скачать"});
  Object.assign(extraCopy.en, {fullDescription: "Full description", showFullDescription: "Show the full description", noDescription: "No description saved; open the posting link.", learningPlanLink: "Learning plan", descriptionTitle: "About the role", technicalDetails: "Technical details: assessments, checks, fields and links", preparationTitle: "Preparation for this role", download: "Download"});
  Object.assign(extraCopy.ru, {pipeline: "Воронка", pipelineDesc: "Где находится каждая активная вакансия: от находки до интервью, сколько дней на этапе и что пора сделать.", contentTranslated: "Тексты: перевод", contentOriginal: "Тексты: оригинал", contentToggleHint: "Показывать сохранённые переводы записей или исходный текст", freshnessFilter: "Проверка доступности", freshness_fresh: "Проверена за 7 дней", freshness_aging: "Проверена 8–14 дней назад", freshness_stale: "Давно не проверялась (15+ дней)", freshness_never: "Не проверялась", neverChecked: "Доступность не проверялась", checkedAgo: "Проверена", undetermined: "результат не определён", checkNow: "Проверить", checkAll: "Проверить доступность", checkingProgress: "Проверяем доступность", checkDone: "Проверка завершена", checkBusy: "Проверка уже идёт — дождитесь её окончания.", checkFailed: "Не удалось выполнить проверку. Попробуйте позже.", checkUnavailable: "Проверка из интерфейса не настроена: запустите ajh availability check или dashboard с --state-dir.", availabilityTitle: "Доступность вакансии", checkResult: "Результат", checkReason: "Основание", checkConfidence: "Уверенность", checkEvidence: "Признак", checkTime: "Проверено", checkUrl: "Проверенная страница", pendingImport: "Результат сохранён на сервере и будет перенесён в локальный журнал при следующей синхронизации.", noCheckYet: "Автоматическая проверка ещё не проводилась.", reason_http_gone: "Страница вакансии удалена (HTTP 404/410)", reason_redirected_away: "Ссылка перенаправляет на общий список или страницу закрытия", reason_closed_marker: "На странице сказано, что вакансия закрыта или в архиве", reason_structured_expired: "Истёк срок в структурированной разметке вакансии", reason_apply_control: "На странице есть кнопка отклика", reason_structured_posting: "Страница публикует структурированную вакансию", reason_access_blocked: "Сайт ограничил автоматический доступ; обход не выполняется", reason_http_error: "Сайт вернул ошибку", reason_no_signal: "На странице нет надёжного признака", reason_network_error: "Сетевая ошибка", reason_not_public_url: "Адрес недоступен для проверки", reason_no_url: "У вакансии нет ссылки на объявление", reason_too_many_redirects: "Слишком много перенаправлений", confidence_high: "высокая", confidence_medium: "средняя", confidence_low: "низкая", remindersTitle: "Напоминания", reminderCheckGroup: "Доступность не проверялась или устарела (15+ дней)", remindersDesc: "Что пора сделать по активным вакансиям. Правила: интервью в ближайшие 7 дней, проверенные документы без отклика дольше 3 дней, документы без ревью дольше 5 дней, нет ответа дольше 14 дней, давно не проверенная доступность.", noReminders: "Сейчас напоминаний нет", noRemindersDesc: "Активные вакансии в порядке.", reminderInterview: "Интервью через", reminderSubmit: "Документы проверены, отклик не отправлен", reminderConfirmSubmission: "Отмечено как отправленное без подтверждённой отправки (дата и доказательство)", reminderReview: "Документы ждут ревью", reminderResponse: "Нет ответа после отправки", reminderCheck: "Доступность проверялась", reminderNeverChecked: "Доступность ни разу не проверялась", funnelTitle: "Этапы", funnelDesc: "Вакансия стоит на самом дальнем достигнутом этапе. Дата этапа — из журнала.", inStage: "На этапе", closedLane: "Закрытые и отклонённые", stage_found: "Найдена", stage_found_hint: "Сохранена в журнале", stage_assessed: "Оценена", stage_assessed_hint: "Есть оценка соответствия", stage_documents: "Документы", stage_documents_hint: "Подготовлен пакет", stage_reviewed: "Проверены", stage_reviewed_hint: "Независимое ревью пройдено", stage_submitted: "Отклик отправлен", stage_submitted_hint: "Подтверждённая отправка с датой и доказательством", stage_response: "Ответ", stage_response_hint: "Есть ответ работодателя", stage_interview: "Интервью", stage_interview_hint: "Приглашение работодателя или назначенная дата"});
  Object.assign(extraCopy.en, {pipeline: "Pipeline", pipelineDesc: "Where each active vacancy stands, from discovery to interview, how long it has been in a stage and what is due.", contentTranslated: "Texts: translated", contentOriginal: "Texts: original", contentToggleHint: "Show stored record translations or the original text", freshnessFilter: "Availability check", freshness_fresh: "Checked within 7 days", freshness_aging: "Checked 8–14 days ago", freshness_stale: "Not checked for 15+ days", freshness_never: "Never checked", neverChecked: "Availability never checked", checkedAgo: "Checked", undetermined: "no clear result", checkNow: "Check", checkAll: "Check availability", checkingProgress: "Checking availability", checkDone: "Check finished", checkBusy: "A check is already running; wait for it to finish.", checkFailed: "The check could not run. Try again later.", checkUnavailable: "Checks from the interface are not configured: run ajh availability check or start the dashboard with --state-dir.", availabilityTitle: "Vacancy availability", checkResult: "Result", checkReason: "Reason", checkConfidence: "Confidence", checkEvidence: "Signal", checkTime: "Checked", checkUrl: "Checked page", pendingImport: "Stored on the server; it is imported into the local journal at the next sync.", noCheckYet: "No automated check yet.", reason_http_gone: "The posting was removed (HTTP 404/410)", reason_redirected_away: "The link redirects to a listing or closed page", reason_closed_marker: "The page says the vacancy is closed or archived", reason_structured_expired: "The structured posting has expired", reason_apply_control: "The page shows an apply control", reason_structured_posting: "The page publishes a structured job posting", reason_access_blocked: "The site restricted automated access; no bypass is attempted", reason_http_error: "The site returned an error", reason_no_signal: "No reliable signal on the page", reason_network_error: "Network error", reason_not_public_url: "The address cannot be checked", reason_no_url: "The vacancy has no posting link", reason_too_many_redirects: "Too many redirects", confidence_high: "high", confidence_medium: "medium", confidence_low: "low", remindersTitle: "Reminders", reminderCheckGroup: "Availability never checked or stale (15+ days)", remindersDesc: "What is due for active vacancies. Rules: interview within 7 days, reviewed documents not sent for over 3 days, documents awaiting review for over 5 days, no response for over 14 days, stale availability.", noReminders: "No reminders right now", noRemindersDesc: "Active vacancies are up to date.", reminderInterview: "Interview in", reminderSubmit: "Documents reviewed, not sent", reminderConfirmSubmission: "Marked as sent without a confirmed submission (date and evidence)", reminderReview: "Documents awaiting review", reminderResponse: "No response after sending", reminderCheck: "Availability last checked", reminderNeverChecked: "Availability never checked", funnelTitle: "Stages", funnelDesc: "A vacancy sits in the furthest stage it has reached. Stage dates come from the journal.", inStage: "In stage", closedLane: "Closed and rejected", stage_found: "Found", stage_found_hint: "Saved to the journal", stage_assessed: "Assessed", stage_assessed_hint: "Fit assessment exists", stage_documents: "Documents", stage_documents_hint: "Package prepared", stage_reviewed: "Reviewed", stage_reviewed_hint: "Independent review passed", stage_submitted: "Applied", stage_submitted_hint: "Confirmed submission with date and evidence", stage_response: "Response", stage_response_hint: "Employer responded", stage_interview: "Interview", stage_interview_hint: "Invitation from the employer or a scheduled date"});
  Object.assign(extraCopy.ru, {openPosting: "Открыть вакансию", postingShort: "вакансия", hoursShort: "ч", foundOn: "найдена", downloadPdf: "Скачать PDF", downloadMarkdown: "Скачать Markdown", openRecord: "Карточка записи", showPlan: "План целиком", createdOn: "Создан", weeksShort: "нед.", notScheduled: "не назначена", weeksTitle: "Недельный план", focusColumn: "Фокус", gapsTitle: "Пробелы и что закрыть", mandatoryShort: "обязательных", detailedPlan: "Подробный план", planLoading: "Загружаем подробный план…", planUnavailable: "Подробный план недоступен или не прошёл проверку целостности.", sharedPlanNote: "Этот подробный план общий для направлений", showSuperseded: "Показать предыдущие версии планов", hideSuperseded: "Скрыть предыдущие версии планов", configuredSources: "Настроенные источники", configuredSourcesDesc: "Автоматические проверки вакансий: расписание, последняя проверка и результат.", dataSources: "Все источники данных", dataSourcesDesc: "Сайты, на которые ссылаются вакансии, компании, документы и история. Раскройте число ссылок, чтобы перейти к каждой.", sourceHost: "Сайт", sourceUse: "Где используется", sourceRecords: "Записей", sourceLinks: "Ссылки", schedule: "Расписание", daily: "раз в сутки", every: "каждые", lastCheck: "Последняя проверка", nextCheck: "Следующая проверка", foundCount: "Найдено вакансий", titleFilter: "Фильтр названий", never: "ещё не проводилась", noSourceLink: "Ссылка на источник не сохранена в настройках.", noTime: "время не указано", more: "ещё", recordChanged: "запись обновлена", eventType: "Тип события", foundLabel: "Найдена", versionFrom: "Версия от"});
  Object.assign(extraCopy.en, {openPosting: "Open posting", postingShort: "posting", hoursShort: "h", foundOn: "found", downloadPdf: "Download PDF", downloadMarkdown: "Download Markdown", openRecord: "Record details", showPlan: "Full plan", createdOn: "Created", weeksShort: "wk", notScheduled: "not scheduled", weeksTitle: "Weekly plan", focusColumn: "Focus", gapsTitle: "Gaps to close", mandatoryShort: "mandatory", detailedPlan: "Detailed plan", planLoading: "Loading the detailed plan…", planUnavailable: "The detailed plan is unavailable or failed its integrity check.", sharedPlanNote: "This detailed plan is shared by tracks", showSuperseded: "Show previous plan versions", hideSuperseded: "Hide previous plan versions", configuredSources: "Configured sources", configuredSourcesDesc: "Automated vacancy checks: schedule, last check and result.", dataSources: "All data sources", dataSourcesDesc: "Websites referenced by vacancies, companies, documents and history. Expand the link count to open each one.", sourceHost: "Website", sourceUse: "Used by", sourceRecords: "Records", sourceLinks: "Links", schedule: "Schedule", daily: "daily", every: "every", lastCheck: "Last check", nextCheck: "Next check", foundCount: "Vacancies found", titleFilter: "Title filter", never: "not yet run", noSourceLink: "No source link is stored in settings.", noTime: "time not recorded", more: "more", recordChanged: "record updated", eventType: "Event type", foundLabel: "Found", versionFrom: "Version of"});
  Object.assign(extraCopy.ru, {recentVacancies: "Свежие вакансии", needs_check: "Требует проверки", masterCv: "Мастер-резюме", files: "Файлы журнала", filesDesc: "Все зарегистрированные материалы, доступные для скачивания", activityEvent: "Событие активности", importRecord: "Импорт", superseded: "устарела"});
  Object.assign(extraCopy.en, {recentVacancies: "Recent vacancies", needs_check: "Needs a check", masterCv: "Master CV", files: "Journal files", filesDesc: "All registered materials available for download", activityEvent: "Activity event", importRecord: "Import", superseded: "superseded"});
  Object.keys(copy).forEach((lang) => Object.assign(copy[lang], extraCopy[lang]));
  const INACTIVE = new Set(["closed", "archived", "expired", "expired_copy", "rejected"]);
  const singular = {vacancies: ["Вакансия", "Vacancy"], companies: ["Компания", "Company"], activities: ["Активность", "Activity"], learning: ["План подготовки", "Learning plan"], events: ["Событие", "Event"], assessments: ["Оценка", "Assessment"], packages: ["Пакет документов", "Document package"], interview_plans: ["План интервью", "Interview plan"], source_settings: ["Источник", "Source"], imports: ["Импорт", "Import"]};
  const kindName = (kind) => singular[kind]?.[state.lang === "ru" ? 0 : 1] || label(kind);
  const humanize = (value) => String(value).replaceAll("_", " ").replace(/^./, (c) => c.toUpperCase());
  const regionNames = {};
  const countryName = (value) => { const code = countryCodes[value]; if (!code || typeof Intl.DisplayNames !== "function") return value; try { regionNames[state.lang] ||= new Intl.DisplayNames([state.lang], {type: "region"}); return regionNames[state.lang].of(code) || value; } catch (_) { return value; } };
  const state = {lang: "ru", section: "overview", data: null, query: "", filters: {}, sort: "newest", page: 1, pageSize: 24, detailToken: 0, opened: null, filtersOpen: false, loadedAt: null, showSuperseded: false, contentMode: "translated", detailTab: "vacancy"};
  try { state.lang = localStorage.getItem("career-copilot-language") === "en" ? "en" : "ru"; state.contentMode = localStorage.getItem("career-copilot-content") === "original" ? "original" : "translated"; } catch (_) { /* Storage is optional. */ }
  const $ = (id) => document.getElementById(id);
  const t = (key) => copy[state.lang][key] || key;
  const label = (key) => labels[key]?.[state.lang === "ru" ? 0 : 1] || copy[state.lang][key] || String(key).replaceAll("_", " ").replace(/^./, (c) => c.toUpperCase());
  const translated = (value) => enums[value]?.[state.lang === "ru" ? 0 : 1] || (typeof value === "string" && /^[a-z]+(?:_[a-z0-9]+)+$/.test(value) ? humanize(value) : typeof value === "string" ? tx(value) : String(value));
  const el = (tag, className, text) => { const node = document.createElement(tag); if (className) node.className = className; if (text !== undefined) node.textContent = text; return node; };
  const button = (text, className, action) => { const node = el("button", className, text); node.type = "button"; node.addEventListener("click", action); return node; };
  // Journal text in the interface language when a stored translation exists; originals stay one click away.
  const tx = (text) => state.contentMode === "original" ? text : state.data?.translations?.[text]?.[state.lang] || text;
  const scalar = (value) => value === null || value === undefined ? "" : typeof value === "object" ? (Array.isArray(value) ? value.map(scalar).filter(Boolean).join(" · ") : scalar(value.text || value.name || value.title || value.value || value.raw || value.description)) : typeof value === "string" ? tx(value) : String(value);
  const known = (value) => { const v = scalar(value).trim(); return v && !/^(unknown|not specified|n\/a|null|none|неизвестно|не указано)$/i.test(v) ? v : ""; };
  const CV_KINDS = new Set(["cv_edits", "cv_edit_decisions", "cv_imports"]);
  const records = (section) => section === "pipeline" ? (state.data?.vacancies || []).filter((record) => record.kind === "vacancies") : section === "resume" ? (state.data?.documents || []).filter((record) => record.kind === "packages" || CV_KINDS.has(record.kind)) : section === "documents" ? (state.data?.documents || []).filter((record) => !CV_KINDS.has(record.kind)) : state.data?.[section] || [];
  const primaryRecords = (section) => ["companies", "vacancies", "activities"].includes(section) ? records(section).filter((record) => record.kind === section) : section === "documents" ? records(section).filter((record) => record.kind !== "legacy_files") : section === "resume" ? records(section).filter((record) => record.kind === "packages") : section === "preparations" ? records(section).filter((record) => ["learning", "interview_plans", "track_plans", "preparation_briefs"].includes(record.kind)) : records(section);
  const defaultFilters = (section) => ["companies", "vacancies", "activities"].includes(section) ? {kind: section} : {};
  const unwrap = (record) => record.payload && typeof record.payload === "object" && !Array.isArray(record.payload) ? record.payload : record;
  const normalize = (record, section) => ({...record, id: String(record.id ?? unwrap(record).id ?? ""), kind: record.kind || kinds[section] || section, payload: unwrap(record)});
  const allRecords = () => state.all || sections.filter((section) => section !== "pipeline").flatMap((section) => records(section));
  const byId = (id, preferred) => { const index = state.index; if (index) return (preferred && index.get(`${preferred}/${id}`)) || index.get(`*/${id}`); const all = allRecords(); return (preferred && all.find((record) => record.kind === preferred && record.id === id)) || all.find((record) => record.id === id && !["activity_events", "legacy_files"].includes(record.kind)); };
  const recordTitle = (record) => {
    const p = record.payload;
    if (record.kind === "packages") { if (p.vacancy_id === "master") return `${t("masterCv")} · ${tracks(record).map(translated).join(", ") || translated(String(record.id).replace(/^master-/, ""))}`; const vacancy = byId(p.vacancy_id, "vacancies"); if (!p.title && vacancy) return [recordTitle(vacancy), companyName(vacancy)].filter(Boolean).join(" · "); }
    if (record.kind === "events" && p.type && !p.title) return translated(p.type);
    if (record.kind === "activity_events") { const activity = byId(p.activity_id, "activities"); return activity ? `${t("activityEvent")} · ${recordTitle(activity)}` : t("activityEvent"); }
    if (record.kind === "imports") return `${t("importRecord")} · ${String(record.id).slice(0, 8)}`;
    if (["source_health", "source_settings"].includes(record.kind) && !p.title) { const setting = records("sources").find((item) => item.kind === "source_settings" && item.id === record.id); return scalar(p.company_name || setting?.payload.company_name) ? `${scalar(p.company_name || setting?.payload.company_name)} · ${translated(p.provider || setting?.payload.provider || record.id)}` : humanize(record.id.replaceAll("-", "_")); }
    if (record.kind === "interview_plans" && !p.title) return `${kindName("interview_plans")} · ${tracks(record).map(translated).join(", ") || record.id}`;
    if (record.kind === "learning" && !p.title) return `${kindName("learning")} · ${tracks(record).map(translated).join(", ") || record.id}`;
    return scalar(p.title || p.name || p.operation || p.exercise || p.objectives || (p.type ? translated(p.type) : "") || (p.track ? translated(p.track) : "")) || record.id || t("unknownRecord");
  };
  const needsCheck = (record) => record.kind === "vacancies" && record.payload.review_status !== "rejected" && record.payload.record_type !== "lead" && (!known(record.display?.availability || record.payload.availability) || (record.display?.availability || record.payload.availability) === "conflicting");
  const status = (record) => {
    const p = record.payload;
    if (record.kind === "vacancies") return known(record.display?.availability || p.availability || p.status) || "unverified";
    if (record.kind === "companies") return isToken(p.decision) ? p.decision : known(p.status) || "unknown";
    if (record.kind === "packages") { const current = Array.isArray(p.versions) ? p.versions.find((version) => version.id === p.current_version) : null; return known(p.application_status || current?.review_status) || "unknown"; }
    if (record.kind === "source_settings") { if (p.enabled === false) return "disabled"; return known(p.health?.status) || "never_checked"; }
    if (record.kind === "assessments") return record.display?.current === false ? "superseded" : isToken(p.decision) ? p.decision : "current";
    return known(p.status || p.availability || p.review_status || (isToken(p.decision) ? p.decision : "") || p.application_status) || "unknown";
  };
  const tracks = (record) => { const value = record.payload.tracks || record.payload.target_tracks || record.payload.target_track || record.payload.track; return (Array.isArray(value) ? value : value ? [value] : []).map(scalar); };
  const dateValue = (record) => record.kind === "source_settings" ? scalar(record.payload.health?.last_attempt || "") : record.kind === "packages" && Array.isArray(record.payload.versions) ? scalar((record.payload.versions.find((version) => version.id === record.payload.current_version) || record.payload.versions.at(-1) || {}).date) : scalar(record.payload.updated_at || record.payload.finished_at || record.payload.started_at || record.payload.at || record.payload.date || record.payload.created_at || record.payload.status_checked_on || record.payload.profile_checked_on || record.payload.reviewed_on || record.payload.last_attempt || record.payload.last_seen || record.payload.first_seen);
  const formatDate = (value) => { if (!value) return ""; const date = new Date(value); return Number.isNaN(date.valueOf()) ? scalar(value) : new Intl.DateTimeFormat(state.lang === "ru" ? "ru-RU" : "en-GB", {day: "2-digit", month: "short", year: "numeric"}).format(date); };
  const companyFor = (record) => records("companies").find((company) => company.id === record.payload.company_id);
  const companyName = (record) => { const company = companyFor(record); return company ? recordTitle(company) : scalar(record.payload.company_name || record.payload.company || record.payload.company_id); };
  const geography = (record) => {
    const p = record.payload, display = record.display?.location || {}, location = p.location && typeof p.location === "object" ? p.location : {};
    let mode = display.remote || known(p.display_remote || p.work_mode);
    if (!mode && p.remote === true) mode = "remote";
    if (!mode && typeof p.remote === "string") mode = p.remote;
    const raw = scalar(display.raw || p.location);
    return {country: known(display.country || record.display_country || p.display_country || p.country || location.country) || "unknown", city: known(display.city || record.display_city || p.display_city || p.city || location.city) || "unknown", remote: mode || "unknown", raw};
  };
  const geographyValue = (value, key) => value === "unknown" ? t("unknown") : key === "country" ? countryName(value) : translated(value);
  const recordsWord = (count) => { const form = new Intl.PluralRules(state.lang).select(count); return state.lang === "ru" ? ({one: "запись", few: "записи"}[form] || "записей") : (form === "one" ? "record" : "records"); };
  const isToken = (value) => typeof value === "string" && /^[\w-]{1,40}$/.test(value.trim());
  const badge = (value) => { const tone = /^(active|open|completed|healthy|ok|approved|ready|verified|success|pass|passed|enabled|current|done|applied|match|fits_verified|accept|written)$/.test(value) ? "good" : /^(blocked|failed|needs_clarification|pending_review|partial|cooldown|fail|rejected|timeout|needs_check|never_checked|conflicting|expired_copy|unverified|conflict|mismatch|config_error|not_interested|has_questions|not_fit_mandatory|gap|insufficient_data|reject|invalid|awaiting_facts|awaiting_content_review|awaiting_visual_review)$/.test(value) ? "attention" : /^(priority|running|in_progress|product|technical-leadership|follow_up|todo|queued|queued_for_agent|pending)$/.test(value) ? "blue" : ""; return el("span", `badge ${tone}`, translated(value)); };
  function safeUrl(value) { try { const url = new URL(value); return ["http:", "https:"].includes(url.protocol) && !url.username && !url.password ? url.href : null; } catch (_) { return null; } }
  function externalLink(value, text) { const url = safeUrl(value); if (!url) return null; const link = el("a", "", text || value); link.href = url; link.target = "_blank"; link.rel = "noopener noreferrer"; return link; }
  function artifactLink(value) { const clean = String(value).replace(/^\.\//, ""); const target = state.artifacts?.has(clean) ? clean : state.artifactAliases?.get(clean); if (!target || !state.artifacts?.has(target)) return null; const link = el("a", "", value); link.href = "/api/artifacts/" + target.split("/").map(encodeURIComponent).join("/"); if (/\.(md|txt)$/i.test(target)) link.addEventListener("click", (event) => { event.preventDefault(); openDocument(target); }); return link; }
  function linksFrom(value, output = new Set(), depth = 0) { if (depth > 9 || output.size >= 30) return output; if (typeof value === "string") { if (safeUrl(value)) output.add(value); } else if (Array.isArray(value)) value.forEach((v) => linksFrom(v, output, depth + 1)); else if (value && typeof value === "object") Object.values(value).forEach((v) => linksFrom(v, output, depth + 1)); return output; }
  const filtersActive = () => Boolean(state.query.trim()) || [...new Set([...Object.keys(state.filters), ...Object.keys(defaultFilters(state.section))])].some((key) => (state.filters[key] || "") !== (defaultFilters(state.section)[key] || ""));
  const activeFilterCount = () => Object.entries(state.filters).filter(([key, value]) => (value || "") !== (defaultFilters(state.section)[key] || "")).length;
  // URL state: #section?q=…&country=…&record=kind/id — shareable, survives reload and back/forward.
  function hashFor(section, withRecord = true) {
    const params = new URLSearchParams(), defaults = defaultFilters(section);
    if (section !== "overview") { if (state.query) params.set("q", state.query); [...new Set([...Object.keys(state.filters), ...Object.keys(defaults)])].forEach((key) => { const value = state.filters[key] || ""; if (value !== (defaults[key] || "")) params.set(key, value || "all"); }); if (state.sort !== "newest") params.set("sort", state.sort); if (state.page > 1) params.set("page", String(state.page)); }
    if (withRecord && state.opened) { params.set("record", `${state.opened.kind}/${state.opened.id}`); if (state.opened.kind === "vacancies" && state.detailTab !== "vacancy") params.set("tab", state.detailTab); }
    const query = params.toString(); return `#${section}${query ? `?${query}` : ""}`;
  }
  function syncHash() { const hash = hashFor(state.section); if (location.hash !== hash) history.replaceState(null, "", hash); }
  function applyHash() {
    const raw = location.hash.slice(1), split = raw.indexOf("?"), name = split < 0 ? raw : raw.slice(0, split), params = new URLSearchParams(split < 0 ? "" : raw.slice(split + 1));
    state.section = sections.includes(name) ? name : "overview"; state.query = params.get("q") || ""; state.sort = params.get("sort") === "name" ? "name" : "newest"; state.page = Math.max(1, Number.parseInt(params.get("page") || "1", 10) || 1);
    state.filters = defaultFilters(state.section); state.detailTab = ["vacancy", "fit", "company", "resume", "prep"].includes(params.get("tab")) ? params.get("tab") : "vacancy"; ["kind", "country", "city", "remote", "status", "track", "availability", "review", "type", "freshness", "market"].forEach((key) => { if (params.has(key)) state.filters[key] = params.get(key) === "all" ? "" : params.get(key); });
    return params.get("record");
  }
  function navigate(section, preset) { if (!sections.includes(section)) section = "overview"; if (state.section !== section || preset) { state.query = ""; state.filters = {...defaultFilters(section), ...(preset || {})}; state.page = 1; state.sort = "newest"; } state.section = section; const hash = hashFor(section, false); if (location.hash !== hash) history.pushState(null, "", hash); render(); $("main").focus({preventScroll: true}); window.scrollTo(0, 0); }
  function renderChrome() {
    document.documentElement.lang = state.lang;
    document.querySelectorAll("[data-i18n]").forEach((node) => { node.textContent = t(node.dataset.i18n); });
    $("navigation").setAttribute("aria-label", state.lang === "ru" ? "Разделы" : "Sections");
    $("overview").setAttribute("aria-label", t("overview"));
    $("breadcrumb").textContent = t(state.section);
    $("language").textContent = state.lang === "ru" ? "EN" : "RU";
    $("language").setAttribute("aria-label", state.lang === "ru" ? "Switch to English" : "Переключить на русский");
    $("close-detail").setAttribute("aria-label", t("close")); $("close-document").setAttribute("aria-label", t("close"));
    $("connection").textContent = state.data ? t("connected") : "";
    $("navigation").replaceChildren(...sections.map((section, index) => { const link = el("a", `nav-link${section === state.section ? " active" : ""}`); link.href = `#${section}`; link.append(el("span", "nav-icon", icons[index]), el("span", "", t(section))); if (section !== "overview" && state.data) link.append(el("span", "nav-count", String(primaryRecords(section).length).padStart(2, "0"))); if (section === state.section) link.setAttribute("aria-current", "page"); return link; }));
    const title = el("div"); title.append(el("div", "eyebrow", `${t("privacy")} / ${t(state.section)}`), el("h1", "", state.section === "overview" ? t("overviewTitle") : t(state.section)), el("p", "", t(`${state.section}Desc`)));
    $("page-heading").replaceChildren(title, el("span", "page-index", String(sections.indexOf(state.section) + 1).padStart(2, "0")));
    document.title = state.section === "overview" ? "Career Copilot" : `${t(state.section)} · Career Copilot`;
    const journalTime = state.data?.meta?.journal_updated_at, loaded = state.loadedAt;
    $("updated-at").textContent = [journalTime ? `${t("journalUpdated")} ${formatDateTime(journalTime)}` : "", loaded ? `${t("loadedAt")} ${formatDateTime(loaded)}` : ""].filter(Boolean).join(" · ");
    $("refresh").textContent = $("refresh").disabled ? t("refreshing") : t("refresh");
    $("content-language").textContent = state.contentMode === "original" ? t("contentOriginal") : t("contentTranslated");
    $("content-language").setAttribute("aria-pressed", String(state.contentMode === "original"));
    $("content-language").title = t("contentToggleHint");
  }
  function formatDateTime(value) { const date = new Date(value); return Number.isNaN(date.valueOf()) ? scalar(value) : new Intl.DateTimeFormat(state.lang === "ru" ? "ru-RU" : "en-GB", {day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit"}).format(date); }
  function emptyState(title, description, compact = false) { const block = el("div", `empty-state${compact ? " compact" : ""}`); block.append(el("span", "eyebrow", "CAREER COPILOT"), el("h2", "", t(title)), el("p", "", t(description))); return block; }
  function render() { renderChrome(); if (!state.data) return; $("load-state").hidden = true; $("overview").hidden = state.section !== "overview"; $("collection").hidden = state.section === "overview"; if (state.section === "overview") renderOverview(); else { renderToolbar(); renderResults(); } }
  function sectionPanel(title, section) { const panel = el("section", "panel"), header = el("div", "panel-header"); header.append(el("h2", "", t(title)), button(t("viewAll"), "text-button", () => navigate(section))); panel.append(header); return panel; }
  function renderOverview() {
    const stats = el("div", "stats-grid");
    [["companies", "companyNote"], ["vacancies", "vacancyNote"], ["documents", "documentNote"], ["activities", "activityNote"]].forEach(([section, note]) => { const stat = button("", "stat", () => navigate(section)); const value = el("div", "stat-value"); value.append(el("strong", "", primaryRecords(section).length.toLocaleString(state.lang)), el("span", "", "↗")); stat.append(el("span", "stat-label", t(section)), value, el("div", "stat-note", t(note))); stats.append(stat); });
    const grid = el("div", "overview-grid"), latest = sectionPanel("recentVacancies", "vacancies");
    const seen = (record) => scalar(record.payload.first_seen || record.payload.created_at || dateValue(record));
    const recent = primaryRecords("vacancies").filter((record) => !INACTIVE.has(record.payload.availability) && record.payload.review_status !== "rejected").sort((a, b) => seen(b).localeCompare(seen(a)) || b.id.localeCompare(a.id)).slice(0, 8);
    if (!recent.length) latest.append(emptyState("noRecords", "noRecordsDesc", true));
    recent.forEach((record) => {
      const row = el("article", "opportunity"), head = el("div", "opportunity-head");
      head.append(employerLine(record), badge(status(record)));
      row.append(head, button(recordTitle(record), "record-title", () => openRecord(record)));
      const text = record.display?.description?.excerpt; if (text) row.append(el("p", "record-summary vacancy-description short", text));
      const bottom = el("div", "opportunity-bottom"); bottom.append(ageBadge(record), vacancyActions(record, {details: false}));
      row.append(bottom); latest.append(row);
    });
    const rail = el("div", "overview-rail"), focus = el("section", "focus-panel"); const unknown = primaryRecords("vacancies").filter(needsCheck).length;
    focus.append(el("div", "eyebrow", t("focus")), el("h2", "", t("focusTitle")), el("p", "", t("focusDesc")), el("div", "focus-divider"), el("span", "focus-number", String(unknown).padStart(2, "0")), el("p", "", state.lang === "ru" ? `${plural(unknown, ["вакансия требует", "вакансии требуют", "вакансий требуют", "", ""])} проверки доступности` : t("unknownAvailability")));
    if (unknown) { const links = el("div", "focus-actions"); links.append(button(t("showUnknown"), "focus-link", () => navigate("vacancies", {availability: "needs_check"}))); if (canCheck()) links.append(checkButton(() => primaryRecords("vacancies").filter(needsCheck).map((record) => record.id), `${t("checkAll")} (${unknown})`, "focus-link")); focus.append(links); }
    const due = groupedReminders(primaryRecords("vacancies")), remindersBox = sectionPanel("remindersTitle", "pipeline");
    if (due.length) due.slice(0, 4).forEach((item) => remindersBox.append(reminderRow(item))); else remindersBox.append(emptyState("noReminders", "noRemindersDesc", true));
    const actions = sectionPanel("nextSteps", "vacancies");
    // Open work first: unfinished activities, then active vacancies and followed companies with a recorded next step.
    const openActivity = (record) => record.kind === "activities" && !["completed", "failed"].includes(record.payload.status);
    const actionable = (record) => known(record.payload.next_action) && (openActivity(record) || (record.kind === "vacancies" && !INACTIVE.has(record.payload.availability) && record.payload.review_status !== "rejected" && !needsCheck(record)) || (record.kind === "companies" && ["priority", "follow_up"].includes(record.payload.decision)));
    const rank = (record) => openActivity(record) ? 0 : record.kind === "vacancies" ? 1 : 2;
    const next = [...records("activities"), ...primaryRecords("vacancies"), ...primaryRecords("companies")].filter(actionable).sort((a, b) => rank(a) - rank(b) || dateValue(b).localeCompare(dateValue(a))).slice(0, 5);
    if (!next.length) actions.append(emptyState("noActions", "noActionsDesc", true));
    next.forEach((record, index) => { const row = el("article", "action-item"), body = el("div"); body.append(button(scalar(record.payload.next_action), "record-title", () => openRecord(record))); if (record.kind === "vacancies") { const context = el("div", "action-context"); context.append(el("span", "", `${kindName(record.kind)} · `), vacancyReference(record, {compact: true})); body.append(context); } else body.append(el("p", "", `${kindName(record.kind)} · ${recordTitle(record)}`)); row.append(el("span", "action-number", String(index + 1).padStart(2, "0")), body); actions.append(row); });
    rail.append(focus, remindersBox, actions); grid.append(latest, rail);
    const strip = el("div", "summary-strip overview-section"); ["preparations", "sources", "history"].forEach((section) => { const item = button("", "", () => navigate(section)); item.append(el("span", "", `${t(section)} ↗`), el("strong", "mono", String(records(section).length).padStart(2, "0"))); strip.append(item); });
    $("overview").replaceChildren(stats, grid, strip);
  }
  const optionText = (key, value) => key === "freshness" ? t(`freshness_${value}`) : key === "type" ? (value.includes("_") || enums[value] ? translated(value) : label(value)) : key === "kind" ? label(value) : ["country", "city", "remote"].includes(key) ? geographyValue(value, key) : translated(value);
  function renderToolbar() {
    const bar = el("div", `toolbar${state.filtersOpen ? " filters-open" : ""}`), searchRow = el("div", "search-row"), searchBox = el("div", "search-box"), search = el("input"); search.type = "search"; search.id = "record-search"; search.placeholder = t("search"); search.setAttribute("aria-label", t("search")); search.setAttribute("aria-keyshortcuts", "/"); search.title = t("searchHint"); search.autocomplete = "off"; search.value = state.query; search.addEventListener("input", () => { state.query = search.value; state.page = 1; renderResults(); }); search.addEventListener("keydown", (event) => { if (event.key === "Escape" && search.value) { event.preventDefault(); search.value = ""; state.query = ""; state.page = 1; renderResults(); } }); searchBox.append(el("span", "search-symbol", "⌕"), search);
    const sort = el("select", "sort-control"); sort.setAttribute("aria-label", state.lang === "ru" ? "Сортировка" : "Sort"); [["newest", "newest"], ["name", "alphabetical"]].forEach(([value, key]) => { const option = el("option", "", t(key)); option.value = value; sort.append(option); }); sort.value = state.sort; sort.addEventListener("change", () => { state.sort = sort.value; state.page = 1; renderResults(); });
    const count = activeFilterCount(), toggle = button(count ? `${t("filters")} · ${count}` : t("filters"), "filters-toggle", () => { state.filtersOpen = !state.filtersOpen; bar.classList.toggle("filters-open", state.filtersOpen); toggle.setAttribute("aria-expanded", String(state.filtersOpen)); }); toggle.setAttribute("aria-expanded", String(state.filtersOpen)); toggle.setAttribute("aria-controls", "filter-row");
    searchRow.append(searchBox, sort, toggle); bar.append(searchRow);
    if (state.section === "vacancies") {
      const markets = el("div", "segmented"); markets.setAttribute("role", "group"); markets.setAttribute("aria-label", t("marketLabel"));
      [["", "marketAll"], ["ru", "marketRu"], ["intl", "marketIntl"], ["unknown", "marketUnknown"]].forEach(([value, key]) => {
        const count = primaryRecords("vacancies").filter((record) => !value || marketOf(record) === value).length, active = (state.filters.market || "") === value;
        const segment = button(`${t(key)} · ${count}`, `segment${active ? " active" : ""}`, () => { state.filters.market = value; state.page = 1; renderToolbar(); renderResults(); });
        segment.setAttribute("aria-pressed", String(active)); markets.append(segment);
      });
      bar.append(markets);
    }
    const row = el("div", "filter-row"), filterKeys = state.section === "vacancies" ? ["kind", "availability", "freshness", "review", "track", "country", "city", "remote"] : state.section === "pipeline" || state.section === "resume" ? ["track"] : state.section === "companies" ? ["kind", "country", "city", "status", "track"] : state.section === "history" ? ["type"] : state.section === "sources" ? [] : state.section === "preparations" ? ["kind", "track"] : ["kind", "status", "track"]; row.id = "filter-row";
    filterKeys.forEach((key) => {
      const wrapper = el("label", "filter-control"), select = el("select"); select.id = `filter-${key}`; wrapper.append(el("span", "", key === "kind" ? label("type") : key === "availability" ? t("availabilityFilter") : key === "review" ? label("review_status") : key === "type" ? t("eventType") : key === "freshness" ? t("freshnessFilter") : t(key)));
      // Facet options come from records matching the other active filters, so a choice never leads to an empty list.
      const values = new Set(), others = Object.entries(state.filters).filter(([other, value]) => other !== key && value);
      records(state.section).filter((record) => others.every(([other, value]) => filterValues(record, other).includes(value))).forEach((record) => filterValues(record, key).forEach((v) => values.add(v)));
      if (state.filters[key]) values.add(state.filters[key]);
      const all = el("option", "", t("all")); all.value = ""; select.append(all);
      [...values].sort((a, b) => (a === "unknown") - (b === "unknown") || optionText(key, a).localeCompare(optionText(key, b), state.lang)).forEach((value) => { const option = el("option", "", optionText(key, value)); option.value = value; select.append(option); });
      select.value = state.filters[key] || ""; select.addEventListener("change", () => { state.filters[key] = select.value; state.page = 1; renderToolbar(); renderResults(); $(`filter-${key}`)?.focus(); }); wrapper.append(select); row.append(wrapper);
    });
    const reset = button(t("reset"), "reset-button", resetFilters); reset.disabled = !filtersActive(); row.append(reset); if (filterKeys.length) bar.append(row); else { sort.hidden = true; toggle.hidden = true; } $("toolbar").replaceChildren(bar);
  }
  function resetFilters() { state.query = ""; state.filters = defaultFilters(state.section); state.page = 1; renderToolbar(); renderResults(); $("record-search")?.focus(); }
  function filterValues(record, key) { if (key === "kind") return [record.kind]; if (key === "market") return [record.kind === "vacancies" ? marketOf(record) : "unknown"]; if (["country", "city", "remote"].includes(key)) return [geography(record)[key]]; if (key === "track") return tracks(record).length ? tracks(record) : ["unknown"]; if (key === "freshness") return [record.kind === "vacancies" ? freshness(record) : "never"]; if (key === "type") return [record.kind === "events" ? known(record.payload.type) || "unknown" : record.kind]; if (key === "review") return [known(record.payload.review_status) || "unknown"]; if (key === "availability") { const value = known(record.display?.availability || record.payload.availability) || "unknown"; return needsCheck(record) ? [value, "needs_check"] : [value]; } return [status(record)]; }
  function renderResults() {
    const query = state.query.trim().toLocaleLowerCase(state.lang);
    const filtered = records(state.section).filter((record) => (!query || `${recordTitle(record)} ${companyName(record)} ${JSON.stringify(record.payload)}`.toLocaleLowerCase(state.lang).includes(query)) && Object.entries(state.filters).every(([key, value]) => !value || filterValues(record, key).includes(value)));
    filtered.sort(state.sort === "name" ? (a, b) => recordTitle(a).localeCompare(recordTitle(b), state.lang) : (a, b) => dateValue(b).localeCompare(dateValue(a)) || recordTitle(a).localeCompare(recordTitle(b), state.lang));
    const totalPages = Math.max(1, Math.ceil(filtered.length / state.pageSize)); state.page = Math.min(state.page, totalPages);
    const active = filtersActive(), reset = document.querySelector(".reset-button"); if (reset) reset.disabled = !active;
    $("results-heading").replaceChildren(el("span", "", `${t("found")}: ${filtered.length.toLocaleString(state.lang)} ${recordsWord(filtered.length)}`), el("span", "", active ? t("activeFilters") : `${String(sections.indexOf(state.section) + 1).padStart(2, "0")} / ${t(state.section)}`));
    if (["sources", "resume", "preparations"].includes(state.section) || (filtered.length && ["history", "pipeline"].includes(state.section))) {
      $("results").replaceChildren(state.section === "resume" ? renderResume(filtered) : state.section === "sources" ? renderSources(filtered) : state.section === "history" ? renderHistory(filtered) : state.section === "pipeline" ? renderPipeline(filtered) : renderPreparationModule(filtered));
      $("pagination").replaceChildren(); renderFiles(); syncHash(); return;
    }
    if (!filtered.length) { const block = emptyState(records(state.section).length ? "noResults" : "noRecords", records(state.section).length ? "noResultsDesc" : "noRecordsDesc"); if (records(state.section).length && active) block.append(button(t("reset"), "primary-button", resetFilters)); $("results").replaceChildren(block); } else { const grid = el("div", "records-grid"); filtered.slice((state.page - 1) * state.pageSize, state.page * state.pageSize).forEach((record) => grid.append(recordCard(record))); $("results").replaceChildren(grid); }
    $("pagination").replaceChildren();
    if (totalPages > 1) { const turn = (delta) => { state.page += delta; renderResults(); $("results-heading").scrollIntoView({block: "start"}); }, previous = button(t("previous"), "", () => turn(-1)), next = button(t("next"), "", () => turn(1)); previous.disabled = state.page === 1; next.disabled = state.page === totalPages; $("pagination").append(previous, el("span", "", `${t("page")} ${state.page} ${t("of")} ${totalPages}`), next); }
    renderFiles();
    syncHash();
  }
  function renderFiles() {
    let panel = $("files-panel");
    if (state.section !== "documents" || !state.artifacts?.size) { if (panel) panel.hidden = true; return; }
    if (!panel) { panel = el("details", "files-panel"); panel.id = "files-panel"; $("collection").append(panel); }
    const groups = new Map(); [...state.artifacts].sort((a, b) => a.localeCompare(b)).forEach((path) => { const root = path.split("/")[0]; if (!groups.has(root)) groups.set(root, []); groups.get(root).push(path); });
    const summary = el("summary"); summary.append(el("span", "", t("files")), el("span", "mono", String(state.artifacts.size)));
    const body = el("div", "files-body"); body.append(el("p", "muted", t("filesDesc")));
    groups.forEach((paths, root) => { const group = el("section", "files-group"), list = el("ul", "files-list"); group.append(el("h3", "eyebrow", `${root} · ${paths.length}`)); paths.forEach((path) => { const item = el("li"), link = el("a", "", path.slice(root.length + 1)); link.href = "/api/artifacts/" + path.split("/").map(encodeURIComponent).join("/"); if (/\.(md|txt)$/i.test(path)) link.addEventListener("click", (event) => { event.preventDefault(); openDocument(path); }); item.append(link); list.append(item); }); group.append(list); body.append(group); });
    const open = panel.open; panel.replaceChildren(summary, body); panel.open = open; panel.hidden = false;
  }
  function geographyBlock(record) { const block = el("div", "geography"), geo = geography(record); ["country", "city", "remote"].forEach((key) => { const item = el("div", `geo-item${geo[key] === "unknown" ? " is-unknown" : ""}`); item.append(el("span", "", t(key)), el("strong", "", geographyValue(geo[key], key))); block.append(item); }); return block; }
  function recordCard(record) {
    if (record.kind === "vacancies") return vacancyCard(record);
    const p = record.payload, card = el("article", "record-card"), top = el("div", "card-top"), titleArea = el("div");
    const subtitle = state.section === "vacancies" ? companyName(record) : record.kind === (defaultFilters(state.section).kind || kinds[state.section]) ? "" : label(record.kind);
    if (subtitle) titleArea.append(el("p", "company-label", subtitle));
    titleArea.append(button(recordTitle(record), "record-title", () => openRecord(record))); top.append(titleArea); if (status(record) !== "unknown" || record.kind === "vacancies") top.append(badge(status(record))); card.append(top);
    const summary = scalar(p.about || p.description || p.summary || p.next_action || p.note || p.findings || p.objectives || p.reason || p.business_areas);
    if (summary) card.append(el("p", "record-summary", summary));
    const meta = el("div", "card-meta"); tracks(record).forEach((track) => meta.append(badge(track))); const decision = known(p.decision);
    if (decision && decision !== status(record) && isToken(decision)) meta.append(badge(decision));
    else if (decision && decision !== status(record) && decision !== summary) { const note = el("p", "record-decision"); note.append(el("span", "", `${t("decisionNote")}: `), document.createTextNode(decision)); card.append(note); }
    if (state.section === "companies" && p.size) { const sizeValue = typeof p.size === "object" ? known(p.size.value) : known(p.size); if (sizeValue) { const size = typeof p.size === "object" ? [typeof p.size.value === "number" ? p.size.value.toLocaleString(state.lang) : sizeValue, known(p.size.metric) ? translated(p.size.metric) : ""].filter(Boolean).join(" ") : sizeValue; meta.append(el("span", "badge", `${t("size")}: ${size}`)); } }
    if (Array.isArray(p.versions)) meta.append(el("span", "badge", `${t("versions")}: ${p.versions.length}`));
    if (record.kind === "packages" && Array.isArray(p.versions)) { const current = p.versions.find((version) => version.id === p.current_version); if (current) { const review = badge(current.review_status || "unknown"); review.textContent = `${label("review_status")}: ${translated(current.review_status || "unknown")}`; meta.append(review); } }
    if (p.actor?.model) meta.append(el("span", "badge", p.actor.model));
    if (meta.childElementCount) card.append(meta);
    if (["companies", "vacancies"].includes(state.section) && (state.section === "vacancies" || Object.entries(geography(record)).some(([key, value]) => key !== "raw" && value !== "unknown"))) card.append(geographyBlock(record));
    if (record.kind === "packages" && p.vacancy_id && p.vacancy_id !== "master") { const vacancy = byId(p.vacancy_id, "vacancies"); if (vacancy) { const line = el("div", "card-vacancy"); line.append(vacancyReference(vacancy, {compact: true})); card.append(line); } }
    if (record.kind === "companies") { const own = companyVacancies(record); if (own.length) { const box = el("div", "card-vacancy"); box.append(el("p", "company-label", `${label("vacancies")} · ${own.length}`)); own.slice(0, 3).forEach((vacancy) => box.append(vacancyReference(vacancy, {compact: true, company: false}))); if (own.length > 3) box.append(button(`+${own.length - 3} ${t("more")}`, "text-button", () => openRecord(record))); card.append(box); } }
    const footer = el("div", "card-footer"), stamp = record.kind === "vacancies" ? seenDate(record) : dateValue(record), prefix = record.kind === "vacancies" ? `${t("foundLabel")} ` : record.kind === "packages" ? `${t("versionFrom")} ` : "";
    footer.append(el("span", "", formatDate(stamp) ? `${prefix}${formatDate(stamp)}` : t("noDate")));
    if (record.kind === "vacancies") { const link = postingLink(record); if (link) footer.append(link); const age = el("div", "card-age"); age.append(ageBadge(record)); if (canCheck() && !inactiveVacancy(record)) age.append(checkButton([record.id])); card.append(age); } else { const firstUrl = [...linksFrom(p.urls || p.url || p.profile_sources || p.source_url || [])][0]; if (firstUrl) footer.append(externalLink(firstUrl, t("original"))); }
    footer.append(button(`${t("open")} →`, "text-button", () => openRecord(record))); card.append(footer); return card;
  }
  // ---------------------------------------------------------------------------
  // Vacancy references: title, company, found date, availability and posting link together.
  // ---------------------------------------------------------------------------
  const vacancyUrl = (record) => [...linksFrom(record.payload.urls || record.payload.url || record.payload.posting || [])][0];
  const seenDate = (record) => scalar(record.payload.first_seen || record.payload.created_at || "");
  const plural = (count, forms) => { const form = new Intl.PluralRules(state.lang).select(count); return state.lang === "ru" ? ({one: forms[0], few: forms[1]}[form] || forms[2]) : (form === "one" ? forms[3] : forms[4]); };
  function postingLink(record, text) {
    const url = vacancyUrl(record); if (!url) return null;
    const link = externalLink(url, text || `${t("openPosting")} ↗`); link.classList.add("posting-link");
    if (!text || text === "↗") link.setAttribute("aria-label", `${t("openPosting")}: ${recordTitle(record)}`);
    return link;
  }
  function vacancyReference(record, {date = true, compact = false, company = true} = {}) {
    const wrap = el("span", `vacancy-ref${compact ? " compact" : ""}`);
    wrap.append(button(recordTitle(record), "record-reference", () => openRecord(record)));
    const found = date && seenDate(record) ? `${t("foundOn")} ${formatDate(seenDate(record))}` : "";
    const meta = [company ? companyName(record) : "", found].filter(Boolean).join(" · ");
    if (meta) wrap.append(el("span", "vacancy-ref-meta", meta));
    wrap.append(badge(status(record)));
    const link = postingLink(record, `${t("postingShort")} ↗`); if (link) { link.setAttribute("aria-label", `${t("openPosting")}: ${recordTitle(record)}`); wrap.append(link); }
    return wrap;
  }
  function recordReference(record) {
    if (record.kind === "vacancies") return vacancyReference(record, {compact: true});
    const title = recordTitle(record), prefix = title.startsWith(kindName(record.kind)) ? "" : `${kindName(record.kind)} · `;
    return button(`${prefix}${title}`, "record-reference", () => openRecord(record));
  }
  const companyVacancies = (company) => primaryRecords("vacancies").filter((record) => record.payload.company_id === company.id);

  // ---------------------------------------------------------------------------
  // Safe Markdown → DOM (headings, paragraphs, lists, pipe tables, **bold**, `code`, links).
  // Text only enters the page through text nodes; relative links stay plain text.
  // ---------------------------------------------------------------------------
  function inlineMarkdown(text) {
    const fragment = document.createDocumentFragment();
    String(text).split(/(\*\*[^*]+\*\*|`[^`]+`|\[[^\]]+\]\([^)\s]+\))/).forEach((part) => {
      if (!part) return;
      if (part.startsWith("**") && part.endsWith("**") && part.length > 4) { const strong = el("strong"); strong.append(inlineMarkdown(part.slice(2, -2))); fragment.append(strong); }
      else if (part.startsWith("`") && part.endsWith("`") && part.length > 2) fragment.append(el("code", "", part.slice(1, -1)));
      else { const link = part.match(/^\[([^\]]+)\]\(([^)\s]+)\)$/); if (link) fragment.append(externalLink(link[2], link[1]) || el("span", "", link[1])); else fragment.append(document.createTextNode(part)); }
    });
    return fragment;
  }
  function renderMarkdown(text) {
    const root = el("div", "markdown"), lines = String(text).replace(/\r\n/g, "\n").split("\n"); let paragraph = [];
    const flush = () => { if (paragraph.length) { const p = el("p"); p.append(inlineMarkdown(paragraph.join(" "))); root.append(p); paragraph = []; } };
    for (let index = 0; index < lines.length; index++) {
      const line = lines[index], stripped = line.trim(), heading = stripped.match(/^(#{1,6})\s+(.*)$/);
      if (!stripped) { flush(); continue; }
      if (heading) { flush(); const node = el(`h${Math.min(heading[1].length + 2, 6)}`); node.append(inlineMarkdown(heading[2])); root.append(node); continue; }
      if (stripped.startsWith("|")) {
        flush(); const rows = [];
        while (index < lines.length && lines[index].trim().startsWith("|")) { const cells = lines[index].trim().replace(/^\||\|$/g, "").split("|").map((cell) => cell.trim()); if (!cells.every((cell) => !cell || /^:?-{3,}:?$/.test(cell))) rows.push(cells); index++; }
        index--; root.append(tableFrom(rows)); continue;
      }
      if (/^([-*]|\d+\.)\s+/.test(stripped)) {
        flush(); const ordered = /^\d+\./.test(stripped), marker = ordered ? /^\s*\d+\.\s+/ : /^\s*[-*]\s+/, list = el(ordered ? "ol" : "ul");
        while (index < lines.length && marker.test(lines[index])) { const item = el("li"); item.append(inlineMarkdown(lines[index].replace(/^\s*([-*]|\d+\.)\s+/, ""))); list.append(item); index++; }
        index--; root.append(list); continue;
      }
      paragraph.push(stripped);
    }
    flush(); return root;
  }
  function tableFrom(rows, header = true) {
    const scroll = el("div", "table-scroll"), table = el("table", "plan-table");
    rows.forEach((cells, rowIndex) => { const tr = el("tr"); cells.forEach((cell) => { const td = el(header && rowIndex === 0 ? "th" : "td"); if (cell instanceof Node) td.append(cell); else td.append(inlineMarkdown(cell)); tr.append(td); }); (header && rowIndex === 0 ? (table.tHead || table.createTHead()) : (table.tBodies[0] || table.createTBody())).append(tr); });
    scroll.append(table); return scroll;
  }
  const textCache = new Map();
  async function artifactText(path) {
    if (!textCache.has(path)) textCache.set(path, fetch("/api/text/" + path.split("/").map(encodeURIComponent).join("/"), {cache: "no-store", credentials: "same-origin"}).then((response) => { if (!response.ok) throw new Error("text unavailable"); return response.text(); }));
    try { return await textCache.get(path); } catch (error) { textCache.delete(path); throw error; }
  }

  // ---------------------------------------------------------------------------
  // Preparation: complete plans on the page, with PDF and Markdown downloads.
  // ---------------------------------------------------------------------------
  function factList(entries) {
    const list = el("dl", "plan-facts");
    entries.filter(([, value]) => value !== null && value !== undefined && value !== "").forEach(([name, value]) => { const row = el("div"); const dd = el("dd"); dd.append(value instanceof Node ? value : document.createTextNode(String(value))); row.append(el("dt", "", name), dd); list.append(row); });
    return list;
  }
  function planShell(record, open) {
    const article = el("article", `plan${record.display?.current === false ? " is-superseded" : ""}`); article.dataset.recordId = record.id; const header = el("header", "plan-header"), heading = el("div", "plan-heading");
    heading.append(el("p", "eyebrow", kindName(record.kind)), el("h2", "plan-title", recordTitle(record)));
    const meta = el("div", "card-meta"); tracks(record).forEach((track) => meta.append(badge(track))); if (record.display?.current === false) meta.append(badge("superseded")); else if (record.kind === "learning") meta.append(badge("current"));
    if (meta.childElementCount) heading.append(meta);
    const actions = el("div", "plan-actions"), pdf = el("a", "primary-button", t("downloadPdf"));
    pdf.href = `/api/plans/${encodeURIComponent(record.kind)}/${encodeURIComponent(record.id)}.pdf${state.lang === "en" ? "?lang=en" : ""}`; pdf.setAttribute("download", "");
    actions.append(pdf, button(t("openRecord"), "quiet-button", () => openRecord(record)));
    header.append(heading, actions);
    const body = el("details", "plan-body"); body.open = open; body.append(el("summary", "", t("showPlan")));
    article.append(header, body); return {article, body};
  }
  function learningPlan(record, open) {
    const p = record.payload, {article, body} = planShell(record, open), vacancy = byId(p.vacancy_id, "vacancies");
    const weeks = Array.isArray(p.weeks) ? p.weeks.filter((week) => week && typeof week === "object") : [], gaps = Array.isArray(p.gaps) ? p.gaps.filter((gap) => gap && typeof gap === "object") : [];
    article.insertBefore(factList([
      [kindName("vacancies"), vacancy ? vacancyReference(vacancy) : (p.vacancy_id ? String(p.vacancy_id) : "")],
      [t("createdOn"), formatDateTime(p.created_at)],
      [label("hours_per_week"), p.hours_per_week ? (weeks.length ? `${p.hours_per_week} ${t("hoursShort")} × ${weeks.length} ${t("weeksShort")} = ${p.hours_per_week * weeks.length} ${t("hoursShort")}` : `${p.hours_per_week} ${t("hoursShort")}`) : ""],
      [label("interview_date"), p.interview_date ? formatDate(p.interview_date) : t("notScheduled")],
      [t("gapsTitle"), gaps.length ? `${gaps.length} · ${t("mandatoryShort")}: ${gaps.filter((gap) => gap.mandatory === true).length}` : ""],
    ]), body);
    if (p.warning) body.append(el("p", "detail-warning", scalar(p.warning)));
    if (weeks.length) { body.append(el("h3", "plan-section-title", t("weeksTitle"))); body.append(tableFrom([[label("week"), t("focusColumn"), label("deliverable"), label("status")], ...weeks.map((week) => [String(week.week ?? ""), scalar(week.focus), scalar(week.deliverable), badge(known(week.status) || "unknown")])])); }
    if (gaps.length) {
      body.append(el("h3", "plan-section-title", t("gapsTitle")));
      const list = el("ol", "gap-list");
      gaps.forEach((gap) => {
        const item = el("li", "gap"), head = el("div", "gap-head"); head.append(el("strong", "", scalar(gap.text)));
        const badges = el("div", "card-meta"); if (gap.gap_type) badges.append(badge(gap.gap_type)); if (gap.mandatory === true) badges.append(el("span", "badge attention", label("mandatory"))); badges.append(badge(known(gap.status) || "unknown")); head.append(badges); item.append(head);
        const vacancies = (Array.isArray(gap.vacancy_ids) ? gap.vacancy_ids : []).map((id) => byId(id, "vacancies")).filter(Boolean);
        const resources = Array.isArray(gap.resources) && gap.resources.length ? renderValue(gap.resources, "resources") : "";
        const linked = vacancies.length ? (() => { const box = el("div", "stacked-refs"); vacancies.forEach((vacancy) => box.append(vacancyReference(vacancy, {date: false, compact: true}))); return box; })() : "";
        item.append(factList([[label("next_action"), scalar(gap.next_action)], [label("done_requires"), scalar(gap.done_requires)], [label("resources"), resources], [label("vacancy_ids"), linked]]));
        list.append(item);
      });
      body.append(list);
    }
    if (Array.isArray(p.shared) && p.shared.length) { body.append(el("h3", "plan-section-title", label("shared"))); const list = el("ul", "plain-list"); p.shared.forEach((item) => list.append(el("li", "", scalar(item)))); body.append(list); }
    return article;
  }
  function interviewPlan(record, open, sharedTracks) {
    const p = record.payload, {article, body} = planShell(record, open), activity = byId(p.activity_id, "activities"), path = p.plan && typeof p.plan.path === "string" ? p.plan.path : "";
    article.insertBefore(factList([[t("createdOn"), formatDateTime(p.created_at)], [kindName("activities"), activity ? recordReference(activity) : ""], [label("model"), scalar(p.actor?.model)], [label("objectives"), Array.isArray(p.objectives) ? String(p.objectives.length) : ""]]), body);
    if (Array.isArray(p.objectives) && p.objectives.length) { body.append(el("h3", "plan-section-title", label("objectives"))); const list = el("ol", "plain-list"); p.objectives.forEach((item) => list.append(el("li", "", scalar(item)))); body.append(list); }
    if (path) {
      const title = el("div", "plan-section-row"); title.append(el("h3", "plan-section-title", t("detailedPlan"))); const markdownLink = artifactLink(path); if (markdownLink) { markdownLink.textContent = t("downloadMarkdown"); markdownLink.className = "quiet-button"; title.append(markdownLink); }
      body.append(title);
      if (sharedTracks.length > 1) body.append(el("p", "muted", `${t("sharedPlanNote")}: ${sharedTracks.map(translated).join(", ")}.`));
      const holder = el("div", "markdown-holder"); holder.append(el("p", "muted", t("planLoading"))); body.append(holder);
      const fill = () => { if (holder.dataset.loaded) return; holder.dataset.loaded = "1"; artifactText(path).then((text) => holder.replaceChildren(renderMarkdown(text))).catch(() => { delete holder.dataset.loaded; holder.replaceChildren(el("p", "detail-warning", t("planUnavailable"))); }); };
      if (body.open) fill(); body.addEventListener("toggle", () => { if (body.open) fill(); });
    }
    return article;
  }
  function renderPreparations(list) {
    const container = el("div", "plans"), plans = list.filter((record) => ["learning", "interview_plans"].includes(record.kind)), others = list.filter((record) => !plans.includes(record) && !PREP_KINDS.has(record.kind));
    const superseded = plans.filter((record) => record.display?.current === false), visible = state.showSuperseded ? plans : plans.filter((record) => record.display?.current !== false);
    const order = (record) => (record.kind === "interview_plans" ? 0 : 1) + (record.display?.current === false ? 2 : 0);
    const paths = new Map(); plans.filter((record) => record.kind === "interview_plans").forEach((record) => { const path = record.payload.plan?.path; if (path) paths.set(path, [...(paths.get(path) || []), ...tracks(record)]); });
    const opened = new Set();
    [...visible].sort((a, b) => order(a) - order(b) || tracks(a).join().localeCompare(tracks(b).join())).forEach((record, index) => {
      if (record.kind === "learning") container.append(learningPlan(record, index === 0));
      else { const path = record.payload.plan?.path, first = path && !opened.has(path); if (path) opened.add(path); container.append(interviewPlan(record, index === 0 && first, paths.get(path) || [])); }
    });
    if (superseded.length) container.append(button(state.showSuperseded ? t("hideSuperseded") : `${t("showSuperseded")} (${superseded.length})`, "quiet-button plans-toggle", () => { state.showSuperseded = !state.showSuperseded; renderResults(); }));
    if (others.length) { const grid = el("div", "records-grid"); others.forEach((record) => grid.append(recordCard(record))); container.append(grid); }
    return container;
  }

  // ---------------------------------------------------------------------------
  // Sources: configured collectors plus every website referenced by the journal.
  // ---------------------------------------------------------------------------
  const boardUrl = (p) => p.provider === "greenhouse" && p.board ? `https://job-boards.greenhouse.io/${encodeURIComponent(p.board)}` : p.provider === "lever" && p.board ? `https://jobs.lever.co/${encodeURIComponent(p.board)}` : "";
  function scheduleText(seconds) { const value = Number(seconds); if (!value) return ""; if (value % 86400 === 0) return value === 86400 ? t("daily") : `${t("every")} ${value / 86400} ${plural(value / 86400, ["день", "дня", "дней", "day", "days"])}`; return `${t("every")} ${Math.round(value / 3600)} ${state.lang === "ru" ? "ч" : "h"}`; }
  function sourceCard(record) {
    const p = record.payload, health = record.kind === "source_health" ? p : p.health || {}, card = el("article", "record-card source-card"), top = el("div", "card-top"), titleArea = el("div");
    titleArea.append(el("p", "company-label", p.provider ? translated(p.provider) : kindName(record.kind)), button(recordTitle(record), "record-title", () => openRecord(record))); top.append(titleArea, badge(status(record))); card.append(top);
    card.append(factList([[label("market"), p.market ? translated(p.market) : ""], [t("schedule"), p.enabled === false ? translated("disabled") : scheduleText(p.interval_seconds)], [t("lastCheck"), health.last_attempt ? formatDateTime(health.last_attempt) : t("never")], [t("nextCheck"), health.next_attempt && p.enabled !== false ? formatDateTime(health.next_attempt) : ""], [t("foundCount"), health.count ?? ""], [t("titleFilter"), scalar(p.include_title)], [t("sourceProblem"), [health.failure_status || (health.status && !String(health.status).startsWith("success") && !["never_checked", "cooldown"].includes(health.status) ? translated(health.status) : ""), health.http_status && !String(health.status).startsWith("success") ? `HTTP ${health.http_status}` : "", scalar(health.config_error)].filter(Boolean).join(" · ")], [t("lastSuccess"), health.last_attempt ? (health.last_success ? formatDateTime(health.last_success) : t("never")) : ""]]));
    const links = el("div", "detail-links"); [...new Set([p.source_verified_url, boardUrl(p)].filter(Boolean))].forEach((url) => { const link = externalLink(url, `${new URL(url).hostname.replace(/^www\./, "")} ↗`); if (link) links.append(link); });
    if (links.childElementCount) card.append(links); else card.append(el("p", "muted small-note", t("noSourceLink")));
    return card;
  }
  function sourceCatalog(query) {
    const hosts = new Map(), sectionsWithLinks = ["vacancies", "companies", "documents", "activities", "preparations", "history"];
    sectionsWithLinks.forEach((section) => records(section).forEach((record) => {
      if (record.display?.current === false) return;
      linksFrom(record.payload, new Set()).forEach((url) => {
        let host; try { host = new URL(url).hostname.replace(/^www\./, ""); } catch (_) { return; }
        if (!hosts.has(host)) hosts.set(host, {host, kinds: new Set(), records: new Set(), links: []});
        const entry = hosts.get(host); entry.kinds.add(record.kind); entry.records.add(record); if (!entry.links.some((link) => link.url === url && link.record === record)) entry.links.push({url, record});
      });
    }));
    const needle = query.trim().toLocaleLowerCase(state.lang);
    return [...hosts.values()].filter((entry) => !needle || entry.host.includes(needle) || [...entry.records].some((record) => `${recordTitle(record)} ${companyName(record)}`.toLocaleLowerCase(state.lang).includes(needle))).sort((a, b) => b.records.size - a.records.size || a.host.localeCompare(b.host));
  }
  function renderSources(list) {
    const container = el("div", "sources-view"), configured = el("section", "view-section");
    configured.append(el("h2", "view-title", t("configuredSources")), el("p", "muted", t("configuredSourcesDesc")));
    if (list.length) { const grid = el("div", "records-grid source-grid"); list.forEach((record) => grid.append(sourceCard(record))); configured.append(grid); } else configured.append(emptyState("noResults", "noResultsDesc", true));
    const catalog = sourceCatalog(state.query), all = el("section", "view-section");
    all.append(el("h2", "view-title", `${t("dataSources")} · ${catalog.length}`), el("p", "muted", t("dataSourcesDesc")));
    if (catalog.length) {
      const rows = [[t("sourceHost"), t("sourceUse"), t("sourceRecords"), t("sourceLinks")]];
      catalog.forEach((entry) => {
        const host = externalLink(`https://${entry.host}`, entry.host) || el("span", "", entry.host);
        const details = el("details", "link-details"), summary = el("summary", "", `${entry.links.length} ${plural(entry.links.length, ["ссылка", "ссылки", "ссылок", "link", "links"])}`), items = el("ul", "plain-list");
        entry.links.slice(0, 200).forEach(({url, record}) => { const item = el("li", "catalog-link"); item.append(externalLink(url, url.replace(/^https?:\/\/(www\.)?/, "").slice(0, 90)), button(recordTitle(record), "record-reference", () => openRecord(record)), el("span", "muted", [kindName(record.kind), record.kind === "vacancies" ? companyName(record) : ""].filter(Boolean).join(" · "))); items.append(item); });
        details.append(summary, items);
        rows.push([host, [...entry.kinds].map((kind) => label(kind)).join(", "), String(entry.records.size), details]);
      });
      all.append(tableFrom(rows));
    } else all.append(emptyState("noResults", "noResultsDesc", true));
    container.append(collectionView(), campaignsView(), configured, workView(), all); return container;
  }

  // ---------------------------------------------------------------------------
  // History: a timeline grouped by day, with times, readable summaries and linked records.
  // ---------------------------------------------------------------------------
  const eventStamp = (record) => scalar(record.payload.at || record.payload.date || record.payload.created_at || record.payload.finished_at || "");
  function dayKey(value) { if (/^\d{4}-\d{2}-\d{2}$/.test(value)) return value; const date = new Date(value); if (Number.isNaN(date.valueOf())) return "unknown"; return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`; }
  function eventSummary(record) {
    const p = record.payload, d = p.details && typeof p.details === "object" ? p.details : {}, parts = [];
    if (p.note) return scalar(p.note);
    if (record.kind === "imports") { const counts = p.counts && typeof p.counts === "object" ? Object.entries(p.counts).map(([key, value]) => `${label(key)}: ${value}`).join(", ") : ""; return [counts, p.files ? `${label("files")}: ${p.files}` : ""].filter(Boolean).join(" · "); }
    if (d.assessment_id) { const assessment = byId(d.assessment_id, "assessments"); if (assessment) parts.push(`${kindName("assessments")}: ${tracks(assessment).map(translated).join(", ")}${assessment.display?.current === false ? ` (${t("superseded")})` : ""}`); }
    if (d.plan_id) { const plan = byId(d.plan_id); if (plan) parts.push(recordTitle(plan)); }
    if (d.skill || d.operation) parts.push([scalar(d.skill), scalar(d.operation)].filter(Boolean).join(" · "));
    if (d.status) parts.push(`${label("status")}: ${translated(scalar(d.status))}`);
    if (d.version_id) parts.push(`${label("version_id")}: ${scalar(d.version_id)}`);
    if (d.review) parts.push(`${label("review")}: ${translated(scalar(typeof d.review === "object" ? d.review.status || d.review.verdict || d.review.result : d.review))}`);
    if (d.model) parts.push(`${label("model")}: ${scalar(d.model)}`);
    if (d.counts && typeof d.counts === "object") parts.push(Object.entries(d.counts).map(([key, value]) => `${label(key)}: ${value}`).join(", "));
    if (d.file_count) parts.push(`${label("file_count")}: ${d.file_count}`);
    if (d.fact_count) parts.push(`${label("fact_count")}: ${d.fact_count}`);
    if (d.next_action) parts.push(`${label("next_action")}: ${scalar(d.next_action)}`);
    if (d.before && d.after) parts.push(t("recordChanged"));
    return parts.filter(Boolean).join(" · ");
  }
  function entityChips(ids) {
    const box = el("div", "chips"), resolved = (Array.isArray(ids) ? ids : []).map((id) => byId(String(id)) || String(id)), limit = 6;
    const add = (items) => items.forEach((item) => box.append(typeof item === "string" ? el("span", "chip muted mono", item) : recordReference(item)));
    add(resolved.slice(0, limit));
    if (resolved.length > limit) { const more = button(`+${resolved.length - limit} ${t("more")}`, "chip more", () => { more.remove(); add(resolved.slice(limit)); }); box.append(more); }
    return box;
  }
  function renderHistory(list) {
    const timeline = el("div", "timeline"), days = new Map();
    [...list].sort((a, b) => eventStamp(b).localeCompare(eventStamp(a))).forEach((record) => { const key = dayKey(eventStamp(record)); if (!days.has(key)) days.set(key, []); days.get(key).push(record); });
    days.forEach((items, key) => {
      const day = el("section", "timeline-day"), heading = el("h2", "timeline-date");
      heading.append(document.createTextNode(key === "unknown" ? t("noDate") : new Intl.DateTimeFormat(state.lang === "ru" ? "ru-RU" : "en-GB", {weekday: "long", day: "numeric", month: "long", year: "numeric"}).format(new Date(`${key}T12:00:00`))), el("span", "mono muted", `${items.length} ${plural(items.length, ["событие", "события", "событий", "event", "events"])}`));
      day.append(heading);
      items.forEach((record) => {
        const p = record.payload, stamp = eventStamp(record), item = el("article", "timeline-item"), hasTime = /T\d{2}:\d{2}/.test(stamp);
        item.append(el("time", "timeline-time mono", hasTime ? new Intl.DateTimeFormat(state.lang === "ru" ? "ru-RU" : "en-GB", {hour: "2-digit", minute: "2-digit"}).format(new Date(stamp)) : t("noTime")));
        item.lastChild.dateTime = stamp;
        const body = el("div", "timeline-body"), top = el("div", "timeline-top");
        top.append(button(recordTitle(record), "record-title", () => openRecord(record))); if (record.kind !== "events") top.append(el("span", "badge", kindName(record.kind)));
        body.append(top);
        const summary = eventSummary(record); if (summary) body.append(el("p", "timeline-summary", summary));
        if (Array.isArray(p.entity_ids) && p.entity_ids.length) body.append(entityChips(p.entity_ids));
        item.append(body); day.append(item);
      });
      timeline.append(day);
    });
    return timeline;
  }
  // ---------------------------------------------------------------------------
  // Data age: when a vacancy's availability was last checked, with stale highlighting.
  // ---------------------------------------------------------------------------
  const DAY_MS = 86400000;
  // Calendar days in the viewer's time zone, so "yesterday" means the previous date, not 24 hours.
  const daysSince = (value) => { if (!value) return null; const date = new Date(/^\d{4}-\d{2}-\d{2}$/.test(value) ? `${value}T00:00:00` : value); if (Number.isNaN(date.valueOf())) return null; const start = new Date(date.getFullYear(), date.getMonth(), date.getDate()), today = new Date(); return Math.max(0, Math.round((new Date(today.getFullYear(), today.getMonth(), today.getDate()) - start) / DAY_MS)); };
  const relativeDays = (days) => new Intl.RelativeTimeFormat(state.lang === "ru" ? "ru" : "en", {numeric: "auto"}).format(-days, "day");
  const checkedAt = (record) => record.display?.checked_at || record.payload.status_checked_on || null;
  function freshness(record) { const days = daysSince(checkedAt(record)); return days === null ? "never" : days <= 7 ? "fresh" : days <= 14 ? "aging" : "stale"; }
  function ageBadge(record) {
    const days = daysSince(checkedAt(record)), bucket = freshness(record);
    const undetermined = (record.display?.availability_check || record.payload.availability_check)?.status === "unknown";
    const text = days === null ? `${t("neverChecked")}${daysSince(seenDate(record)) !== null ? ` · ${t("foundOn")} ${relativeDays(daysSince(seenDate(record)))}` : ""}` : `${t("checkedAgo")} ${relativeDays(days)}${undetermined ? ` · ${t("undetermined")}` : ""}`;
    const node = el("span", `age age-${undetermined && bucket === "fresh" ? "aging" : bucket}`, text); node.title = t(`freshness_${bucket}`); return node;
  }

  // ---------------------------------------------------------------------------
  // On-demand availability checks through the dashboard state directory.
  // ---------------------------------------------------------------------------
  const canCheck = () => Boolean(state.data?.capabilities?.availability_check);
  let checking = false;
  async function checkAvailability(ids) {
    if (checking || !ids.length) return;
    if (!canCheck()) { showNotice(t("checkUnavailable")); return; }
    checking = true; let done = 0; const outcome = {open: 0, closed: 0, unknown: 0};
    try {
      for (let index = 0; index < ids.length; index += 10) {
        const batch = ids.slice(index, index + 10);
        showNotice(`${t("checkingProgress")} ${Math.min(index + batch.length, ids.length)} / ${ids.length}…`, 60000);
        const response = await fetch("/api/availability/check", {method: "POST", credentials: "same-origin", cache: "no-store", headers: {"Content-Type": "application/json", "X-Career-Copilot": "availability-check"}, body: JSON.stringify({vacancy_ids: batch})});
        if (response.status === 409) { showNotice(t("checkBusy")); return; }
        if (!response.ok) throw new Error("check failed");
        const data = await response.json();
        Object.values(data.results || {}).forEach((result) => { outcome[result.status] = (outcome[result.status] || 0) + 1; done++; });
      }
      await load();
      showNotice(`${t("checkDone")}: ${done} · ${translated("open")} ${outcome.open} · ${translated("closed")} ${outcome.closed} · ${translated("unknown")} ${outcome.unknown}`, 8000);
      if (state.opened && $("record-dialog").open) { const fresh = byId(state.opened.id, state.opened.kind); if (fresh) openRecord(fresh); }
    } catch (_) { showNotice(t("checkFailed")); }
    finally { checking = false; }
  }
  function checkButton(ids, text, className = "text-button check-button") {
    const node = button(text || t("checkNow"), className, () => checkAvailability(typeof ids === "function" ? ids() : ids));
    node.disabled = !canCheck(); if (!canCheck()) node.title = t("checkUnavailable"); return node;
  }
  function availabilityPanel(record) {
    const check = record.display?.availability_check || record.payload.availability_check, panel = el("section", "detail-section availability-panel"), head = el("div", "plan-section-row");
    head.append(el("h3", "", t("availabilityTitle")), checkButton([record.id], t("checkNow"), "quiet-button check-button")); panel.append(head);
    const row = el("div", "card-meta"); row.append(badge(status(record)), ageBadge(record)); panel.append(row);
    if (check) {
      panel.append(factList([[t("checkResult"), translated(check.status)], [t("checkReason"), t(`reason_${check.reason}`)], [t("checkConfidence"), t(`confidence_${check.confidence}`)], [t("checkEvidence"), check.evidence ? String(check.evidence) : ""], [t("checkTime"), formatDateTime(check.checked_at)], [t("checkUrl"), check.final_url ? externalLink(check.final_url, check.final_url.replace(/^https?:\/\/(www\.)?/, "").slice(0, 80)) : ""]]));
      if (check.pending_import) panel.append(el("p", "muted small-note", t("pendingImport")));
    } else panel.append(el("p", "muted", t("noCheckYet")));
    return panel;
  }

  // ---------------------------------------------------------------------------
  // Application funnel: furthest stage per vacancy, time in stage and reminders.
  // ---------------------------------------------------------------------------
  const STAGES = ["found", "assessed", "documents", "reviewed", "submitted", "response", "interview"];
  const stamp = (...values) => values.map((value) => scalar(value)).filter(Boolean).sort().pop() || "";
  function vacancyStage(record) {
    const p = record.payload, reached = {found: stamp(p.first_seen, p.created_at)};
    const assessment = allRecords().filter((item) => item.kind === "assessments" && item.payload.vacancy_id === record.id && item.display?.current !== false);
    if (assessment.length || (Array.isArray(p.assessments) && p.assessments.length) || ["ranked", "researched"].includes(p.review_status)) reached.assessed = stamp(...assessment.map((item) => item.payload.at), p.reviewed_on) || reached.found;
    const packages = records("documents").filter((item) => item.kind === "packages" && item.payload.vacancy_id === record.id);
    packages.forEach((item) => {
      const versions = Array.isArray(item.payload.versions) ? item.payload.versions : [], current = versions.find((version) => version.id === item.payload.current_version);
      const first = versions.map((version) => scalar(version.date)).filter(Boolean).sort()[0];
      reached.documents = reached.documents || first || reached.assessed || reached.found;
      if (current?.review_status === "passed") reached.reviewed = stamp(current.date) || reached.documents;
    });
    // Only an evidence-backed, user-confirmed submission counts as sent; an imported "submitted" flag does not.
    const linked = (kind) => allRecords().filter((item) => item.kind === kind && (item.payload.vacancy_id === record.id || (Array.isArray(item.payload.vacancy_ids) && item.payload.vacancy_ids.includes(record.id))));
    const submissions = linked("submissions").filter((item) => item.payload.user_confirmed === true && item.payload.sent_at && item.payload.evidence);
    if (submissions.length) reached.submitted = stamp(...submissions.map((item) => item.payload.sent_at));
    const responses = linked("employer_responses").filter((item) => item.payload.evidence);
    if (responses.length) reached.response = stamp(...responses.map((item) => item.payload.received_at));
    // Practice and feedback are preparation, not an interview with the employer.
    const invited = responses.filter((item) => ["interview", "offer"].includes(item.payload.status));
    if (p.interview_date || invited.length) reached.interview = stamp(p.interview_date, ...invited.map((item) => item.payload.received_at));
    reached.unconfirmedSubmission = !submissions.length && packages.some((item) => item.payload.application_status === "submitted");
    const stage = [...STAGES].reverse().find((name) => reached[name] !== undefined) || "found";
    return {stage, since: reached[stage], reached};
  }
  const inactiveVacancy = (record) => INACTIVE.has(status(record)) || record.payload.review_status === "rejected";
  function reminders(list = primaryRecords("vacancies")) {
    const items = [];
    list.filter((record) => !inactiveVacancy(record)).forEach((record) => {
      const {stage, since, reached} = vacancyStage(record), inStage = daysSince(since);
      if (record.payload.interview_date && new Date(record.payload.interview_date).valueOf() >= Date.now() - DAY_MS && Math.ceil((new Date(record.payload.interview_date).valueOf() - Date.now()) / DAY_MS) <= 7) items.push({record, severity: 0, key: "reminderInterview", days: Math.max(0, Math.ceil((new Date(record.payload.interview_date).valueOf() - Date.now()) / DAY_MS))});
      if (reached.unconfirmedSubmission) items.push({record, severity: 1, key: "reminderConfirmSubmission", days: inStage});
      else if (stage === "reviewed" && inStage !== null && inStage > 3) items.push({record, severity: 1, key: "reminderSubmit", days: inStage});
      if (stage === "documents" && inStage !== null && inStage > 5) items.push({record, severity: 2, key: "reminderReview", days: inStage});
      if (stage === "submitted" && inStage !== null && inStage > 14) items.push({record, severity: 1, key: "reminderResponse", days: inStage});
      if (reached.assessed && ["stale", "never"].includes(freshness(record))) items.push({record, severity: 3, key: "reminderCheck", days: daysSince(checkedAt(record))});
    });
    return items.sort((a, b) => a.severity - b.severity || (b.days ?? 999) - (a.days ?? 999));
  }
  function groupedReminders(list) {
    const items = reminders(list), checks = items.filter((item) => item.key === "reminderCheck"), others = items.filter((item) => item.key !== "reminderCheck");
    return checks.length > 1 ? [...others, {key: "reminderCheckGroup", severity: 3, records: checks.map((item) => item.record)}] : items;
  }
  function reminderRow(item) {
    if (item.key === "reminderCheckGroup") {
      const row = el("article", "reminder severity-3"), body = el("div"), details = el("details", "link-details"), list = el("div", "stacked-refs");
      details.append(el("summary", "", `${item.records.length} ${plural(item.records.length, ["вакансия", "вакансии", "вакансий", "vacancy", "vacancies"])}`));
      item.records.forEach((record) => { const line = el("div", "card-age"); line.append(vacancyReference(record, {date: false, compact: true}), ageBadge(record)); list.append(line); });
      details.append(list); body.append(el("strong", "", t("reminderCheckGroup")), details); row.append(body, checkButton(item.records.map((record) => record.id), `${t("checkAll")} (${item.records.length})`));
      return row;
    }
    const row = el("article", `reminder severity-${item.severity}`), body = el("div");
    const text = item.key === "reminderCheck" ? (item.days === null ? t("reminderNeverChecked") : `${t("reminderCheck")} ${relativeDays(item.days)}`) : item.key === "reminderConfirmSubmission" ? t(item.key) : `${t(item.key)}: ${item.days} ${plural(item.days, ["день", "дня", "дней", "day", "days"])}`;
    body.append(el("strong", "", text), vacancyReference(item.record, {date: false, compact: true}));
    row.append(body);
    if (item.key === "reminderCheck") row.append(checkButton([item.record.id]));
    return row;
  }
  function renderPipeline(list) {
    const container = el("div", "pipeline-view"), active = list.filter((record) => !inactiveVacancy(record)), inactive = list.filter(inactiveVacancy);
    const due = groupedReminders(active);
    const remindersPanel = el("section", "view-section"); remindersPanel.append(el("h2", "view-title", `${t("remindersTitle")} · ${due.length}`), el("p", "muted", t("remindersDesc")));
    if (due.length) { const box = el("div", "reminder-list"); due.forEach((item) => box.append(reminderRow(item))); remindersPanel.append(box); } else remindersPanel.append(emptyState("noReminders", "noRemindersDesc", true));
    const board = el("div", "pipeline-board"), byStage = new Map(STAGES.map((name) => [name, []]));
    active.forEach((record) => { const info = vacancyStage(record); byStage.get(info.stage).push({record, info}); });
    STAGES.forEach((name) => {
      const column = el("section", "pipeline-column"), items = byStage.get(name).sort((a, b) => (a.info.since || "").localeCompare(b.info.since || ""));
      const header = el("header", "pipeline-head"); header.append(el("span", "", t(`stage_${name}`)), el("strong", "mono", String(items.length))); column.append(header, el("p", "pipeline-hint", t(`stage_${name}_hint`)));
      items.forEach(({record, info}) => {
        const card = el("article", "pipeline-card"); card.append(employerLine(record), button(recordTitle(record), "record-title", () => openRecord(record)));
        const meta = el("div", "card-meta"); meta.append(badge(status(record)), ageBadge(record)); card.append(meta);
        const since = daysSince(info.since); if (since !== null) card.append(el("p", "pipeline-since", `${t("inStage")} ${since} ${plural(since, ["день", "дня", "дней", "day", "days"])} · ${formatDate(info.since)}`));
        if (record.display?.description?.excerpt) card.append(el("p", "record-summary vacancy-description short", record.display.description.excerpt));
        card.append(vacancyActions(record, {details: false}));
        column.append(card);
      });
      board.append(column);
    });
    const funnel = el("section", "view-section"); funnel.append(el("h2", "view-title", t("funnelTitle")), el("p", "muted", t("funnelDesc")));
    const scroll = el("div", "pipeline-scroll"); scroll.append(board); funnel.append(scroll);
    const closed = el("details", "files-panel"); const summary = el("summary"); summary.append(el("span", "", t("closedLane")), el("span", "mono", String(inactive.length))); closed.append(summary);
    const closedBody = el("div", "files-body stacked-refs"); inactive.forEach((record) => closedBody.append(vacancyReference(record, {compact: true}))); closed.append(closedBody);
    container.append(remindersPanel, funnel, closed); return container;
  }
  // ---------------------------------------------------------------------------
  // Vacancy essentials: employer and place, description, status, posting, full text, plan.
  // Everything else lives in the collapsed technical details.
  // ---------------------------------------------------------------------------
  const flag = (country) => { const code = countryCodes[country]; return code ? String.fromCodePoint(...[...code].map((char) => 127397 + char.charCodeAt(0))) : ""; };
  function placeChip(record) {
    const geo = geography(record), parts = [geo.country !== "unknown" ? `${flag(geo.country)} ${countryName(geo.country)}`.trim() : "", geo.city !== "unknown" ? geo.city : "", geo.remote !== "unknown" ? translated(geo.remote) : ""].filter(Boolean);
    return parts.length ? el("span", "place-chip", parts.join(" · ")) : null;
  }
  function employerLine(record) { const line = el("div", "employer-line"); line.append(el("span", "company-name", companyName(record) || t("unknown"))); const place = placeChip(record); if (place) line.append(place); return line; }
  const learningFor = (record) => records("preparations").filter((item) => item.kind === "learning" && item.display?.current !== false && (item.payload.vacancy_id === record.id || (Array.isArray(item.payload.gaps) && item.payload.gaps.some((gap) => Array.isArray(gap.vacancy_ids) && gap.vacancy_ids.includes(record.id)))));
  function openPlan(plan) {
    if ($("record-dialog").open) $("record-dialog").close();
    navigate("preparations");
    requestAnimationFrame(() => { const article = [...document.querySelectorAll(".plan")].find((node) => node.dataset.recordId === plan.id); if (!article) return; const body = article.querySelector("details"); if (body) body.open = true; article.classList.add("is-highlighted"); article.scrollIntoView({block: "start"}); });
  }
  function technicalSections(record, notice) {
    const p = record.payload, fragment = document.createDocumentFragment();
    if (notice && notice !== "detailLoading") fragment.append(el("p", "detail-warning", t(notice)));
    if (["companies", "vacancies"].includes(record.kind)) { const geo = el("div", "detail-geography"); geo.append(geographyBlock(record)); const raw = geography(record).raw; if (raw) { const rawText = el("div", "location-line"); rawText.textContent = `${t("originalLocation")}: ${raw}`; geo.append(rawText); } fragment.append(geo); }
    if (record.kind === "vacancies" && !record.missing) fragment.append(availabilityPanel(record));
    const links = [...linksFrom(p.urls || p.url || p.profile_sources || p.source_url || [])]; if (links.length) { const group = el("div", "detail-links"); links.forEach((url, index) => group.append(externalLink(url, record.kind === "vacancies" && index === 0 ? `${t("openPosting")} ↗` : `${t("source")} ${index + 1} ↗`))); fragment.append(group); }
    const groups = {recordFields: {}, evidenceFields: {}, versionFields: {}, sourceFields: {}};
    Object.entries(p).forEach(([key, value]) => { if (key === "id") return; const group = /^(versions|files|artifacts|reviews|current_version|review_status|application_status)$/.test(key) ? "versionFields" : /(requirement|evidence|assessment|gate|decision|seniority|gap)/.test(key) ? "evidenceFields" : /(source|url|snapshot|dossier|provenance)/.test(key) ? "sourceFields" : "recordFields"; groups[group][key] = value; });
    Object.entries(groups).forEach(([name, fields]) => { if (!Object.keys(fields).length) return; const section = el("section", "detail-section"); section.append(el("h3", "", t(name)), renderValue(fields)); fragment.append(section); });
    const mentions = (candidate) => { const c = candidate.payload; return (Array.isArray(c.entity_ids) && c.entity_ids.includes(record.id)) || (Array.isArray(c.vacancy_ids) && c.vacancy_ids.includes(record.id)) || (Array.isArray(c.gaps) && c.gaps.some((gap) => Array.isArray(gap.vacancy_ids) && gap.vacancy_ids.includes(record.id))); };
    const related = allRecords().filter((candidate) => candidate !== record && !(candidate.id === record.id && candidate.kind === record.kind) && ((record.kind === "companies" && candidate.payload.company_id === record.id) || (record.kind === "vacancies" && candidate.payload.vacancy_id === record.id) || (record.kind === "packages" && candidate.payload.package_id === record.id) || (record.kind === "activities" && (candidate.payload.activity_id === record.id || candidate.payload.parent_activity_id === record.id)) || (!["activity_events", "legacy_files"].includes(candidate.kind) && mentions(candidate)))).sort((a, b) => (a.display?.current === false) - (b.display?.current === false) || dateValue(b).localeCompare(dateValue(a)));
    if (related.length) { const section = el("section", "detail-section"), items = el("div", "related-records"); related.slice(0, 40).forEach((candidate) => { const row = el("div", "related-row"); row.append(recordReference(candidate)); if (candidate.kind !== "vacancies" && formatDate(dateValue(candidate))) row.append(el("span", "muted related-date", formatDate(dateValue(candidate)))); if (candidate.display?.current === false) row.append(badge("superseded")); items.append(row); }); section.append(el("h3", "", t("related")), items); fragment.append(section); }
    const raw = el("details", "raw-details"); raw.append(el("summary", "", t("technical")), el("pre", "", JSON.stringify(p, null, 2))); fragment.append(el("div", "detail-id", record.id), raw);
    return fragment;
  }
  // ---------------------------------------------------------------------------
  // Vacancy cards and details (research §7.2): role and original pay, employer and place,
  // conditions with their origin, fit, next step, dates and actions. Unknown stays unknown.
  // ---------------------------------------------------------------------------
  Object.assign(copy.ru, {
    salaryNotStated: "Зарплата не указана", fromWord: "от", upToWord: "до",
    period_month: "в месяц", period_year: "в год", period_hour: "в час", period_unknown: "период не указан",
    tax_gross: "до вычета налогов", tax_net: "на руки", tax_unknown: "налоги не указаны",
    providerConversion: "пересчёт поставщика, не предложение работодателя", monthShort: "мес",
    whereAllowed: "Где разрешено работать", languageLabel: "Язык", formatLabel: "Формат", employmentLabel: "Занятость",
    notStated: "не указано", unknownShort: "?", toClarify: "нужно уточнить", remoteNeedsCountries: "удалённо, страны не указаны — нужно уточнить", officeIn: "офис:",
    fitLabel: "Соответствие", fitNotAssessedReason: "оценки по требованиям ещё нет", nextStep: "Следующий шаг",
    campaignsLabel: "Кампании", campaignFits: "подходит", campaignUnknown: "уточнить", campaignMismatch: "не подходит",
    publishedOn: "Опубликовано", discoveredOn: "Обнаружено", verifiedOn: "Проверено", lastSeen: "Последний раз в выдаче", notStatedShort: "не указано",
    moreDetails: "Подробнее", tailorCv: "Адаптировать резюме", preparationAction: "Подготовка", originalPosting: "Оригинал",
    vacancySections: "Разделы вакансии", tab_vacancy: "Вакансия", tab_fit: "Соответствие", tab_company: "Компания", tab_resume: "Резюме", tab_prep: "Подготовка",
    conditionsTitle: "Условия", salaryLabel: "Зарплата", marketLabel: "Рынок", completeness: "Полнота описания", conditionsNotExtracted: "Условия ещё не извлечены из сохранённого текста.",
    scope_full: "полное описание", scope_page_text: "текст страницы", scope_excerpt: "фрагмент из выдачи", scope_salary_index_card: "карточка агрегатора без описания", scope_card: "карточка без описания", scope_retained: "описание в материалах исследования", scope_none: "описания нет",
    campaignsTitle: "Кампании поиска", campaignsNote: "Сравнение с вашими предпочтениями. На оценку квалификации не влияет.", noCampaigns: "Кампании поиска ещё не настроены.",
    criterion_market: "Рынок", criterion_track: "Направление", criterion_role_titles: "Роль", criterion_levels: "Уровень", criterion_work_countries: "Страны работы", criterion_work_modes: "Формат", criterion_employment: "Занятость", criterion_languages: "Язык", criterion_salary: "Зарплата", criterion_exclusions: "Исключения",
    personalDecision: "Личное решение", decisionStatus: "Решение", reasonLabel: "Причина", dateLabel: "Дата", researchNote: "Заметка исследования",
    notInterestedReason: "Почему не интересно", markNotInterested: "Не интересно", markInterested: "Интересно", clearDecision: "Снять решение", reasonRequired: "Укажите причину.",
    decisionHelp: "Личное решение хранится отдельно и не меняет доказательства и оценку.",
    fitTitle: "Подходим или нет", fitNotAssessedHelp: "Оценка появится после разбора требований и сопоставления с подтверждёнными фактами.", requestEvaluation: "Запросить оценку", requirementColumn: "Требование", mandatoryColumn: "Обязательно", evidenceColumn: "Доказательство", resultColumn: "Результат",
    companyUnknown: "Компания не найдена в журнале.", companyNeedsReview: "Компания создана автоматически при добавлении вакансии — проверьте название и профиль.", otherVacancies: "Другие вакансии компании", companyDossiers: "Досье и исследования", openCompany: "Карточка компании",
    resumeForVacancy: "Резюме под эту вакансию", noVacancyCv: "Версии резюме под эту вакансию пока нет.", requestTailorCv: "Поставить задачу: адаптировать резюме", tailorNote: "Задачу выполнит агентская сессия по контракту авторства и ревью. Master-резюме при этом не меняется.", currentVersion: "Текущая версия", openPackage: "Открыть пакет",
    prepForVacancy: "Подготовка к этой вакансии", codingTitle: "Нужен ли coding", coding_required: "требуется", coding_not_required: "не требуется", coding_unknown: "неизвестно", codingBasis: "Основание", codingSource: "Источник (ссылка или документ)", saveCoding: "Сохранить", codingBasisRequired: "Укажите основание.", codingNote: "Флаг ставится только с основанием; из названия роли не выводится, LeetCode не назначается автоматически.",
    requestBrief: "Поставить задачу: памятка к вакансии", briefNote: "Исследование компании, этапов и вопросов с источниками. Готовое резюме не требуется.",
    requestsUnavailable: "Действия из интерфейса доступны, когда веб-интерфейс запущен с каталогом состояния (--state-dir).", requestQueued: "Заявка сохранена. Она применится к журналу при следующей синхронизации.", taskQueued: "Задача сохранена и будет передана агентской сессии при синхронизации.", requestConflict: "Запись изменилась с момента открытия. Данные обновлены — повторите действие.", requestInvalid: "Заявка не принята", requestBusy: "Слишком много необработанных заявок. Дождитесь синхронизации.", requestFailed: "Не удалось сохранить заявку.",
    awaitingImport: "ожидает синхронизации", workTitle: "Заявки и задачи", workDesc: "Заявки из интерфейса применяются к журналу командой ajh inbox apply. Задачи выполняются агентской сессией; «готово» появляется только после завершённой активности.", noWork: "Заявок и задач нет.",
    request_vacancy_decision: "Личное решение", request_clarification_answer: "Ответ на вопрос", request_coding_requirement: "Флаг coding", request_evaluate: "Оценка", request_vacancy_add: "Добавление вакансии", request_prep_plan: "План подготовки", request_prep_create: "Вопрос для практики", request_practice_answer: "Ответ на практике", request_cv_edit_decision: "Решение по правке резюме", request_cv_import: "Импорт резюме", request_campaign_upsert: "Кампания поиска",
    task_collect: "Сбор вакансий", task_annotate_requirements: "Разметка требований", task_tailor_cv: "Адаптация резюме", task_fix_master_cv: "Правка master-резюме", task_extract_cv_facts: "Извлечение фактов из CV", task_prepare_vacancy_brief: "Памятка к вакансии", task_track_plan_materials: "Материалы плана", task_review_practice: "Разбор ответа",
    collectTitle: "Сбор и добавление вакансий", collectDesc: "Запуск сбора ставит задачу агентской сессии. Добавленная ссылка или текст сохраняются с оригиналом.", runCollection: "Запустить сбор", collectQueued: "Задача сбора сохранена.",
    lastRun: "Последний сбор", noRuns: "Сбор через адаптеры ещё не запускался.", runTime: "Время", runNew: "Новые", runChanged: "Изменились", runUnchanged: "Без изменений", runDuplicates: "Возможные дубли", runErrors: "Ошибки источников", changedFields: "поля", duplicateOf: "похожа на",
    addVacancy: "Добавить вакансию по ссылке или тексту", vacancyLink: "Ссылка на вакансию", vacancyText: "Или текст вакансии", vacancyTitleField: "Название (если в тексте нет строки Title:)", companyField: "Компания", locationField: "Место работы", trackField: "Направление", anyOption: "не выбрано", addVacancySubmit: "Сохранить заявку", linkOrText: "Укажите ссылку или вставьте текст — что-то одно.",
    campaignsDesc: "Что вы ищете: рынок, роли, уровень, страны, формат, язык, занятость, зарплата и исключения. Одна вакансия может подходить нескольким кампаниям.", newCampaign: "Новая кампания", editCampaign: "Изменить", campaignName: "Название", roleTitles: "Роли (через запятую)", levelsField: "Уровни (через запятую)", countriesField: "Страны работы (через запятую)", languagesField: "Языки, коды ISO (через запятую)", exclusionsField: "Исключения (через запятую)", salaryMin: "Минимум", currencyField: "Валюта (ISO)", periodField: "Период", taxField: "Налоги", activeField: "Активна", saveCampaign: "Сохранить кампанию", campaignNameRequired: "Укажите название и направление.", matchedVacancies: "подходят",
    reasonAllMandatory: "Все обязательные требования подтверждены проверенными фактами", basis_reviewed_evidence: "Проверенные факты сопоставлены и просмотрены", basis_unreviewed_evidence: "Факты привязаны, но не просмотрены против этого требования", basis_structural_unknown: "Нужны датированные доказательства или подтверждение; курс это не закрывает", basis_probable_experience: "Опыт, вероятно, есть в подтверждённых фактах — подтвердите и опишите в резюме", basis_checked_no_evidence: "После сравнения подтверждений нет — развивать и показать результат", basis_not_linked: "Факты ещё не сопоставлены с требованием — нужна разметка", basis_confirmed_unmet: "Подтверждённое несоответствие", basis_authorization_no: "В настройках кандидата нет разрешения на работу", basis_authorization_yes: "В настройках кандидата есть разрешение на работу", basis_track_annotated: "Направление вакансии размечено", basis_track_missing: "Направление вакансии не размечено", basis_gate_recorded: "Условие зафиксировано", basis_gate_not_recorded: "Не зафиксировано", basis_geography_not_stated: "Где можно работать, не указано", basis_geography_listed: "Разрешённые страны указаны в вакансии", basis_languages_covered: "Языки кандидата покрывают требование", basis_languages_missing: "Требуемого языка нет в языках кандидата", basis_no_requirements: "Требования не размечены по полному описанию", basis_no_verified_facts: "Нет подтверждённых фактов кандидата по этому треку", basis_level_mapping_needed: "Соответствие уровню компании нужно подтвердить", basis_level_meets_band: "Уровень входит в целевой диапазон работодателя", basis_level_below_band: "Уровень ниже целевого диапазона работодателя", basis_level_unmapped: "Уровень работодателя не сопоставлен", basis_level_director_threshold: "Порог уровня директора для российского рынка", basis_level_confirm_scope: "Подтвердите масштаб и уровень; числового пересчёта между компаниями нет",
    staleShort: "требует обновления", staleNotice: "Оценка требует обновления: изменились", input_vacancy: "вакансия", input_company: "компания", input_facts: "факты кандидата", input_policy: "политика уровней", input_candidate: "ограничения кандидата", legacyAssessment: "Оценка по старым правилам — запросите новую, чтобы увидеть объяснение.", matrixTitle: "Требования", constraintsTitle: "Обязательные ограничения", completenessTitle: "Полнота данных", requirementsCount: "Требований", verifiedFacts: "Подтверждённых фактов по треку", suggestedFacts: "похожие подтверждённые факты", basisLabel: "Основание", clarificationLabel: "Ответ на уточнение", action_cv_edit: "Правка резюме", action_preparation: "В подготовку", action_clarify: "Уточнить", action_decision_basis: "Основание для решения", goToResume: "К резюме", goToPrep: "К подготовке", clarificationAnswer: "Ответ или уточнение", saveAnswer: "Сохранить ответ", decisionBasisHelp: "Подтверждённое несоответствие; пересмотрите, если изменятся факты или условия.", requestAnnotation: "Поставить задачу: разметить требования", fitRules: "Без процента и вероятности найма. Отсутствие слова в резюме не означает отсутствие опыта; предпочтения кампаний не меняют результат.", constraint_track: "Направление", constraint_seniority: "Уровень", constraint_language: "Язык", constraint_eligibility: "Допуск к работе", constraint_geography: "География", constraint_required_languages: "Требуемые языки",
    sourceProblem: "Проблема", campaignsInvalid: "Кампании в settings.json не применяются из-за ошибки", lastSuccess: "Последний успех", marketAll: "Все", marketRu: "РФ", marketIntl: "Международные", marketUnknown: "Рынок не определён"
  });
  Object.assign(copy.en, {
    salaryNotStated: "Salary not stated", fromWord: "from", upToWord: "up to",
    period_month: "per month", period_year: "per year", period_hour: "per hour", period_unknown: "period not stated",
    tax_gross: "before tax", tax_net: "after tax", tax_unknown: "tax basis not stated",
    providerConversion: "provider recalculation, not an employer offer", monthShort: "mo",
    whereAllowed: "Where work is allowed", languageLabel: "Language", formatLabel: "Format", employmentLabel: "Employment",
    notStated: "not stated", unknownShort: "?", toClarify: "to clarify", remoteNeedsCountries: "remote, countries not stated — to clarify", officeIn: "office:",
    fitLabel: "Fit", fitNotAssessedReason: "no requirement assessment yet", nextStep: "Next step",
    campaignsLabel: "Campaigns", campaignFits: "fits", campaignUnknown: "to clarify", campaignMismatch: "does not fit",
    publishedOn: "Published", discoveredOn: "Discovered", verifiedOn: "Verified", lastSeen: "Last seen in a listing", notStatedShort: "not stated",
    moreDetails: "Details", tailorCv: "Tailor CV", preparationAction: "Preparation", originalPosting: "Original",
    vacancySections: "Vacancy sections", tab_vacancy: "Vacancy", tab_fit: "Fit", tab_company: "Company", tab_resume: "CV", tab_prep: "Preparation",
    conditionsTitle: "Conditions", salaryLabel: "Salary", marketLabel: "Market", completeness: "Description completeness", conditionsNotExtracted: "Conditions have not been extracted from the retained text yet.",
    scope_full: "full description", scope_page_text: "page text", scope_excerpt: "listing excerpt", scope_salary_index_card: "aggregator card without a description", scope_card: "card without a description", scope_retained: "description in research material", scope_none: "no description",
    campaignsTitle: "Search campaigns", campaignsNote: "Compared with your preferences. This does not affect the qualification assessment.", noCampaigns: "No search campaigns are configured yet.",
    criterion_market: "Market", criterion_track: "Track", criterion_role_titles: "Role", criterion_levels: "Level", criterion_work_countries: "Work countries", criterion_work_modes: "Format", criterion_employment: "Employment", criterion_languages: "Language", criterion_salary: "Salary", criterion_exclusions: "Exclusions",
    personalDecision: "Personal decision", decisionStatus: "Decision", reasonLabel: "Reason", dateLabel: "Date", researchNote: "Research note",
    notInterestedReason: "Why it is not interesting", markNotInterested: "Not interested", markInterested: "Interested", clearDecision: "Clear decision", reasonRequired: "Give a reason.",
    decisionHelp: "A personal decision is stored separately and does not change evidence or the assessment.",
    fitTitle: "Do we fit", fitNotAssessedHelp: "The assessment appears after the requirements are annotated and compared with verified facts.", requestEvaluation: "Request assessment", requirementColumn: "Requirement", mandatoryColumn: "Mandatory", evidenceColumn: "Evidence", resultColumn: "Result",
    companyUnknown: "The company is not in the journal.", companyNeedsReview: "The company was created automatically when the vacancy was added; check its name and profile.", otherVacancies: "Other vacancies at this company", companyDossiers: "Dossiers and research", openCompany: "Company record",
    resumeForVacancy: "CV for this vacancy", noVacancyCv: "No CV version for this vacancy yet.", requestTailorCv: "Queue task: tailor the CV", tailorNote: "An agent session performs the task under the authorship and review contract. The master CV does not change.", currentVersion: "Current version", openPackage: "Open package",
    prepForVacancy: "Preparation for this vacancy", codingTitle: "Is coding required", coding_required: "required", coding_not_required: "not required", coding_unknown: "unknown", codingBasis: "Basis", codingSource: "Source (link or document)", saveCoding: "Save", codingBasisRequired: "Give the basis.", codingNote: "Set only with a basis; it is never inferred from the job title and LeetCode is never assigned automatically.",
    requestBrief: "Queue task: vacancy brief", briefNote: "Company, interview stages and questions with sources. A finished CV is not required.",
    requestsUnavailable: "Interface actions are available when the dashboard runs with a state directory (--state-dir).", requestQueued: "Request saved. It is applied to the journal at the next sync.", taskQueued: "Task saved; it is handed to an agent session at the next sync.", requestConflict: "The record changed since you opened it. Data refreshed — repeat the action.", requestInvalid: "Request rejected", requestBusy: "Too many unprocessed requests. Wait for the next sync.", requestFailed: "The request could not be saved.",
    awaitingImport: "awaiting sync", workTitle: "Requests and tasks", workDesc: "Interface requests are applied to the journal by ajh inbox apply. Tasks run in an agent session; “done” appears only after a finished activity.", noWork: "No requests or tasks.",
    request_vacancy_decision: "Personal decision", request_clarification_answer: "Clarification answer", request_coding_requirement: "Coding flag", request_evaluate: "Assessment", request_vacancy_add: "Add vacancy", request_prep_plan: "Preparation plan", request_prep_create: "Practice question", request_practice_answer: "Practice answer", request_cv_edit_decision: "CV edit decision", request_cv_import: "CV import", request_campaign_upsert: "Search campaign",
    task_collect: "Collect vacancies", task_annotate_requirements: "Annotate requirements", task_tailor_cv: "Tailor CV", task_fix_master_cv: "Fix master CV", task_extract_cv_facts: "Extract CV facts", task_prepare_vacancy_brief: "Vacancy brief", task_track_plan_materials: "Plan materials", task_review_practice: "Answer review",
    collectTitle: "Collect and add vacancies", collectDesc: "Running collection queues a task for an agent session. An added link or text is stored with its original.", runCollection: "Run collection", collectQueued: "Collection task saved.",
    lastRun: "Last collection", noRuns: "Adapter collection has not run yet.", runTime: "Time", runNew: "New", runChanged: "Changed", runUnchanged: "Unchanged", runDuplicates: "Possible duplicates", runErrors: "Source errors", changedFields: "fields", duplicateOf: "looks like",
    addVacancy: "Add a vacancy by link or text", vacancyLink: "Vacancy link", vacancyText: "Or the vacancy text", vacancyTitleField: "Title (if the text has no Title: line)", companyField: "Company", locationField: "Location", trackField: "Track", anyOption: "not selected", addVacancySubmit: "Save request", linkOrText: "Give a link or paste the text, not both.",
    campaignsDesc: "What you are looking for: market, roles, level, countries, format, language, employment, salary and exclusions. One vacancy can fit several campaigns.", newCampaign: "New campaign", editCampaign: "Edit", campaignName: "Name", roleTitles: "Roles (comma-separated)", levelsField: "Levels (comma-separated)", countriesField: "Work countries (comma-separated)", languagesField: "Languages, ISO codes (comma-separated)", exclusionsField: "Exclusions (comma-separated)", salaryMin: "Minimum", currencyField: "Currency (ISO)", periodField: "Period", taxField: "Tax basis", activeField: "Active", saveCampaign: "Save campaign", campaignNameRequired: "Give a name and a track.", matchedVacancies: "fit",
    reasonAllMandatory: "All mandatory requirements are backed by reviewed verified facts", basis_reviewed_evidence: "Verified facts compared and reviewed", basis_unreviewed_evidence: "Facts are linked but not reviewed against this requirement", basis_structural_unknown: "Needs dated evidence or confirmation; a course cannot close it", basis_probable_experience: "Experience probably exists in verified facts; confirm it and describe it in the CV", basis_checked_no_evidence: "No evidence after comparison; build and demonstrate it", basis_not_linked: "Facts are not compared with this requirement yet; annotation needed", basis_confirmed_unmet: "Confirmed mismatch", basis_authorization_no: "Candidate settings: no work authorization", basis_authorization_yes: "Candidate settings: work authorization confirmed", basis_track_annotated: "Vacancy track is annotated", basis_track_missing: "Vacancy track is not annotated", basis_gate_recorded: "Condition recorded", basis_gate_not_recorded: "Not recorded", basis_geography_not_stated: "Where the work may be done is not stated", basis_geography_listed: "Allowed countries are listed in the vacancy", basis_languages_covered: "Candidate languages cover the requirement", basis_languages_missing: "A required language is not among the candidate's languages", basis_no_requirements: "Requirements are not annotated from a full description", basis_no_verified_facts: "No verified candidate facts for this track", basis_level_mapping_needed: "The employer level equivalence needs evidence", basis_level_meets_band: "Within the employer's documented target band", basis_level_below_band: "Below the employer's target band", basis_level_unmapped: "Unmapped employer level", basis_level_director_threshold: "Director threshold for the Russian market", basis_level_confirm_scope: "Confirm scope and seniority; no cross-company numeric conversion",
    staleShort: "needs update", staleNotice: "The assessment needs an update; changed", input_vacancy: "vacancy", input_company: "company", input_facts: "candidate facts", input_policy: "level policy", input_candidate: "candidate constraints", legacyAssessment: "Assessed with the previous rules; request a new assessment to see the explanation.", matrixTitle: "Requirements", constraintsTitle: "Mandatory constraints", completenessTitle: "Data completeness", requirementsCount: "Requirements", verifiedFacts: "Verified facts for the track", suggestedFacts: "similar verified facts", basisLabel: "Basis", clarificationLabel: "Clarification answer", action_cv_edit: "CV edit", action_preparation: "To preparation", action_clarify: "Clarify", action_decision_basis: "Decision basis", goToResume: "To CV", goToPrep: "To preparation", clarificationAnswer: "Answer or clarification", saveAnswer: "Save answer", decisionBasisHelp: "A confirmed mismatch; revisit it if facts or conditions change.", requestAnnotation: "Queue task: annotate requirements", fitRules: "No percentage or hiring probability. A missing word in the CV is not missing experience; campaign preferences never change the result.", constraint_track: "Track", constraint_seniority: "Level", constraint_language: "Language", constraint_eligibility: "Eligibility", constraint_geography: "Geography", constraint_required_languages: "Required languages",
    sourceProblem: "Problem", campaignsInvalid: "Campaigns in settings.json are ignored because of an error", lastSuccess: "Last success", marketAll: "All", marketRu: "Russia", marketIntl: "International", marketUnknown: "Market unknown"
  });
  Object.assign(enums, {
    remote: ["Удалённо", "Remote"], hybrid: ["Гибрид", "Hybrid"], office: ["Офис", "Office"], full_time: ["Полная занятость", "Full-time"], part_time: ["Частичная занятость", "Part-time"], contract: ["Контракт", "Contract"], internship: ["Стажировка", "Internship"], temporary: ["Временная работа", "Temporary"],
    fits_verified: ["Подходит по проверенным требованиям", "Fits verified requirements"], has_questions: ["Есть вопросы", "Has questions"], not_fit_mandatory: ["Не подходит по обязательному условию", "Does not meet a mandatory condition"], insufficient_data: ["Недостаточно данных", "Insufficient data"], gap: ["Пробел", "Gap"], pass: ["Выполнено", "Pass"], fail: ["Не выполнено", "Fail"], qualification: ["Квалификация", "Qualification"], constraint: ["Ограничение", "Constraint"],
    match: ["Подходит", "Match"], mismatch: ["Не подходит", "Does not fit"], not_assessed: ["Не оценено", "Not assessed"], queued: ["В очереди", "Queued"], running: ["Выполняется", "Running"], done: ["Готово", "Done"], applied: ["Применено", "Applied"], queued_for_agent: ["Передано агенту", "Handed to an agent"], conflict: ["Конфликт версий", "Version conflict"], failed: ["Ошибка", "Failed"], config_error: ["Ошибка настройки", "Configuration error"],
    ru: ["РФ", "Russia"], intl: ["Международный", "International"], any: ["Любой", "Any"], not_interested: ["Не интересно", "Not interested"], interested: ["Интересно", "Interested"], greenhouse: ["Greenhouse", "Greenhouse"], intake: ["Добавлена вручную", "Added manually"]
  });
  const TRACK_OPTIONS = ["product", "technical-leadership"];
  const DETAIL_TABS = ["vacancy", "fit", "company", "resume", "prep"];
  const conditionsOf = (record) => record.payload?.conditions && typeof record.payload.conditions === "object" ? record.payload.conditions : {};
  const conditionValue = (record, key) => { const entry = conditionsOf(record)[key]; return entry && typeof entry === "object" ? entry.value : undefined; };
  const knownCondition = (value) => value !== undefined && value !== null && value !== "unknown" && !(Array.isArray(value) && !value.length);
  const marketOf = (record) => ["ru", "intl"].includes(record.payload?.market) ? record.payload.market : "unknown";
  const languageName = (code) => { try { return new Intl.DisplayNames([state.lang], {type: "language"}).of(code) || code; } catch (_) { return code; } };
  function money(value, currency) {
    if (typeof value !== "number") return "";
    try { return new Intl.NumberFormat(state.lang === "ru" ? "ru-RU" : "en-US", {style: "currency", currency, maximumFractionDigits: 0}).format(value); }
    catch (_) { return `${value.toLocaleString(state.lang)} ${currency || ""}`.trim(); }
  }
  function salaryParts(record) {
    const salary = conditionsOf(record).salary;
    if (!salary || (typeof salary.min !== "number" && typeof salary.max !== "number")) return {known: false, amount: t("salaryNotStated"), meta: ""};
    const low = money(salary.min, salary.currency), high = money(salary.max, salary.currency);
    const amount = low && high ? (salary.min === salary.max ? low : `${low} – ${high}`) : low ? `${t("fromWord")} ${low}` : `${t("upToWord")} ${high}`;
    return {known: true, amount, meta: [t(`period_${salary.period || "unknown"}`), t(`tax_${salary.gross_net || "unknown"}`)].join(" · "), source: salary.source, raw: typeof salary.raw === "string" ? salary.raw : ""};
  }
  function salaryBlock(record) {
    const parts = salaryParts(record), box = el("div", `vc-salary${parts.known ? "" : " is-unknown"}`);
    box.append(el("strong", "", parts.amount));
    if (parts.meta) box.append(el("span", "", parts.meta));
    if (parts.known) box.title = [parts.source ? `${t("source")}: ${parts.source}` : "", parts.raw].filter(Boolean).join(" — ");
    const conversion = conditionsOf(record).provider_conversion;
    if (conversion && typeof conversion.amount === "number") box.append(el("span", "vc-conversion", `≈ ${money(conversion.amount, conversion.currency)}/${t("monthShort")} · ${t("providerConversion")}`));
    return box;
  }
  function languageText(record) { const value = conditionValue(record, "language"); return knownCondition(value) ? value.map(languageName).join(", ") : t("notStated"); }
  function allowedGeographyText(record) {
    const geo = conditionsOf(record).allowed_geography || {}, mode = conditionValue(record, "work_mode"), place = geography(record);
    if (geo.status === "listed" && Array.isArray(geo.countries) && geo.countries.length) return geo.countries.map((country) => countryName(country)).join(", ");
    if (geo.status === "office_location" && geo.basis) return `${t("officeIn")} ${geo.basis}`;
    if ((mode === "office" || mode === "hybrid") && place.country !== "unknown") return `${translated(mode)}: ${[place.city !== "unknown" ? place.city : "", countryName(place.country)].filter(Boolean).join(", ")}`;
    return mode === "remote" || place.remote === "remote" ? t("remoteNeedsCountries") : t("toClarify");
  }
  const currentAssessments = (record) => allRecords().filter((item) => item.kind === "assessments" && item.payload.vacancy_id === record.id && item.display?.current !== false);
  const basisText = (code, fallback) => code && t(`basis_${code}`) !== `basis_${code}` ? t(`basis_${code}`) : tx(scalar(fallback));
  function reasonText(payload) {
    const ref = payload.reason_ref;
    if (!ref || typeof ref !== "object") return scalar(payload.reason);
    if (ref.type === "all_mandatory") return `${t("reasonAllMandatory")}: ${ref.count}`;
    if (ref.type === "data") return basisText(ref.code, payload.reason);
    if (ref.type === "requirement") { const row = (payload.requirements || []).find((item) => item.requirement_id === ref.id); return row ? `${tx(scalar(row.text))} — ${basisText(ref.code, row.basis)}` : scalar(payload.reason); }
    if (ref.type === "constraint") { const item = (payload.constraints || []).find((entry) => entry.name === ref.name); return `${t(`constraint_${ref.name}`)} — ${basisText(ref.code, item?.basis || payload.reason)}`; }
    return scalar(payload.reason);
  }
  function fitSummary(record) {
    const items = currentAssessments(record).sort((a, b) => scalar(b.payload.at).localeCompare(scalar(a.payload.at)));
    if (!items.length) return {status: "not_assessed", reason: t("fitNotAssessedReason"), all: []};
    const p = items[0].payload, legacy = !p.outcome;
    return {status: p.outcome || (isToken(p.decision) ? p.decision : "unknown"), reason: legacy ? scalar(p.reason || p.summary || t("legacyAssessment")) : reasonText(p), assessment: items[0], all: items, stale: items.some((item) => Array.isArray(item.display?.stale) && item.display.stale.length), legacy};
  }
  function campaignSummary(record) {
    const list = record.display?.campaigns || [], count = (value) => list.filter((item) => item.status === value).length;
    return [[count("match"), "campaignFits"], [count("unknown"), "campaignUnknown"], [count("mismatch"), "campaignMismatch"]].filter(([value]) => value).map(([value, key]) => `${t(key)}: ${value}`).join(" · ");
  }
  const sourceLabel = (record) => { const p = record.payload; if (p.provider && p.provider !== "intake") return translated(p.provider); const url = vacancyUrl(record); try { return url ? new URL(url).hostname.replace(/^www\./, "") : ""; } catch (_) { return ""; } };
  function datesLine(record) {
    const dates = record.display?.dates || {}, found = dates.discovered_at || seenDate(record), checked = checkedAt(record), source = sourceLabel(record);
    return el("p", "vc-dates", [
      `${t("publishedOn")}: ${dates.published_on ? formatDate(dates.published_on) : t("notStatedShort")}`,
      found ? `${t("discoveredOn")}: ${formatDate(found)}` : "",
      `${t("verifiedOn")}: ${checked ? formatDate(checked) : t("never")}`,
      source ? `${t("source")}: ${source}` : ""
    ].filter(Boolean).join(" · "));
  }
  function conditionChips(record) {
    const row = el("div", "vc-chips"), add = (text, unknown = false, extra = "") => row.append(el("span", `chip${unknown ? " is-unknown" : ""}${extra}`, text));
    tracks(record).forEach((track) => add(translated(track), false, " chip-track"));
    const level = record.payload.level && typeof record.payload.level === "object" ? scalar(record.payload.level.raw) : scalar(record.payload.level); if (level) add(level);
    const mode = conditionValue(record, "work_mode"), geoMode = geography(record).remote;
    if (knownCondition(mode)) add(translated(mode)); else if (geoMode !== "unknown") add(translated(geoMode)); else add(`${t("formatLabel")}: ${t("unknownShort")}`, true);
    const employment = conditionValue(record, "employment"); if (knownCondition(employment)) add(translated(employment)); else add(`${t("employmentLabel")}: ${t("unknownShort")}`, true);
    return row;
  }
  function fitLine(record) {
    const fit = fitSummary(record), line = el("div", "vc-fit");
    line.append(el("span", "vc-fit-label", `${t("fitLabel")}:`), badge(fit.status));
    if (fit.stale) line.append(el("span", "badge attention", t("staleShort")));
    if (fit.reason) line.append(el("span", "vc-fit-reason", fit.legacy ? tx(fit.reason) : fit.reason));
    const summary = campaignSummary(record); if (summary) line.append(el("span", "vc-fit-campaigns", `${t("campaignsLabel")}: ${summary}`));
    return line;
  }
  function vacancyActions(record, {details = true} = {}) {
    const row = el("div", "vacancy-actions");
    if (details) row.append(button(t("moreDetails"), "text-button", () => openRecord(record, "vacancy")));
    row.append(button(t("tailorCv"), "text-button", () => openRecord(record, "resume")), button(t("preparationAction"), "text-button", () => openRecord(record, "prep")));
    const link = postingLink(record, `${t("originalPosting")} ↗`); if (link) row.append(link);
    return row;
  }
  function vacancyCard(record) {
    const card = el("article", "record-card vacancy-card"), head = el("div", "vc-head"), titleBox = el("div", "vc-title");
    titleBox.append(button(recordTitle(record), "record-title", () => openRecord(record)), employerLine(record));
    head.append(titleBox, salaryBlock(record)); card.append(head, conditionChips(record));
    card.append(el("p", "vc-line", `${t("whereAllowed")}: ${allowedGeographyText(record)} · ${t("languageLabel")}: ${languageText(record)}`));
    const text = record.display?.description?.excerpt; if (text) card.append(el("p", "record-summary vacancy-description", text));
    card.append(fitLine(record));
    const next = scalar(record.payload.next_action); if (next) card.append(el("p", "vc-line vc-next", `${t("nextStep")}: ${tx(next)}`));
    const statusRow = el("div", "card-age"); statusRow.append(badge(status(record)), ageBadge(record));
    card.append(statusRow, datesLine(record), vacancyActions(record));
    return card;
  }

  // Requests: the interface asks, the journal decides (ajh inbox apply), agents do authored work.
  const canRequest = () => Boolean(state.data?.capabilities?.requests);
  let requesting = false;
  async function sendRequest(body, message) {
    if (requesting) return false;
    if (!canRequest()) { showNotice(t("requestsUnavailable"), 8000); return false; }
    requesting = true;
    try {
      const response = await fetch("/api/requests", {method: "POST", credentials: "same-origin", cache: "no-store", headers: {"Content-Type": "application/json", "X-Career-Copilot": "request"}, body: JSON.stringify(body)});
      if (response.status === 409) { await load(); showNotice(t("requestConflict"), 8000); return false; }
      if (response.status === 422) { const data = await response.json().catch(() => ({})); showNotice(`${t("requestInvalid")}${data.detail ? `: ${data.detail}` : ""}`, 9000); return false; }
      if (response.status === 429) { showNotice(t("requestBusy"), 8000); return false; }
      if (!response.ok) throw new Error("request failed");
      await load(); showNotice(message || t("requestQueued"), 8000); return true;
    } catch (_) { showNotice(t("requestFailed")); return false; }
    finally { requesting = false; }
  }
  function requestButton(text, className, build, message) {
    const node = button(text, className, async () => {
      const body = build(); if (!body) return;
      node.disabled = true;
      const ok = await sendRequest(body, message);
      node.disabled = !canRequest();
      if (ok && state.opened && $("record-dialog").open) { const fresh = byId(state.opened.id, state.opened.kind); if (fresh) openRecord(fresh); }
    });
    node.disabled = !canRequest(); if (!canRequest()) node.title = t("requestsUnavailable");
    return node;
  }
  const workRecords = (kind) => (state.data?.work || []).filter((item) => item.kind === kind);
  const requestLabel = (request) => request.type === "task" ? t(`task_${request.payload?.task_type}`) : t(`request_${request.type}`);
  function relatedWork(vacancyId, types) {
    const about = (request) => request.base?.id === vacancyId || request.payload?.vacancy_id === vacancyId || request.payload?.related?.vacancy_id === vacancyId;
    const typed = (request) => !types || types.includes(request.type) || types.includes(request.payload?.task_type);
    return {
      pending: (state.data?.pending_requests || []).filter((request) => about(request) && typed(request)),
      requests: workRecords("inbox_requests").map((item) => item.payload).filter((request) => request.status !== "queued_for_agent" && about(request) && typed(request)),
      tasks: workRecords("tasks").map((item) => item.payload).filter((task) => task.related?.vacancy_id === vacancyId && (!types || types.includes(task.type)))
    };
  }
  function workList(work, limit = 20) {
    const list = el("ul", "work-list"), row = (state, text) => { const item = el("li"); item.append(badge(state), el("span", "", text)); list.append(item); };
    work.pending.slice(0, limit).forEach((request) => row("pending", `${requestLabel(request)} · ${formatDateTime(request.created_at)} · ${t("awaitingImport")}`));
    work.requests.slice(0, limit).forEach((request) => row(request.status, [requestLabel(request), formatDateTime(request.applied_at || request.created_at), request.error ? tx(request.error) : ""].filter(Boolean).join(" · ")));
    work.tasks.slice(0, limit).forEach((task) => row(task.status, [t(`task_${task.type}`), task.related?.track ? translated(task.related.track) : "", formatDateTime(task.updated_at || task.created_at), task.next_action ? tx(task.next_action) : ""].filter(Boolean).join(" · ")));
    return list.childElementCount ? list : null;
  }
  function formField(text, control, wide = false) { const wrap = el("label", `form-field${wide ? " wide" : ""}`); wrap.append(el("span", "", text), control); return wrap; }
  function formInput(type, attrs = {}) { const node = el(type === "textarea" ? "textarea" : "input"); if (type !== "textarea") node.type = type; Object.entries(attrs).forEach(([key, value]) => { if (key === "value") node.value = value; else node.setAttribute(key, value); }); return node; }
  function formSelect(options, value) { const node = el("select"); options.forEach(([optionValue, text]) => { const option = el("option", "", text); option.value = optionValue; node.append(option); }); node.value = value ?? ""; return node; }
  const trackSelect = (value) => formSelect(TRACK_OPTIONS.map((track) => [track, translated(track)]), TRACK_OPTIONS.includes(value) ? value : TRACK_OPTIONS[0]);
  const commaList = (value) => value.split(",").map((item) => item.trim()).filter(Boolean);

  function renderVacancyDetail(record, notice) {
    const fragment = document.createDocumentFragment(); $("detail-kind").textContent = kindName("vacancies");
    const title = el("h2", "detail-heading", recordTitle(record)); title.id = "detail-title";
    const head = el("div", "vc-head detail-head"), titleBox = el("div", "vc-title"); titleBox.append(employerLine(record), title); head.append(titleBox, salaryBlock(record));
    const statusRow = el("div", "status-line"); statusRow.append(badge(status(record)), ageBadge(record));
    if (canCheck() && !record.missing && !inactiveVacancy(record)) statusRow.append(checkButton([record.id]));
    const link = postingLink(record, `${t("originalPosting")} ↗`); if (link) statusRow.append(link);
    fragment.append(head, statusRow);
    if (notice) { const message = el("p", notice === "detailLoading" ? "muted" : "detail-warning", t(notice)); if (notice === "detailLoading") message.setAttribute("role", "status"); fragment.append(message); }
    const current = DETAIL_TABS.includes(state.detailTab) ? state.detailTab : "vacancy", tabs = el("div", "tabs");
    tabs.setAttribute("role", "tablist"); tabs.setAttribute("aria-label", t("vacancySections"));
    const select = (name, focus) => { state.detailTab = name; syncHash(); renderVacancyDetail(state.opened || record, notice === "detailLoading" ? notice : undefined); if (focus) document.getElementById(`tab-${name}`)?.focus(); };
    DETAIL_TABS.forEach((name, index) => {
      const tab = button(t(`tab_${name}`), `tab${name === current ? " active" : ""}`, () => select(name, false));
      tab.id = `tab-${name}`; tab.setAttribute("role", "tab"); tab.setAttribute("aria-selected", String(name === current)); tab.setAttribute("aria-controls", "vacancy-tab-panel"); tab.tabIndex = name === current ? 0 : -1;
      tab.addEventListener("keydown", (event) => {
        const target = event.key === "ArrowRight" ? index + 1 : event.key === "ArrowLeft" ? index - 1 : event.key === "Home" ? 0 : event.key === "End" ? DETAIL_TABS.length - 1 : null;
        if (target === null) return; event.preventDefault(); select(DETAIL_TABS[(target + DETAIL_TABS.length) % DETAIL_TABS.length], true);
      });
      tabs.append(tab);
    });
    const panel = el("section", "tab-panel"); panel.id = "vacancy-tab-panel"; panel.setAttribute("role", "tabpanel"); panel.setAttribute("aria-labelledby", `tab-${current}`); panel.tabIndex = 0;
    panel.append(({vacancy: vacancyTab, fit: fitTab, company: companyTab, resume: resumeTab, prep: prepTab})[current](record, notice));
    fragment.append(tabs, panel);
    $("detail-content").replaceChildren(fragment);
  }
  function vacancyTab(record, notice) {
    const fragment = document.createDocumentFragment(), doc = record.display?.description, about = el("section", "vacancy-about");
    fragment.append(conditionChips(record));
    about.append(el("h3", "", t("descriptionTitle")), el("p", "vacancy-description-full", doc?.excerpt || t("noDescription")));
    if (doc?.path) {
      const full = el("details", "full-description"), holder = el("div", "markdown-holder"); full.append(el("summary", "", t("showFullDescription")), holder);
      full.addEventListener("toggle", () => { if (!full.open || holder.dataset.loaded) return; holder.dataset.loaded = "1"; holder.replaceChildren(el("p", "muted", t("planLoading"))); artifactText(doc.path).then((text) => { holder.replaceChildren(documentBody(doc.path, text)); if (doc.kind === "research") highlightHeading(holder, doc.heading, record); }).catch(() => { delete holder.dataset.loaded; holder.replaceChildren(el("p", "detail-warning", t("planUnavailable"))); }); });
      about.append(full);
    }
    fragment.append(about, conditionsPanel(record), decisionPanel(record));
    const tech = el("details", "technical-details"); tech.append(el("summary", "", t("technicalDetails")), technicalSections(record, notice === "detailLoading" ? undefined : notice));
    fragment.append(tech);
    return fragment;
  }
  function withSource(text, entry, extra) {
    const box = el("span"); box.append(document.createTextNode(text));
    const origin = [entry?.source ? `${t("source")}: ${entry.source}` : "", extra || ""].filter(Boolean).join(" · ");
    if (origin) box.append(el("span", "condition-source", ` · ${origin}`));
    return box;
  }
  function conditionsPanel(record) {
    const c = conditionsOf(record), dates = record.display?.dates || {}, salary = salaryParts(record), section = el("section", "detail-section conditions-panel");
    const mode = conditionValue(record, "work_mode"), employment = conditionValue(record, "employment"), geo = c.allowed_geography || {};
    const scope = record.payload.content_scope || (record.display?.description ? "retained" : "none");
    section.append(el("h3", "", t("conditionsTitle")));
    section.append(factList([
      [t("salaryLabel"), withSource(salary.known ? `${salary.amount} · ${salary.meta}` : t("salaryNotStated"), c.salary, salary.raw)],
      [t("providerConversion"), c.provider_conversion && typeof c.provider_conversion.amount === "number" ? `≈ ${money(c.provider_conversion.amount, c.provider_conversion.currency)} ${t("period_month")} · ${scalar(c.provider_conversion.provider)}` : ""],
      [t("formatLabel"), withSource(knownCondition(mode) ? translated(mode) : t("notStated"), c.work_mode)],
      [t("employmentLabel"), withSource(knownCondition(employment) ? translated(employment) : t("notStated"), c.employment)],
      [t("languageLabel"), withSource(languageText(record), c.language)],
      [t("whereAllowed"), withSource(allowedGeographyText(record), geo, geo.status === "listed" && geo.basis ? geo.basis : "")],
      [t("marketLabel"), translated(marketOf(record))],
      [t("publishedOn"), dates.published_on ? formatDate(dates.published_on) : t("notStated")],
      [t("discoveredOn"), formatDate(dates.discovered_at || seenDate(record)) || t("notStated")],
      [t("verifiedOn"), checkedAt(record) ? formatDateTime(checkedAt(record)) : t("never")],
      [t("lastSeen"), dates.last_seen ? formatDateTime(dates.last_seen) : ""],
      [t("completeness"), t(`scope_${scope}`) === `scope_${scope}` ? scalar(scope) : t(`scope_${scope}`)]
    ]));
    if (!Object.keys(c).length) section.append(el("p", "muted small-note", t("conditionsNotExtracted")));
    return section;
  }
  function criterionContext(record, name) {
    const salary = salaryParts(record);
    return {market: translated(marketOf(record)), track: tracks(record).map(translated).join(", ") || t("notStated"), role_titles: recordTitle(record), levels: scalar(record.payload.level?.raw || record.payload.level) || t("notStated"), work_countries: allowedGeographyText(record), work_modes: knownCondition(conditionValue(record, "work_mode")) ? translated(conditionValue(record, "work_mode")) : t("notStated"), employment: knownCondition(conditionValue(record, "employment")) ? translated(conditionValue(record, "employment")) : t("notStated"), languages: languageText(record), salary: salary.known ? `${salary.amount} · ${salary.meta}` : t("salaryNotStated"), exclusions: ""}[name] || "";
  }
  function campaignsPanel(record) {
    const list = record.display?.campaigns || [], section = el("section", "detail-section");
    section.append(el("h3", "", t("campaignsTitle")), el("p", "muted small-note", t("campaignsNote")));
    if (!list.length) { section.append(el("p", "muted", t("noCampaigns"))); return section; }
    list.forEach((match) => {
      const box = el("div", "campaign-match"), head = el("div", "plan-section-row"), items = el("ul", "criteria-list");
      head.append(el("strong", "", match.campaign_name), badge(match.status));
      match.criteria.forEach((criterion) => { const item = el("li"); item.title = criterion.basis; item.append(el("span", "criterion-name", t(`criterion_${criterion.name}`)), badge(criterion.status), el("span", "muted", criterionContext(record, criterion.name) || criterion.basis)); items.append(item); });
      box.append(head, items); section.append(box);
    });
    return section;
  }
  function decisionPanel(record) {
    const section = el("section", "detail-section"), current = record.payload.personal_decision, base = {kind: "vacancies", id: record.id, version: record.version};
    section.append(el("h3", "", t("personalDecision")));
    if (current && typeof current === "object") section.append(factList([[t("decisionStatus"), translated(current.status)], [t("reasonLabel"), current.reason ? tx(current.reason) : ""], [t("dateLabel"), current.at ? formatDateTime(current.at) : ""]]));
    const legacy = scalar(record.payload.decision); if (legacy) section.append(factList([[t("researchNote"), tx(legacy)]]));
    const form = el("div", "inline-form"), reason = formInput("text", {maxlength: "1000", placeholder: t("notInterestedReason"), "aria-label": t("notInterestedReason")});
    form.append(reason, requestButton(t("markNotInterested"), "quiet-button", () => { if (!reason.value.trim()) { showNotice(t("reasonRequired")); reason.focus(); return null; } return {type: "vacancy_decision", base, payload: {status: "not_interested", reason: reason.value.trim()}}; }), requestButton(t("markInterested"), "quiet-button", () => ({type: "vacancy_decision", base, payload: {status: "interested"}})));
    if (current) form.append(requestButton(t("clearDecision"), "quiet-button", () => ({type: "vacancy_decision", base, payload: {status: "cleared"}})));
    section.append(form, el("p", "muted small-note", t("decisionHelp")));
    const work = workList(relatedWork(record.id, ["vacancy_decision"])); if (work) section.append(work);
    return section;
  }
  function fitTab(record) {
    const fragment = document.createDocumentFragment(), fit = fitSummary(record), section = el("section", "detail-section first");
    section.append(el("h3", "", t("fitTitle")));
    if (!fit.assessment) section.append(el("p", "muted", t("fitNotAssessedHelp")));
    fit.all.forEach((assessment) => section.append(assessmentView(record, assessment)));
    const form = el("div", "inline-form"), track = trackSelect(tracks(record)[0]);
    form.append(track, requestButton(t("requestEvaluation"), "quiet-button", () => ({type: "evaluate", payload: {vacancy_id: record.id, track: track.value}})), requestButton(t("requestAnnotation"), "quiet-button", () => ({type: "task", payload: {task_type: "annotate_requirements", related: {vacancy_id: record.id, track: track.value}}}), t("taskQueued")));
    section.append(form, el("p", "muted small-note", t("fitRules")));
    const work = workList(relatedWork(record.id, ["evaluate", "annotate_requirements", "clarification_answer"])); if (work) section.append(work);
    fragment.append(section, campaignsPanel(record));
    return fragment;
  }
  function assessmentView(record, assessment) {
    const p = assessment.payload, box = el("div", "assessment-block"), head = el("div", "fit-head"), stale = assessment.display?.stale;
    head.append(el("span", "eyebrow", `${translated(p.track)} · ${formatDateTime(p.at)}`), badge(p.outcome || (isToken(p.decision) ? p.decision : "unknown")));
    box.append(head);
    if (p.reason) box.append(el("p", "fit-reason", p.outcome ? reasonText(p) : tx(p.reason)));
    if (Array.isArray(stale) && stale.length) box.append(el("p", "detail-warning", `${t("staleNotice")}: ${stale.map((part) => t(`input_${part}`)).join(", ")}`));
    else if (!p.outcome || stale === null) box.append(el("p", "muted small-note", t("legacyAssessment")));
    const rows = Array.isArray(p.requirements) ? p.requirements : [];
    if (rows.length) {
      const list = el("ol", "fit-matrix");
      rows.forEach((row) => list.append(requirementRow(record, row)));
      box.append(el("h4", "", t("matrixTitle")), list);
    }
    const limits = Array.isArray(p.constraints) ? p.constraints : [];
    if (limits.length) {
      const list = el("ul", "criteria-list");
      limits.forEach((item) => { const li = el("li"); li.append(el("span", "criterion-name", t(`constraint_${item.name}`)), badge(item.status), el("span", "muted", basisText(item.basis_code, item.basis))); list.append(li); });
      box.append(el("h4", "", t("constraintsTitle")), list);
    }
    const data = p.completeness;
    if (data && typeof data === "object") box.append(el("h4", "", t("completenessTitle")), factList([[t("completeness"), t(`scope_${data.description}`) === `scope_${data.description}` ? scalar(data.description) : t(`scope_${data.description}`)], [t("requirementsCount"), `${data.requirements} · ${t("mandatoryShort")}: ${data.mandatory_requirements}`], [t("verifiedFacts"), String(data.verified_facts_for_track)]]));
    return box;
  }
  function requirementRow(record, row) {
    const item = el("li", `fit-row is-${row.status || (row.covered ? "match" : "unknown")}`), head = el("div", "fit-row-head");
    head.append(el("strong", "", tx(scalar(row.text || row.requirement_id))));
    const tags = el("span", "card-meta"); if (row.mandatory) tags.append(el("span", "badge attention", label("mandatory"))); tags.append(badge(row.category || row.gap_type || "qualification"), badge(row.status || (row.covered ? "match" : "unknown"))); head.append(tags); item.append(head);
    const evidence = Array.isArray(row.evidence) ? row.evidence.map((entry) => typeof entry === "object" ? [entry.fact_id, entry.source].filter(Boolean).join(" — ") : String(entry)).join("; ") : "";
    item.append(factList([[t("evidenceColumn"), evidence || (row.suggested_facts?.length ? `${t("suggestedFacts")}: ${row.suggested_facts.join(", ")}` : "—")], [t("basisLabel"), row.basis ? basisText(row.basis_code, row.basis) : ""], [t("clarificationLabel"), row.clarification ? `${row.clarification.answer} (${formatDateTime(row.clarification.at)})` : ""]]));
    const action = row.action?.type;
    if (action && action !== "none") {
      const bar = el("div", "inline-form fit-action"); bar.append(el("span", "badge blue", t(`action_${action}`)));
      if (action === "cv_edit") bar.append(button(`${t("goToResume")} →`, "text-button", () => { state.detailTab = "resume"; syncHash(); renderVacancyDetail(state.opened || record); }));
      if (action === "preparation") bar.append(button(`${t("goToPrep")} →`, "text-button", () => { state.detailTab = "prep"; syncHash(); renderVacancyDetail(state.opened || record); }));
      if (action === "clarify") {
        const answer = formInput("text", {maxlength: "4000", placeholder: t("clarificationAnswer"), "aria-label": t("clarificationAnswer")});
        bar.append(answer, requestButton(t("saveAnswer"), "quiet-button", () => { if (!answer.value.trim()) { answer.focus(); return null; } return {type: "clarification_answer", base: {kind: "vacancies", id: record.id, version: record.version}, payload: {question: scalar(row.text), answer: answer.value.trim(), requirement_id: row.requirement_id}}; }));
      }
      if (action === "decision_basis") bar.append(el("span", "muted", t("decisionBasisHelp")));
      item.append(bar);
    }
    return item;
  }
  function companyTab(record) {
    const company = companyFor(record), section = el("section", "detail-section first");
    if (!company) { section.append(el("p", "muted", t("companyUnknown"))); return section; }
    const p = company.payload, size = p.size && typeof p.size === "object" ? p.size : {};
    section.append(el("h3", "", recordTitle(company)));
    if (p.needs_review) section.append(el("p", "detail-warning", t("companyNeedsReview")));
    section.append(factList([[label("about"), known(scalar(p.about)) ? tx(scalar(p.about)) : t("notStated")], [label("business_areas"), scalar(p.business_areas)], [label("size"), size.value ? [scalar(size.value), scalar(size.metric), size.as_of ? formatDate(size.as_of) : ""].filter(Boolean).join(" · ") : t("notStated")], [t("country"), geographyValue(geography(company).country, "country")]]));
    const links = [...linksFrom(p.urls || p.url || p.profile_sources || p.source_url || [])].slice(0, 6);
    if (links.length) { const group = el("div", "detail-links"); links.forEach((url, index) => group.append(externalLink(url, `${t("source")} ${index + 1} ↗`))); section.append(group); }
    const dossiers = allRecords().filter((item) => item.kind === "company_dossiers" && item.payload.company_id === company.id);
    if (dossiers.length) { const box = el("div", "stacked-refs"); dossiers.forEach((item) => box.append(recordReference(item))); section.append(el("h4", "", t("companyDossiers")), box); }
    const others = companyVacancies(company).filter((item) => item.id !== record.id);
    if (others.length) { const box = el("div", "stacked-refs"); others.slice(0, 20).forEach((item) => box.append(vacancyReference(item, {compact: true, company: false}))); section.append(el("h4", "", t("otherVacancies")), box); }
    section.append(button(`${t("openCompany")} →`, "text-button", () => openRecord(company)));
    return section;
  }
  function resumeTab(record) {
    const section = el("section", "detail-section first"), packages = records("documents").filter((item) => item.kind === "packages" && item.payload.vacancy_id === record.id);
    section.append(el("h3", "", t("resumeForVacancy")));
    if (!packages.length) section.append(el("p", "muted", t("noVacancyCv")));
    packages.forEach((pkg) => section.append(packageBlock(pkg)));
    const form = el("div", "inline-form"), track = trackSelect(tracks(record)[0]);
    form.append(track, requestButton(t("requestTailorCv"), "primary-button", () => ({type: "task", payload: {task_type: "tailor_cv", related: {vacancy_id: record.id, track: track.value}}}), t("taskQueued")));
    section.append(form, el("p", "muted small-note", t("tailorNote")));
    const work = workList(relatedWork(record.id, ["tailor_cv"])); if (work) section.append(work);
    return section;
  }
  function prepTab(record) {
    const fragment = document.createDocumentFragment(), section = el("section", "detail-section first"), plans = learningFor(record);
    section.append(el("h3", "", t("prepForVacancy")));
    plans.forEach((plan) => { const row = el("div", "vacancy-actions"); row.append(button(recordTitle(plan), "record-reference", () => openPlan(plan))); const pdf = el("a", "text-button", t("downloadPdf")); pdf.href = `/api/plans/learning/${encodeURIComponent(plan.id)}.pdf${state.lang === "en" ? "?lang=en" : ""}`; pdf.setAttribute("download", ""); row.append(pdf); section.append(row); });
    const briefForm = el("div", "inline-form"), track = trackSelect(tracks(record)[0]);
    briefForm.append(track, requestButton(t("requestBrief"), "primary-button", () => ({type: "task", payload: {task_type: "prepare_vacancy_brief", related: {vacancy_id: record.id, track: track.value}}}), t("taskQueued")));
    section.append(briefForm, el("p", "muted small-note", t("briefNote")));
    const coding = record.payload.coding_requirement && typeof record.payload.coding_requirement === "object" ? record.payload.coding_requirement : null, codingBox = el("section", "detail-section");
    codingBox.append(el("h3", "", t("codingTitle")));
    codingBox.append(factList([[t("decisionStatus"), t(`coding_${coding?.status || "unknown"}`)], [t("codingBasis"), coding?.basis ? tx(coding.basis) : ""], [t("source"), coding?.source ? (externalLink(coding.source, coding.source) || coding.source) : ""], [t("dateLabel"), coding?.date ? formatDate(coding.date) : coding?.recorded_at ? formatDate(coding.recorded_at) : ""]]));
    const choice = formSelect(["required", "not_required", "unknown"].map((value) => [value, t(`coding_${value}`)]), coding?.status || "unknown");
    const basis = formInput("text", {maxlength: "1000", placeholder: t("codingBasis"), "aria-label": t("codingBasis")}), source = formInput("text", {maxlength: "500", placeholder: t("codingSource"), "aria-label": t("codingSource")});
    const codingForm = el("div", "inline-form"); choice.setAttribute("aria-label", t("codingTitle"));
    codingForm.append(choice, basis, source, requestButton(t("saveCoding"), "quiet-button", () => { if (!basis.value.trim()) { showNotice(t("codingBasisRequired")); basis.focus(); return null; } return {type: "coding_requirement", base: {kind: "vacancies", id: record.id, version: record.version}, payload: {status: choice.value, basis: basis.value.trim(), source: source.value.trim() || null, date: new Date().toISOString().slice(0, 10)}}; }));
    codingBox.append(codingForm, el("p", "muted small-note", t("codingNote")));
    const briefWork = workList(relatedWork(record.id, ["prepare_vacancy_brief"])); if (briefWork) section.append(briefWork);
    records("preparations").filter((item) => item.kind === "preparation_briefs" && item.payload.vacancy_id === record.id).sort((a, b) => scalar(b.payload.created_at).localeCompare(scalar(a.payload.created_at))).forEach((item) => section.append(briefView(item)));
    const sessions = records("preparations").filter((item) => item.kind === "practice_sessions" && item.payload.vacancy_id === record.id);
    if (sessions.length) { section.append(el("h4", "", t("practiceTitle"))); sessions.forEach((item) => section.append(practiceView(item))); }
    section.append(newPracticeForm({vacancy_id: record.id, track: tracks(record)[0]}));
    const codingWork = workList(relatedWork(record.id, ["coding_requirement"])); if (codingWork) codingBox.append(codingWork);
    fragment.append(section, codingBox);
    return fragment;
  }

  // CV module: master CVs, vacancy versions, edit proposals with decisions and import.
  Object.assign(copy.ru, {
    mastersTitle: "Master-резюме", mastersDesc: "Ровно одно master-резюме на трек. Версии под вакансии их не меняют.", noMaster: "Master-резюме для этого трека ещё нет.", requestFixMaster: "Поставить задачу: исправить master", cvState: "Состояние", versionsCount: "Версий", basedOn: "Основано на", previewPdf: "Предпросмотр PDF", sourceText: "Исходник (Markdown)", extractedText: "Извлечённый из PDF текст", reviewFindings: "Замечания ревью", requirementCoverage: "Покрытие требований", coverage_covered: "покрыто", coverage_not_evidenced: "нет подтверждения", coverage_not_applicable: "неприменимо",
    proposalsTitle: "Предложения правок", proposalsDesc: "Было → стало → причина → факт. Принятие правки не заменяет содержательное и визуальное ревью: новая версия создаётся автором и проходит проверки.", noProposals: "Предложений правок нет.", editBefore: "Было", editAfter: "Стало", editReason: "Причина", editFacts: "Факты", editRequirements: "Требования", editQuestion: "Вопрос кандидату", acceptEdit: "Принять", rejectEdit: "Отклонить", editEdit: "Отредактировать", saveEdited: "Сохранить свой вариант", noDecision: "решения нет", decisionsProgress: "решено", insertIntoSection: "вставка в раздел",
    vacancyVersionsTitle: "Версии под вакансии", noVacancyVersions: "Версий под вакансии пока нет.",
    importTitle: "Импорт резюме", importDesc: "Вставьте текст резюме. Разделы, даты и утверждения извлекаются для проверки; факты создаются только после подтверждения через ajh facts import.", importText: "Текст резюме", importFilename: "Имя файла", importSubmit: "Сохранить заявку на импорт", importNeedsText: "Вставьте текст резюме (не короче 100 символов).", importsList: "Импортированные резюме", importSections: "Разделы", importDates: "Периоды", importClaims: "Утверждения для проверки",
    cvReason_mechanical_source: "Механический черновик — нужен автор (флагманская модель)", cvReason_coverage_unreconciled: "Матрица фактов не сверена", cvReason_no_reviews: "Следующий шаг — содержательное ревью", cvReason_content_review_missing_or_failed: "Содержательное ревью не пройдено", cvReason_visual_review_missing_or_failed: "Визуальное ревью не пройдено", cvReason_review_status_pending: "Статус ревью ещё не подтверждён"
  });
  Object.assign(copy.en, {
    mastersTitle: "Master CVs", mastersDesc: "Exactly one master CV per track. Vacancy versions never change them.", noMaster: "No master CV for this track yet.", requestFixMaster: "Queue task: fix the master", cvState: "State", versionsCount: "Versions", basedOn: "Based on", previewPdf: "PDF preview", sourceText: "Source (Markdown)", extractedText: "Text extracted from the PDF", reviewFindings: "Review findings", requirementCoverage: "Requirement coverage", coverage_covered: "covered", coverage_not_evidenced: "not evidenced", coverage_not_applicable: "not applicable",
    proposalsTitle: "Proposed edits", proposalsDesc: "Before → after → reason → fact. Accepting an edit does not replace the content and visual reviews: a new version is authored and checked.", noProposals: "No proposed edits.", editBefore: "Before", editAfter: "After", editReason: "Reason", editFacts: "Facts", editRequirements: "Requirements", editQuestion: "Question for the candidate", acceptEdit: "Accept", rejectEdit: "Reject", editEdit: "Edit", saveEdited: "Save my version", noDecision: "no decision", decisionsProgress: "decided", insertIntoSection: "insert into section",
    vacancyVersionsTitle: "Vacancy versions", noVacancyVersions: "No vacancy versions yet.",
    importTitle: "Import a CV", importDesc: "Paste the CV text. Sections, dates and claims are extracted for checking; facts are created only after confirmation through ajh facts import.", importText: "CV text", importFilename: "File name", importSubmit: "Save import request", importNeedsText: "Paste the CV text (at least 100 characters).", importsList: "Imported CVs", importSections: "Sections", importDates: "Periods", importClaims: "Claims to check",
    cvReason_mechanical_source: "Mechanical draft; a flagship author is needed", cvReason_coverage_unreconciled: "The fact matrix is not reconciled", cvReason_no_reviews: "Next: content review", cvReason_content_review_missing_or_failed: "Content review not passed", cvReason_visual_review_missing_or_failed: "Visual review not passed", cvReason_review_status_pending: "Review status not confirmed yet"
  });
  Object.assign(enums, {written: ["Написано", "Written"], awaiting_facts: ["Ждёт фактов", "Awaiting facts"], awaiting_content_review: ["Ждёт содержательного ревью", "Awaiting content review"], awaiting_visual_review: ["Ждёт визуального ревью", "Awaiting visual review"], invalid: ["Нарушена целостность", "Integrity broken"], accept: ["Принято", "Accepted"], reject: ["Отклонено", "Rejected"], edit: ["Отредактировано", "Edited"], wording: ["Формулировка", "Wording"], emphasis: ["Акцент", "Emphasis"], reorder: ["Порядок", "Order"], add_evidence: ["Добавить доказательство", "Add evidence"], remove: ["Удалить", "Remove"], master: ["Master", "Master"]});
  const currentVersion = (pkg) => { const versions = Array.isArray(pkg.payload.versions) ? pkg.payload.versions : []; return versions.find((version) => version.id === pkg.payload.current_version) || versions.at(-1) || null; };
  function lazyPdf(path, label) {
    const details = el("details", "pdf-preview"), summary = el("summary", "", label || t("previewPdf"));
    details.append(summary);
    details.addEventListener("toggle", () => { if (!details.open || details.querySelector("iframe")) return; const frame = el("iframe"); frame.src = "/api/preview/" + (state.artifactAliases?.get(path) || path).split("/").map(encodeURIComponent).join("/"); frame.title = label || t("previewPdf"); frame.loading = "lazy"; details.append(frame); });
    return details;
  }
  function packageBlock(pkg) {
    const version = currentVersion(pkg), box = el("div", "assessment-block cv-version"), head = el("div", "fit-head");
    if (!version) { box.append(el("p", "muted", t("noVacancyCv"))); return box; }
    const info = pkg.display?.versions?.[version.id] || {}, files = version.files || {};
    head.append(el("strong", "", recordTitle(pkg)), badge(info.state || "unknown")); box.append(head);
    if (Array.isArray(info.reasons) && info.reasons.length) box.append(el("p", "muted small-note", info.reasons.map((code) => t(`cvReason_${code}`) === `cvReason_${code}` ? code : t(`cvReason_${code}`)).join(" · ")));
    const origin = version.based_on && typeof version.based_on === "object" ? `${version.based_on.package_id} · ${version.based_on.version_id}` : "";
    box.append(factList([[t("currentVersion"), [scalar(version.id), version.date ? formatDate(version.date) : ""].filter(Boolean).join(" · ")], [t("versionsCount"), String((pkg.payload.versions || []).length)], [t("basedOn"), origin], [label("author_model"), scalar(version.author_model)]]));
    const links = el("div", "vacancy-actions");
    if (files.cv_source) links.append(button(t("sourceText"), "text-button", () => openDocument(resolved(files.cv_source), {title: recordTitle(pkg)})));
    if (files.cv_text) links.append(button(t("extractedText"), "text-button", () => openDocument(resolved(files.cv_text), {title: recordTitle(pkg)})));
    const resolved = (value) => state.artifactAliases?.get(value) || value;
    if (files.cv_pdf) { const pdf = el("a", "text-button", t("downloadPdf")); pdf.href = "/api/artifacts/" + resolved(files.cv_pdf).split("/").map(encodeURIComponent).join("/"); links.append(pdf); }
    links.append(button(`${t("openPackage")} →`, "text-button", () => openRecord(pkg)));
    box.append(links);
    if (files.cv_pdf) box.append(lazyPdf(files.cv_pdf));
    const coverage = Array.isArray(info.requirement_coverage) ? info.requirement_coverage : [];
    if (coverage.length) { const vacancy = byId(pkg.payload.vacancy_id, "vacancies"), list = el("ul", "criteria-list"); coverage.forEach((row) => { const requirement = (vacancy?.payload.requirements || []).find((item) => item.id === row.requirement_id); const item = el("li"); item.append(el("span", "criterion-name", tx(scalar(requirement?.text || row.requirement_id))), badge(row.status === "covered" ? "match" : row.status === "not_evidenced" ? "gap" : "unknown"), el("span", "muted", [t(`coverage_${row.status}`), row.cv_location, (row.fact_ids || []).join(", ")].filter(Boolean).join(" · "))); list.append(item); }); box.append(el("h4", "", t("requirementCoverage")), list); }
    const findings = Array.isArray(info.findings) ? info.findings : [];
    if (findings.length) { const list = el("ul", "work-list"); findings.forEach((review) => { const item = el("li"); item.append(badge(review.passed ? "passed" : "failed"), el("span", "", `${translated(review.kind)}: ${(Array.isArray(review.findings) ? review.findings : [review.findings]).map(scalar).filter(Boolean).join("; ")}`)); list.append(item); }); box.append(el("h4", "", t("reviewFindings")), list); }
    return box;
  }
  function renderResume(list) {
    const container = el("div", "sources-view"), packages = list.filter((record) => record.kind === "packages"), trackFilter = state.filters.track || "";
    const masters = el("section", "view-section"); masters.append(el("h2", "view-title", t("mastersTitle")), el("p", "muted", t("mastersDesc")));
    const grid = el("div", "records-grid");
    TRACK_OPTIONS.filter((track) => !trackFilter || track === trackFilter).forEach((track) => {
      const card = el("article", "record-card"), pkg = packages.find((item) => item.payload.vacancy_id === "master" && item.payload.track === track);
      card.append(el("p", "company-label", translated(track)));
      if (pkg) card.append(packageBlock(pkg)); else card.append(el("p", "muted", t("noMaster")));
      const form = el("div", "inline-form"); form.append(requestButton(t("requestFixMaster"), "quiet-button", () => ({type: "task", payload: {task_type: "fix_master_cv", related: {track, ...(pkg ? {package_id: pkg.id, version_id: pkg.payload.current_version} : {})}}}), t("taskQueued"))); card.append(form);
      const work = workList({pending: (state.data?.pending_requests || []).filter((request) => request.payload?.task_type === "fix_master_cv" && request.payload?.related?.track === track), requests: [], tasks: workRecords("tasks").map((item) => item.payload).filter((task) => task.type === "fix_master_cv" && task.related?.track === track)}); if (work) card.append(work);
      grid.append(card);
    });
    masters.append(grid);
    const proposals = el("section", "view-section"), edits = list.filter((record) => record.kind === "cv_edits" && (!trackFilter || record.payload.track === trackFilter));
    proposals.append(el("h2", "view-title", t("proposalsTitle")), el("p", "muted", t("proposalsDesc")));
    if (edits.length) edits.sort((a, b) => scalar(b.payload.created_at).localeCompare(scalar(a.payload.created_at))).forEach((record) => proposals.append(proposalBlock(record, list))); else proposals.append(el("p", "muted", t("noProposals")));
    const versions = el("section", "view-section"), tailored = packages.filter((item) => item.payload.vacancy_id !== "master" && (!trackFilter || item.payload.track === trackFilter));
    versions.append(el("h2", "view-title", t("vacancyVersionsTitle")));
    if (tailored.length) tailored.forEach((pkg) => { const vacancy = byId(pkg.payload.vacancy_id, "vacancies"); const group = el("div", "cv-group"); if (vacancy) group.append(vacancyReference(vacancy, {compact: true})); group.append(packageBlock(pkg)); versions.append(group); }); else versions.append(el("p", "muted", t("noVacancyVersions")));
    container.append(masters, proposals, versions, importView(list));
    return container;
  }
  function proposalBlock(record, list) {
    const p = record.payload, box = el("article", "assessment-block proposal"), head = el("div", "fit-head");
    const history = list.filter((item) => item.kind === "cv_edit_decisions" && item.payload.proposal_id === record.id).sort((a, b) => (a.payload.sequence || 0) - (b.payload.sequence || 0));
    const latest = {}; history.forEach((item) => { latest[item.payload.edit_id] = item.payload; });
    const pkg = byId(p.package_id, "packages");
    head.append(el("strong", "", pkg ? recordTitle(pkg) : p.package_id), el("span", "muted small-note", `${translated(p.scope)} · ${p.version_id} · ${formatDateTime(p.created_at)} · ${t("decisionsProgress")} ${Object.keys(latest).length}/${(p.edits || []).length}`));
    box.append(head);
    const pending = (state.data?.pending_requests || []).filter((request) => request.type === "cv_edit_decision" && request.payload?.proposal_id === record.id);
    (p.edits || []).forEach((edit) => {
      const item = el("div", "edit-row"), top = el("div", "fit-row-head"), decision = latest[edit.id], waiting = pending.filter((request) => request.payload.edit_id === edit.id);
      top.append(el("span", "card-meta"), el("span", "card-meta")); top.firstChild.append(badge(edit.kind)); top.lastChild.append(waiting.length ? badge("pending") : decision ? badge(decision.decision) : el("span", "muted small-note", t("noDecision")));
      item.append(top);
      const diff = el("div", "edit-diff"), before = el("div", "edit-before"), after = el("div", "edit-after");
      before.append(el("span", "eyebrow", t("editBefore")), el("p", "", edit.before || `— ${t("insertIntoSection")}: ${edit.section}`));
      after.append(el("span", "eyebrow", t("editAfter")), el("p", "", decision?.decision === "edit" ? decision.text : edit.after || "—"));
      diff.append(before, after); item.append(diff);
      item.append(factList([[t("editReason"), tx(edit.reason)], [t("editFacts"), (edit.fact_ids || []).join(", ")], [t("editRequirements"), (edit.requirement_ids || []).join(", ")], [t("editQuestion"), edit.needs_candidate_input ? tx(scalar(edit.question)) : ""]]));
      const base = {kind: "cv_edits", id: record.id, version: record.version}, bar = el("div", "inline-form");
      const body = (decisionValue, text) => ({type: "cv_edit_decision", base, payload: {proposal_id: record.id, edit_id: edit.id, decision: decisionValue, ...(text ? {text} : {})}});
      bar.append(requestButton(t("acceptEdit"), "quiet-button", () => body("accept")), requestButton(t("rejectEdit"), "quiet-button", () => body("reject")));
      if (edit.kind !== "remove") {
        const editor = el("details", "form-details inline-editor"), area = formInput("textarea", {rows: "3", maxlength: "4000", "aria-label": t("editAfter")}); area.value = decision?.text || edit.after;
        editor.append(el("summary", "", t("editEdit")), area, requestButton(t("saveEdited"), "primary-button", () => area.value.trim() ? body("edit", area.value.trim()) : null));
        bar.append(editor);
      }
      item.append(bar); box.append(item);
    });
    return box;
  }
  function importView(list) {
    const section = el("section", "view-section"), details = el("details", "form-details"), form = el("div", "form-grid");
    const track = trackSelect(state.filters.track), filename = formInput("text", {maxlength: "120", value: "cv.md"}), text = formInput("textarea", {rows: "10", maxlength: "35000"});
    form.append(formField(t("trackField"), track), formField(t("importFilename"), filename), formField(t("importText"), text, true));
    details.append(el("summary", "", t("importTitle")), form, requestButton(t("importSubmit"), "primary-button", () => text.value.trim().length < 100 ? (showNotice(t("importNeedsText")), null) : {type: "cv_import", payload: {track: track.value, text: text.value, filename: filename.value.trim() || "cv.md"}}, t("taskQueued")));
    section.append(el("h2", "view-title", t("importTitle")), el("p", "muted", t("importDesc")), details);
    const imports = list.filter((record) => record.kind === "cv_imports");
    if (imports.length) {
      const box = el("div", "stacked-refs");
      imports.forEach((record) => { const p = record.payload, item = el("div", "assessment-block"), task = workRecords("tasks").find((entry) => entry.id === p.task_id); item.append(el("strong", "", `${p.filename} · ${translated(p.track)} · ${formatDateTime(p.imported_at)}`)); item.append(factList([[t("importSections"), (p.sections || []).map((s) => s.title).filter(Boolean).join(", ")], [t("importDates"), String((p.dates || []).length)], [t("task_extract_cv_facts"), task ? translated(task.payload.status) : ""]])); if ((p.claims_to_check || []).length) { const claims = el("details", "link-details"), ul = el("ul", "plain-list"); claims.append(el("summary", "", `${t("importClaims")} · ${p.claims_to_check.length}`)); p.claims_to_check.slice(0, 50).forEach((line) => ul.append(el("li", "", line))); claims.append(ul); item.append(claims); } if (p.text?.path) item.append(button(t("extractedText"), "text-button", () => openDocument(p.text.path))); box.append(item); });
      section.append(el("h3", "", t("importsList")), box);
    }
    return section;
  }

  // Preparation module: vacancy briefs (mode A), track plans for general gaps (mode B), text practice.
  const PREP_KINDS = new Set(["track_plans", "preparation_briefs", "practice_sessions", "practice_attempts", "practice_reviews"]);
  Object.assign(copy.ru, {
    prepEntryVacancy: "К вакансии", prepEntryVacancyDesc: "Компания, этапы, вопросы, истории и памятка с источниками. Резюме и назначенное интервью не требуются.", chooseVacancy: "Вакансия", prepEntryGaps: "Общие пробелы", prepEntryGapsDesc: "Направление, цель, время и опыт → темы из пробелов по вакансиям (дубли не добавляют вес) или базовая подготовка → практика → разбор → повтор.", goalField: "Цель", hoursField: "Часов в неделю", experienceField: "Опыт (кратко, необязательно)", createPlan: "Составить план", goalRequired: "Укажите цель и часы.",
    trackPlansTitle: "Планы по общим пробелам", basis_vacancies: "из пробелов вакансий", basis_baseline: "базовая подготовка по направлению — не из требований вакансий", topicWhy: "Почему", topicWhere: "Где найдено", topicWeight: "Вес (разных ролей)", topicCriterion: "Критерий", topicExercise: "Упражнение", topicMaterials: "Материалы", topic_open: "не начато", topic_attempted: "есть попытка", topic_reviewed: "есть разбор", practiceTopic: "Практиковать", requestMaterials: "Поставить задачу: подобрать материалы", readingNote: "Чтение материалов не закрывает пробел — статус меняет только разобранная попытка.",
    briefsTitle: "Памятки к вакансиям", briefCompany: "Компания", briefRole: "Роль и интервью", briefQuestions: "Вопросы", briefStories: "Истории STAR", briefPlan: "План", briefSummary: "Памятка", claim_confirmed: "подтверждено", claim_participant_report: "со слов участников", claim_assumption: "допущение", provenance_published: "опубликован", provenance_generated: "сгенерирован", storyGaps: "Не хватает историй", employerQuestions: "Вопросы работодателю", tests: "Что проверяет",
    practiceTitle: "Практика", newPractice: "Новый вопрос для практики", questionField: "Вопрос", typeField: "Тип", testsField: "Что проверяет", provenanceField: "Происхождение", createSession: "Создать", questionRequired: "Укажите вопрос и что он проверяет.", answerField: "Ваш ответ", submitAnswer: "Отправить ответ на разбор", retryAnswer: "Повторить попытку", followUpAnswer: "Ответить на уточнение", awaitingReview: "ждёт разбора агентом", reviewTitle: "Разбор", attemptLabel: "Попытка", reviewProblem: "Проблема", reviewImprovement: "Как улучшить", followUpLabel: "Уточняющий вопрос", retryQuestion: "Вопрос для повтора", practiceNote: "Практика не создаёт опыт и не меняет резюме. Подтверждённый прогресс фиксирует независимый проверяющий.", draftSaved: "черновик сохранён в браузере", answerRequired: "Напишите ответ.",
    attemptKind_answer: "ответ", attemptKind_retry: "повтор", attemptKind_follow_up: "ответ на уточнение", qtype_behavioral: "поведенческий", qtype_leadership: "лидерство", qtype_product_case: "продуктовый кейс", qtype_system_design: "системный дизайн", qtype_self_presentation: "самопрезентация", qtype_coding: "coding"
  });
  Object.assign(copy.en, {
    prepEntryVacancy: "For a vacancy", prepEntryVacancyDesc: "Company, stages, questions, stories and a brief with sources. No CV or scheduled interview is required.", chooseVacancy: "Vacancy", prepEntryGaps: "General gaps", prepEntryGapsDesc: "Direction, goal, time and experience → topics from vacancy gaps (duplicates add no weight) or baseline preparation → practice → review → retry.", goalField: "Goal", hoursField: "Hours per week", experienceField: "Experience (short, optional)", createPlan: "Build plan", goalRequired: "Give a goal and hours.",
    trackPlansTitle: "Plans for general gaps", basis_vacancies: "from vacancy gaps", basis_baseline: "baseline preparation for the direction — not from vacancy requirements", topicWhy: "Why", topicWhere: "Found in", topicWeight: "Weight (distinct roles)", topicCriterion: "Criterion", topicExercise: "Exercise", topicMaterials: "Materials", topic_open: "not started", topic_attempted: "attempted", topic_reviewed: "reviewed", practiceTopic: "Practice", requestMaterials: "Queue task: find materials", readingNote: "Reading materials does not close a gap; only a reviewed attempt changes the status.",
    briefsTitle: "Vacancy briefs", briefCompany: "Company", briefRole: "Role and interview", briefQuestions: "Questions", briefStories: "STAR stories", briefPlan: "Plan", briefSummary: "Brief", claim_confirmed: "confirmed", claim_participant_report: "participant report", claim_assumption: "assumption", provenance_published: "published", provenance_generated: "generated", storyGaps: "Missing stories", employerQuestions: "Questions for the employer", tests: "What it tests",
    practiceTitle: "Practice", newPractice: "New practice question", questionField: "Question", typeField: "Type", testsField: "What it tests", provenanceField: "Provenance", createSession: "Create", questionRequired: "Give the question and what it tests.", answerField: "Your answer", submitAnswer: "Send the answer for review", retryAnswer: "Retry", followUpAnswer: "Answer the follow-up", awaitingReview: "awaiting review by an agent", reviewTitle: "Review", attemptLabel: "Attempt", reviewProblem: "Problem", reviewImprovement: "How to improve", followUpLabel: "Follow-up question", retryQuestion: "Retry question", practiceNote: "Practice creates no experience and never changes the CV. Confirmed progress is recorded by an independent reviewer.", draftSaved: "draft saved in this browser", answerRequired: "Write an answer.",
    attemptKind_answer: "answer", attemptKind_retry: "retry", attemptKind_follow_up: "follow-up answer", qtype_behavioral: "behavioral", qtype_leadership: "leadership", qtype_product_case: "product case", qtype_system_design: "system design", qtype_self_presentation: "self-presentation", qtype_coding: "coding"
  });
  Object.assign(enums, {reviewed: ["Разобрано", "Reviewed"], attempted: ["Есть попытка", "Attempted"], baseline: ["Базовый план", "Baseline"]});
  const PREP_TEXT_RU = {"Product sense and discovery": "Продуктовое мышление и исследование", "Strategy and prioritization": "Стратегия и приоритизация", "Metrics and experiments": "Метрики и эксперименты", "Pricing, GTM and unit economics": "Ценообразование, выход на рынок и юнит-экономика", "Stakeholder leadership": "Работа со стейкхолдерами", "Self-presentation": "Самопрезентация", "Architecture and system design": "Архитектура и системный дизайн", "Distributed systems and trade-offs": "Распределённые системы и компромиссы", "Reliability and incident analysis": "Надёжность и разбор инцидентов", "Engineering organization and delivery": "Инженерная организация и поставка", "Hiring, feedback and team growth": "Найм, обратная связь и развитие команды", "Frame a problem, segments and success criteria": "Сформулировать проблему, сегменты и критерии успеха", "Choose between alternatives and explain trade-offs": "Выбрать из альтернатив и объяснить компромиссы", "Design a testable experiment with a guardrail metric": "Спроектировать проверяемый эксперимент с защитной метрикой", "Ground a pricing decision in inputs and constraints": "Обосновать ценовое решение входными данными и ограничениями", "Describe influencing without authority with a real story": "Рассказать реальную историю влияния без формальной власти", "Two-minute story of the career path and motivation": "Двухминутный рассказ о карьерном пути и мотивации", "Design a service with explicit trade-offs": "Спроектировать сервис с явными компромиссами", "Explain consistency and failure handling": "Объяснить согласованность и обработку сбоев", "Analyse an incident and propose SLOs": "Разобрать инцидент и предложить SLO", "Explain how delivery and quality were improved": "Объяснить, как улучшались поставка и качество", "A real story about developing an engineer": "Реальная история о развитии инженера", "Baseline preparation for the direction; not derived from vacancy requirements": "Базовая подготовка по направлению; не из требований вакансий", "Preparation gap in vacancy requirements": "Пробел подготовки в требованиях вакансий", "A reviewed answer that meets the rubric on a retry": "Разобранный ответ, который на повторе соответствует критериям", "A reviewed answer or exercise that meets the requirement without new CV claims": "Разобранный ответ или упражнение, которое закрывает требование без новых утверждений в резюме"};
  const prepText = (value) => { const text = scalar(value); if (state.lang !== "ru") return tx(text); if (PREP_TEXT_RU[text]) return PREP_TEXT_RU[text]; const exercise = text.match(/^(?:Explain or solve a realistic case for|How would you demonstrate): (.*?)\??$/); return exercise ? `${text.startsWith("How") ? "Как бы вы показали" : "Объяснить или решить реалистичный кейс"}: ${tx(exercise[1])}` : tx(text); };
  const prepRecords = (kind) => (state.data?.preparations || []).filter((record) => record.kind === kind);
  function renderPreparationModule(list) {
    const container = el("div", "sources-view"), entries = el("section", "view-section"), grid = el("div", "records-grid");
    const vacancyEntry = el("article", "record-card"), vacancies = primaryRecords("vacancies").filter((record) => !inactiveVacancy(record)).sort((a, b) => recordTitle(a).localeCompare(recordTitle(b), state.lang));
    const choice = formSelect(vacancies.map((record) => [record.id, `${recordTitle(record)} · ${companyName(record)}`]), vacancies[0]?.id || "");
    vacancyEntry.append(el("h3", "", t("prepEntryVacancy")), el("p", "muted small-note", t("prepEntryVacancyDesc")), formField(t("chooseVacancy"), choice), button(`${t("tab_prep")} →`, "primary-button", () => { const record = byId(choice.value, "vacancies"); if (record) openRecord(record, "prep"); }));
    const gapsCard = el("article", "record-card"), track = trackSelect(state.filters.track), goal = formInput("text", {maxlength: "500"}), hours = formInput("number", {min: "1", max: "80", step: "1", value: "6"}), experience = formInput("text", {maxlength: "2000"});
    gapsCard.append(el("h3", "", t("prepEntryGaps")), el("p", "muted small-note", t("prepEntryGapsDesc")), formField(t("trackField"), track), formField(t("goalField"), goal), formField(t("hoursField"), hours), formField(t("experienceField"), experience), requestButton(t("createPlan"), "primary-button", () => { const value = Number(hours.value); if (!goal.value.trim() || !(value > 0)) { showNotice(t("goalRequired")); return null; } return {type: "prep_plan", payload: {track: track.value, goal: goal.value.trim(), hours: value, experience: experience.value.trim() || null}}; }));
    grid.append(vacancyEntry, gapsCard); entries.append(grid);
    const trackFilter = state.filters.track || "", plans = prepRecords("track_plans").filter((record) => !trackFilter || record.payload.track === trackFilter).sort((a, b) => scalar(b.payload.created_at).localeCompare(scalar(a.payload.created_at)));
    const plansSection = el("section", "view-section"); plansSection.append(el("h2", "view-title", t("trackPlansTitle")), el("p", "muted", t("readingNote")));
    plans.forEach((record) => plansSection.append(trackPlanView(record)));
    const briefs = prepRecords("preparation_briefs"), briefsSection = el("section", "view-section");
    if (briefs.length) { briefsSection.append(el("h2", "view-title", t("briefsTitle"))); briefs.forEach((record) => { const vacancy = byId(record.payload.vacancy_id, "vacancies"); if (vacancy) briefsSection.append(vacancyReference(vacancy, {compact: true})); briefsSection.append(briefView(record)); }); }
    const sessions = prepRecords("practice_sessions").filter((record) => !record.payload.vacancy_id), practice = el("section", "view-section");
    practice.append(el("h2", "view-title", t("practiceTitle")), el("p", "muted", t("practiceNote")));
    sessions.forEach((record) => practice.append(practiceView(record)));
    practice.append(newPracticeForm({track: trackFilter || undefined}));
    const work = workList({pending: (state.data?.pending_requests || []).filter((request) => ["prep_plan", "prep_create", "practice_answer"].includes(request.type)), requests: workRecords("inbox_requests").map((item) => item.payload).filter((request) => ["prep_plan", "prep_create", "practice_answer"].includes(request.type) && ["failed", "conflict", "rejected"].includes(request.status)), tasks: []});
    if (work) practice.append(work);
    container.append(entries, plansSection, briefsSection, practice, renderPreparations(list));
    return container;
  }
  function trackPlanView(record) {
    const p = record.payload, box = el("article", "plan"), head = el("header", "plan-header"), statuses = record.display?.topic_status || {};
    const heading = el("div", "plan-heading"); heading.append(el("p", "eyebrow", `${translated(p.track)} · ${formatDateTime(p.created_at)}`), el("h2", "plan-title", scalar(p.goal)));
    const meta = el("div", "card-meta"); meta.append(badge(p.basis?.kind === "baseline" ? "baseline" : "current"), el("span", "muted small-note", t(`basis_${p.basis?.kind || "baseline"}`)), el("span", "muted small-note", `${p.hours_per_week} ${t("hoursShort")}/${t("weeksShort")}`)); heading.append(meta); head.append(heading); box.append(head);
    const list = el("ol", "fit-matrix");
    (p.topics || []).forEach((topic) => {
      const item = el("li", `fit-row is-${statuses[topic.id] === "reviewed" ? "match" : statuses[topic.id] === "attempted" ? "unknown" : "gap"}`), top = el("div", "fit-row-head");
      top.append(el("strong", "", prepText(topic.title))); const tags = el("span", "card-meta"); tags.append(badge(topic.type), el("span", "badge", t(`topic_${statuses[topic.id] || "open"}`))); top.append(tags); item.append(top);
      const where = el("div", "stacked-refs"); (topic.where_found || []).forEach((id) => { const vacancy = byId(id, "vacancies"); if (vacancy) where.append(vacancyReference(vacancy, {compact: true, date: false})); });
      item.append(factList([[t("topicWhy"), prepText(topic.why)], [t("topicWhere"), where.childElementCount ? where : ""], [t("topicWeight"), topic.weight ? String(topic.weight) : ""], [t("topicExercise"), prepText(topic.exercise)], [t("topicCriterion"), prepText(topic.criterion)], [t("topicMaterials"), (topic.materials || []).length ? renderValue(topic.materials, "materials") : ""]]));
      const bar = el("div", "inline-form");
      bar.append(requestButton(t("practiceTopic"), "quiet-button", () => ({type: "prep_create", payload: {track: p.track, plan_id: record.id, topic_id: topic.id, question: scalar(topic.diagnostic_question || topic.exercise), type: ["behavioral", "leadership", "product_case", "system_design", "self_presentation"].includes(topic.type) ? topic.type : "behavioral", tests: scalar(topic.criterion), provenance: "generated"}})));
      item.append(bar);
      const sessions = prepRecords("practice_sessions").filter((session) => session.payload.plan_id === record.id && session.payload.topic_id === topic.id);
      sessions.forEach((session) => item.append(practiceView(session)));
      list.append(item);
    });
    box.append(list);
    const actions = el("div", "inline-form"); actions.append(requestButton(t("requestMaterials"), "quiet-button", () => ({type: "task", payload: {task_type: "track_plan_materials", related: {plan_id: record.id, track: p.track}}}), t("taskQueued"))); box.append(actions);
    return box;
  }
  function claimList(claims) {
    const list = el("ul", "criteria-list");
    (claims || []).forEach((claim) => { const item = el("li"); item.append(el("span", `badge ${claim.kind === "confirmed" ? "good" : claim.kind === "assumption" ? "attention" : "blue"}`, t(`claim_${claim.kind}`)), el("span", "", tx(scalar(claim.text)))); (claim.sources || []).forEach((source) => { const link = externalLink(source.url, `${new URL(source.url).hostname.replace(/^www\./, "")} · ${source.date} ↗`); if (link) item.append(link); }); list.append(item); });
    return list;
  }
  function briefView(record) {
    const p = record.payload, box = el("details", "form-details brief"), body = el("div", "brief-body");
    box.append(el("summary", "", `${t("briefSummary")} · ${translated(p.track)} · ${formatDateTime(p.created_at)}`));
    if (p.brief) body.append(el("p", "fit-reason", tx(p.brief)));
    body.append(el("h4", "", t("briefCompany")), claimList(p.company?.claims));
    body.append(el("h4", "", t("briefRole")));
    if ((p.role?.tasks || []).length) { const tasks = el("ul", "plain-list"); p.role.tasks.forEach((task) => tasks.append(el("li", "", tx(task)))); body.append(tasks); }
    body.append(claimList((p.interview?.stages || []).map((stage) => ({kind: stage.kind, text: [stage.name, stage.format].filter(Boolean).join(" — "), sources: stage.sources}))));
    body.append(factList([[t("codingTitle"), `${t(`coding_${p.coding?.status || "unknown"}`)}${p.coding?.basis ? ` — ${tx(p.coding.basis)}` : ""}`]]));
    if ((p.questions || []).length) { const list = el("ul", "criteria-list"); p.questions.forEach((question) => { const item = el("li"); item.append(el("span", "badge", t(`qtype_${question.type}`)), el("span", "badge blue", t(`provenance_${question.provenance}`)), el("span", "", tx(question.text)), el("span", "muted", `${t("tests")}: ${tx(question.tests)}`)); list.append(item); }); body.append(el("h4", "", t("briefQuestions")), list); }
    if ((p.stories || []).length) { const list = el("ul", "plain-list"); p.stories.forEach((story) => list.append(el("li", "", `${story.title}: ${story.situation} → ${story.task} → ${story.action} → ${story.result} (${(story.fact_ids || []).join(", ")})`))); body.append(el("h4", "", t("briefStories")), list); }
    if ((p.story_gaps || []).length) body.append(factList([[t("storyGaps"), p.story_gaps.map(tx).join("; ")]]));
    if ((p.plan || []).length) body.append(el("h4", "", t("briefPlan")), tableFrom([[t("dateLabel"), label("hours"), t("focusColumn")], ...p.plan.map((step) => [step.when, String(step.hours), tx(step.focus)])]));
    if ((p.employer_questions || []).length) { const list = el("ul", "plain-list"); p.employer_questions.forEach((question) => list.append(el("li", "", tx(question)))); body.append(el("h4", "", t("employerQuestions")), list); }
    box.append(body); return box;
  }
  function highlighted(text, fragments) {
    const container = el("p", "practice-answer"), spans = [];
    fragments.forEach((fragment) => { let from = 0; while (fragment && (from = text.indexOf(fragment, from)) >= 0) { spans.push([from, from + fragment.length]); from += fragment.length; } });
    spans.sort((a, b) => a[0] - b[0]); let cursor = 0;
    spans.forEach(([start, end]) => { if (start < cursor) return; container.append(document.createTextNode(text.slice(cursor, start)), el("mark", "", text.slice(start, end))); cursor = end; });
    container.append(document.createTextNode(text.slice(cursor)));
    return container;
  }
  function practiceView(session) {
    const p = session.payload, box = el("div", "assessment-block practice"), attempts = prepRecords("practice_attempts").filter((item) => item.payload.session_id === session.id).sort((a, b) => a.payload.number - b.payload.number);
    const reviews = prepRecords("practice_reviews"), pending = (state.data?.pending_requests || []).filter((request) => request.type === "practice_answer" && request.payload?.session_id === session.id);
    const head = el("div", "fit-head"); head.append(el("strong", "", prepText(p.question)), el("span", "card-meta")); head.lastChild.append(badge(p.type), el("span", "badge blue", t(`provenance_${p.provenance}`))); box.append(head, el("p", "muted small-note", `${t("tests")}: ${prepText(p.tests)}`));
    let lastReview = null, lastAttempt = null;
    attempts.forEach((attempt) => {
      const a = attempt.payload, review = reviews.find((item) => item.payload.attempt_id === attempt.id), row = el("div", "edit-row");
      row.append(el("span", "eyebrow", `${t("attemptLabel")} ${a.number} · ${t(`attemptKind_${a.kind}`)} · ${formatDateTime(a.submitted_at)}`));
      const holder = el("div"); row.append(holder);
      artifactText(a.answer.path).then((text) => holder.replaceChildren(highlighted(text, review ? review.payload.items.map((item) => item.fragment) : []))).catch(() => holder.replaceChildren(el("p", "detail-warning", t("planUnavailable"))));
      if (review) {
        const list = el("ul", "criteria-list"); review.payload.items.forEach((item) => { const li = el("li"); li.append(el("mark", "", item.fragment), el("span", "criterion-name", item.criterion), el("span", "", `${t("reviewProblem")}: ${item.problem}`), el("span", "muted", `${t("reviewImprovement")}: ${item.improvement}`)); list.append(li); });
        row.append(el("h4", "", t("reviewTitle")), list, factList([[t("followUpLabel"), scalar(review.payload.follow_up)], [t("retryQuestion"), scalar(review.payload.retry?.question)], [label("next_action"), scalar(review.payload.next_action)]]));
        lastReview = review;
      } else row.append(el("p", "muted small-note", t("awaitingReview")));
      lastAttempt = attempt; box.append(row);
    });
    pending.forEach((request) => box.append(el("p", "muted small-note", `${t("attemptLabel")} · ${formatDateTime(request.created_at)} · ${t("awaitingImport")}`)));
    const key = `career-copilot-draft-${session.id}`, area = formInput("textarea", {rows: "5", maxlength: "12000", "aria-label": t("answerField"), placeholder: t("answerField")});
    try { area.value = localStorage.getItem(key) || ""; } catch (_) { /* Storage is optional. */ }
    area.addEventListener("input", () => { try { localStorage.setItem(key, area.value); } catch (_) { /* Storage is optional. */ } });
    const form = el("div", "practice-form"), bar = el("div", "inline-form");
    const send = (extra) => { if (!area.value.trim()) { showNotice(t("answerRequired")); area.focus(); return null; } const body = {type: "practice_answer", payload: {session_id: session.id, answer: area.value.trim(), ...extra}}; try { localStorage.removeItem(key); } catch (_) { /* Storage is optional. */ } return body; };
    if (!lastAttempt) bar.append(requestButton(t("submitAnswer"), "primary-button", () => send({})));
    else { bar.append(requestButton(t("retryAnswer"), "primary-button", () => send({previous_attempt_id: lastAttempt.id}))); if (lastReview?.payload.follow_up) bar.append(requestButton(t("followUpAnswer"), "quiet-button", () => send({follow_up_to: lastAttempt.id}))); }
    form.append(area, bar, el("p", "muted small-note", t("draftSaved")));
    box.append(form);
    return box;
  }
  function newPracticeForm(context) {
    const details = el("details", "form-details"), form = el("div", "form-grid"), question = formInput("text", {maxlength: "1000"}), tests = formInput("text", {maxlength: "500"});
    const type = formSelect(["behavioral", "leadership", "product_case", "system_design", "self_presentation", "coding"].map((value) => [value, t(`qtype_${value}`)]), "behavioral"), provenance = formSelect([["generated", t("provenance_generated")], ["published", t("provenance_published")]], "generated");
    form.append(formField(t("questionField"), question, true), formField(t("testsField"), tests, true), formField(t("typeField"), type), formField(t("provenanceField"), provenance));
    details.append(el("summary", "", t("newPractice")), form, requestButton(t("createSession"), "primary-button", () => { if (!question.value.trim() || !tests.value.trim()) { showNotice(t("questionRequired")); return null; } return {type: "prep_create", payload: {...context, question: question.value.trim(), tests: tests.value.trim(), type: type.value, provenance: provenance.value}}; }));
    return details;
  }

  // Sources: collection runs, adding vacancies, search campaigns and the request queue.
  function collectionView() {
    const section = el("section", "view-section"), actions = el("div", "inline-form");
    section.append(el("h2", "view-title", t("collectTitle")), el("p", "muted", t("collectDesc")));
    actions.append(requestButton(t("runCollection"), "primary-button", () => ({type: "task", payload: {task_type: "collect", related: {}}}), t("collectQueued")));
    section.append(actions);
    if (!canRequest()) section.append(el("p", "muted small-note", t("requestsUnavailable")));
    section.append(lastRunPanel(), addVacancyForm());
    return section;
  }
  function lastRunPanel() {
    const box = el("div", "run-summary"), runs = (state.data?.collection_runs || []).slice().sort((a, b) => scalar(b.payload.started_at).localeCompare(scalar(a.payload.started_at)));
    box.append(el("h3", "", t("lastRun")));
    if (!runs.length) { box.append(el("p", "muted", t("noRuns"))); return box; }
    const run = runs[0].payload, list = (key) => Array.isArray(run[key]) ? run[key] : [];
    box.append(factList([[t("runTime"), formatDateTime(run.finished_at || run.started_at)], [t("runNew"), String(list("new").length)], [t("runChanged"), String(list("changed").length)], [t("runUnchanged"), String(run.unchanged ?? 0)], [t("runDuplicates"), String(list("possible_duplicates").length)], [t("runErrors"), String(list("errors").length)]]));
    const refs = el("div", "stacked-refs");
    list("new").forEach((id) => { const vacancy = byId(id, "vacancies"); if (vacancy) refs.append(vacancyReference(vacancy, {compact: true})); });
    list("changed").forEach((item) => { const vacancy = byId(item.id, "vacancies"); if (!vacancy) return; const row = el("div", "related-row"); row.append(vacancyReference(vacancy, {compact: true}), el("span", "muted", `${t("changedFields")}: ${(item.fields || []).map(label).join(", ")}`)); refs.append(row); });
    list("possible_duplicates").forEach((item) => { const a = byId(item.vacancy_id, "vacancies"), b = byId(item.other_id, "vacancies"); if (!a || !b) return; const row = el("div", "related-row"); row.append(vacancyReference(a, {compact: true}), el("span", "muted", t("duplicateOf")), vacancyReference(b, {compact: true})); refs.append(row); });
    list("errors").forEach((item) => { const row = el("div", "related-row"); row.append(badge(item.status), el("span", "", [item.source_id, item.http_status ? `HTTP ${item.http_status}` : "", item.reason || "", `${t("lastSuccess")}: ${item.last_success ? formatDateTime(item.last_success) : t("never")}`].filter(Boolean).join(" · "))); refs.append(row); });
    if (refs.childElementCount) box.append(refs);
    return box;
  }
  function addVacancyForm() {
    const details = el("details", "form-details"), form = el("div", "form-grid");
    const url = formInput("url", {maxlength: "2000", placeholder: "https://"}), text = formInput("textarea", {rows: "6", maxlength: "100000"});
    const title = formInput("text", {maxlength: "200"}), company = formInput("text", {maxlength: "200"}), location = formInput("text", {maxlength: "200"});
    const market = formSelect([["", t("anyOption")], ["ru", translated("ru")], ["intl", translated("intl")]], ""), track = formSelect([["", t("anyOption")], ...TRACK_OPTIONS.map((value) => [value, translated(value)])], "");
    form.append(formField(t("vacancyLink"), url, true), formField(t("vacancyText"), text, true), formField(t("vacancyTitleField"), title), formField(t("companyField"), company), formField(t("locationField"), location), formField(t("marketLabel"), market), formField(t("trackField"), track));
    const submit = requestButton(t("addVacancySubmit"), "primary-button", () => {
      const link = url.value.trim(), body = text.value.trim();
      if (Boolean(link) === Boolean(body)) { showNotice(t("linkOrText")); (link ? text : url).focus(); return null; }
      return {type: "vacancy_add", payload: {url: link || null, text: body || null, title: title.value.trim() || null, company_name: company.value.trim() || null, location: location.value.trim() || null, market: market.value || null, track: track.value || null}};
    });
    details.append(el("summary", "", t("addVacancy")), form, submit);
    return details;
  }
  function campaignsView() {
    const section = el("section", "view-section"), list = state.data?.campaigns || [];
    section.append(el("h2", "view-title", t("campaignsTitle")), el("p", "muted", t("campaignsDesc")));
    if (state.data?.campaigns_error) section.append(el("p", "detail-warning", `${t("campaignsInvalid")}: ${state.data.campaigns_error}`));
    if (list.length) { const grid = el("div", "records-grid"); list.forEach((campaign) => grid.append(campaignCard(campaign))); section.append(grid); }
    else section.append(el("p", "muted", t("noCampaigns")));
    section.append(campaignEditor(null));
    return section;
  }
  function campaignCard(campaign) {
    const card = el("article", "record-card"), top = el("div", "card-top"), meta = el("div", "card-meta");
    const fits = primaryRecords("vacancies").filter((record) => (record.display?.campaigns || []).some((match) => match.campaign_id === campaign.id && match.status === "match")).length;
    top.append(el("strong", "record-title", campaign.name)); meta.append(badge(campaign.market), badge(campaign.track)); if (!campaign.active) meta.append(badge("disabled"));
    const salary = campaign.salary && typeof campaign.salary.min === "number" ? `${t("fromWord")} ${money(campaign.salary.min, campaign.salary.currency)} · ${t(`period_${campaign.salary.period}`)} · ${t(`tax_${campaign.salary.gross_net || "unknown"}`)}` : "";
    card.append(top, meta, factList([[t("criterion_role_titles"), campaign.role_titles.join(", ")], [t("criterion_levels"), campaign.levels.join(", ")], [t("criterion_work_countries"), campaign.work_countries.join(", ")], [t("criterion_work_modes"), campaign.work_modes.map(translated).join(", ")], [t("criterion_employment"), campaign.employment.map(translated).join(", ")], [t("criterion_languages"), campaign.languages.map(languageName).join(", ")], [t("criterion_salary"), salary], [t("criterion_exclusions"), campaign.exclusions.join(", ")], [t("matchedVacancies"), String(fits)]]), campaignEditor(campaign));
    return card;
  }
  function campaignEditor(campaign) {
    const c = campaign || {}, details = el("details", "form-details"), form = el("div", "form-grid");
    const name = formInput("text", {maxlength: "120", value: c.name || ""}), market = formSelect([["any", translated("any")], ["ru", translated("ru")], ["intl", translated("intl")]], c.market || "any"), track = trackSelect(c.track);
    const roles = formInput("text", {value: (c.role_titles || []).join(", ")}), levels = formInput("text", {value: (c.levels || []).join(", ")}), countries = formInput("text", {value: (c.work_countries || []).join(", ")}), languages = formInput("text", {value: (c.languages || []).join(", ")}), exclusions = formInput("text", {value: (c.exclusions || []).join(", ")});
    const checks = (values, selected) => { const box = el("div", "check-row"), inputs = values.map((value) => { const wrap = el("label", "check"), input = formInput("checkbox"); input.value = value; input.checked = (selected || []).includes(value); wrap.append(input, el("span", "", translated(value))); box.append(wrap); return input; }); return {box, values: () => inputs.filter((input) => input.checked).map((input) => input.value)}; };
    const modes = checks(["remote", "hybrid", "office"], c.work_modes), employment = checks(["full_time", "part_time", "contract", "internship", "temporary"], c.employment);
    const salary = c.salary || {}, minimum = formInput("number", {min: "0", step: "1000", value: typeof salary.min === "number" ? String(salary.min) : ""}), currency = formInput("text", {maxlength: "3", value: salary.currency || ""});
    const period = formSelect([["month", t("period_month")], ["year", t("period_year")], ["hour", t("period_hour")]], salary.period || "month"), tax = formSelect([["unknown", t("tax_unknown")], ["gross", t("tax_gross")], ["net", t("tax_net")]], salary.gross_net || "unknown");
    const active = formInput("checkbox"); active.checked = c.active !== false;
    form.append(formField(t("campaignName"), name), formField(t("marketLabel"), market), formField(t("trackField"), track), formField(t("roleTitles"), roles, true), formField(t("levelsField"), levels), formField(t("countriesField"), countries), formField(t("formatLabel"), modes.box), formField(t("employmentLabel"), employment.box), formField(t("languagesField"), languages), formField(t("salaryMin"), minimum), formField(t("currencyField"), currency), formField(t("periodField"), period), formField(t("taxField"), tax), formField(t("exclusionsField"), exclusions, true), formField(t("activeField"), active));
    const submit = requestButton(t("saveCampaign"), "primary-button", () => {
      if (!name.value.trim()) { showNotice(t("campaignNameRequired")); name.focus(); return null; }
      const amount = minimum.value === "" ? null : Number(minimum.value);
      return {type: "campaign_upsert", payload: {expected_version: campaign ? campaign.version : null, campaign: {id: campaign ? campaign.id : undefined, name: name.value.trim(), market: market.value, track: track.value, role_titles: commaList(roles.value), levels: commaList(levels.value), work_countries: commaList(countries.value), work_modes: modes.values(), employment: employment.values(), languages: commaList(languages.value), exclusions: commaList(exclusions.value), salary: amount === null ? null : {min: amount, currency: currency.value.trim().toUpperCase(), period: period.value, gross_net: tax.value}, active: active.checked}}};
    });
    details.append(el("summary", "", campaign ? t("editCampaign") : t("newCampaign")), form, submit);
    return details;
  }
  function workView() {
    const section = el("section", "view-section"), requests = workRecords("inbox_requests").map((item) => item.payload).sort((a, b) => scalar(b.applied_at || b.created_at).localeCompare(scalar(a.applied_at || a.created_at)));
    const tasks = workRecords("tasks").map((item) => item.payload).sort((a, b) => scalar(b.updated_at).localeCompare(scalar(a.updated_at)));
    section.append(el("h2", "view-title", t("workTitle")), el("p", "muted", t("workDesc")));
    section.append(workList({pending: state.data?.pending_requests || [], requests: requests.filter((request) => request.status !== "queued_for_agent"), tasks}, 40) || el("p", "muted", t("noWork")));
    return section;
  }

  // ---------------------------------------------------------------------------
  // In-browser reader for Markdown and text files (download stays available).
  // ---------------------------------------------------------------------------
  const SECTION_WORDS = "Чем предстоит заниматься|Что предстоит делать|Что нужно делать|Обязанности|Задачи|Требования|Мы ожидаем|Что мы ожидаем|Наши пожелания к соискателю|Будет плюсом|Мы предлагаем|Что мы предлагаем|Условия|О компании|О команде|Наша миссия|Responsibilities|What you(?:'|’)ll do|Minimum qualifications|Preferred qualifications|Basic qualifications|Qualifications|Requirements|About the job|About the role|About us|What we offer|Benefits";
  // Case-sensitive on purpose: "Условия работы:" starts a section, "условия" inside a sentence does not.
  const SECTION_ALTERNATIVES = SECTION_WORDS.split("|").flatMap((word) => [word, word.toUpperCase()]).join("|");
  const SECTION_START = new RegExp(`\\s(?=(?:${SECTION_ALTERNATIVES})(?:\\s*:|\\s+[A-ZА-ЯЁ]))`, "gu");
  const SECTION_HEAD = new RegExp(`^(${SECTION_WORDS})\\s*:?\\s*`, "iu");
  function documentBody(path, text) {
    if (!/\.txt$/i.test(path)) return renderMarkdown(text);
    const root = el("div", "markdown posting-text"), lines = String(text).replace(/\r\n/g, "\n").split("\n"), meta = [];
    let start = 0;
    for (let index = 0; index < Math.min(lines.length, 15); index++) {
      const match = lines[index].trim().match(/^(Title|Company|Location|URL|Source|Salary|Posted|Date):\s*(.*)$/i);
      if (match) { const value = match[2].trim().replace(/[ ,]+$/, ""); if (value && !/^(title|company)$/i.test(match[1])) meta.push([match[1].toLowerCase(), value]); start = index + 1; }
      else if (lines[index].trim()) break;
    }
    if (meta.length) root.append(factList(meta.map(([key, value]) => [key === "location" ? t("city") : key === "url" ? t("openPosting") : key === "salary" ? label("salary") : label(key), /^https?:/i.test(value) ? externalLink(value, value.replace(/^https?:\/\/(www\.)?/, "")) || value : value])));
    lines.slice(start).join("\n").replace(SECTION_START, "\n\n").split(/\n{2,}/).map((part) => part.trim()).filter(Boolean).forEach((part) => {
      const head = part.match(SECTION_HEAD); let body = part;
      if (head) { root.append(el("h4", "", head[1])); body = part.slice(head[0].length); }
      // Long single-line postings read better as short paragraphs of a few sentences.
      const sentences = body.split(/(?<=[.!?;])\s+(?=[A-ZА-ЯЁ«"(])/u);
      for (let index = 0; index < sentences.length; index += 3) { const chunk = sentences.slice(index, index + 3).join(" ").trim(); if (chunk) root.append(el("p", "", chunk)); }
    });
    return root;
  }
  // Scroll to the exact row/paragraph naming this vacancy in a shared research file, else to its section.
  function highlightHeading(container, heading, record) {
    const needles = record ? [...String(record.id).matchAll(/\d{4,}/g)].map((match) => match[0]).concat(recordTitle(record).slice(0, 40)) : [];
    const exact = needles.length ? [...container.querySelectorAll("tr,li,p")].find((node) => needles.some((needle) => needle && node.textContent.includes(needle))) : null;
    const target = exact || (heading ? [...container.querySelectorAll("h3,h4,h5,h6")].find((node) => node.textContent.trim().includes(heading.slice(0, 40))) : null);
    if (target) { target.classList.add("is-highlighted"); requestAnimationFrame(() => target.scrollIntoView({block: "start"})); }
  }
  async function openDocument(path, {heading, title, record} = {}) {
    const dialog = $("document-dialog"), name = path.split("/").pop();
    $("document-kind").textContent = name; $("document-download").href = "/api/artifacts/" + path.split("/").map(encodeURIComponent).join("/");
    const header = el("h2", "detail-heading", title || name); header.id = "document-title";
    $("document-content").replaceChildren(header, el("p", "muted", t("planLoading")));
    if (!dialog.open) dialog.showModal(); dialog.scrollTop = 0;
    try { const text = await artifactText(path); const body = documentBody(path, text); $("document-content").replaceChildren(header, body); highlightHeading(body, heading, record); }
    catch (_) { $("document-content").replaceChildren(header, el("p", "detail-warning", t("planUnavailable"))); }
  }
  function relation(value, key) {
    const preferred = {company_id: "companies", vacancy_id: "vacancies", vacancy_ids: "vacancies", related_vacancy_ids: "vacancies", package_id: "packages", activity_id: "activities", parent_activity_id: "activities", event_id: "events", assessment_id: "assessments", plan_id: "interview_plans"}[key];
    if (preferred) return byId(value, preferred) || null;
    return ["entity_ids", "records"].includes(key) ? byId(value) || null : null;
  }
  function renderValue(value, key = "", depth = 0) {
    if (value === null || value === undefined || value === "") return el("span", "muted", t("unknown"));
    if (typeof value === "boolean") return el("span", "", t(value ? "yes" : "no"));
    if (typeof value === "string") { const related = relation(value, key); if (related) return recordReference(related); const file = artifactLink(value); if (file) return file; const link = externalLink(value); if (link) return link; return el("span", "field-string", translated(value)); }
    if (typeof value === "number") return el("span", "", value.toLocaleString(state.lang));
    if (Array.isArray(value)) { if (!value.length) return el("span", "muted", t("empty")); const list = el("ol", "value-list"); value.forEach((item) => { const li = el("li"); li.append(renderValue(item, key, depth + 1)); list.append(li); }); return list; }
    const list = el("dl", "field-list"); Object.entries(value).forEach(([field, item]) => { const row = el("div", "field-row"), dd = el("dd"); dd.append(renderValue(item, field, depth + 1)); row.append(el("dt", "", label(field)), dd); list.append(row); }); return list;
  }
  async function openRecord(record, tab) {
    if (tab) state.detailTab = tab; else if (!state.opened || state.opened.id !== record.id || state.opened.kind !== record.kind) state.detailTab = state.opened ? "vacancy" : state.detailTab;
    state.opened = record; const token = ++state.detailToken; renderDetail(record, "detailLoading"); if (!$("record-dialog").open) $("record-dialog").showModal(); $("record-dialog").scrollTop = 0; syncHash();
    try { const response = await fetch(`/api/records/${encodeURIComponent(record.kind)}/${encodeURIComponent(record.id)}`, {cache: "no-store", credentials: "same-origin"}); if (!response.ok) throw new Error("record unavailable"); const exact = await response.json(); if (token !== state.detailToken) return; const full = normalize(exact.record || exact, state.section); full.display ||= record.display; state.opened = full; renderDetail(full); }
    catch (_) { if (token === state.detailToken) renderDetail(record, record.missing ? "recordMissing" : "detailError"); }
  }
  function renderDetail(record, notice) {
    if (record.kind === "vacancies") { renderVacancyDetail(record, notice); return; }
    const p = record.payload; $("detail-kind").textContent = label(record.kind);
    const fragment = document.createDocumentFragment(), title = el("h2", "detail-heading", recordTitle(record)); title.id = "detail-title"; fragment.append(title, el("div", "detail-id", record.id));
    const meta = el("div", "card-meta"); if (status(record) !== "unknown" || record.kind === "vacancies") meta.append(badge(status(record))); tracks(record).forEach((track) => meta.append(badge(track))); fragment.append(meta);
    if (notice) { const message = el("p", notice === "detailLoading" ? "muted" : "detail-warning", t(notice)); if (notice === "detailLoading") message.setAttribute("role", "status"); fragment.append(message); }
    if (["companies", "vacancies"].includes(record.kind)) { const geo = el("div", "detail-geography"); geo.append(geographyBlock(record)); const raw = geography(record).raw; if (raw) { const rawText = el("div", "location-line"); rawText.textContent = `${t("originalLocation")}: ${raw}`; geo.append(rawText); } fragment.append(geo); }
    if (record.kind === "vacancies" && !record.missing) fragment.append(availabilityPanel(record));
    const links = [...linksFrom(p.urls || p.url || p.profile_sources || p.source_url || [])]; if (links.length) { const group = el("div", "detail-links"); links.forEach((url, index) => group.append(externalLink(url, record.kind === "vacancies" && index === 0 ? `${t("openPosting")} ↗` : `${t("source")} ${index + 1} ↗`))); fragment.append(group); }
    const groups = {recordFields: {}, evidenceFields: {}, versionFields: {}, sourceFields: {}};
    Object.entries(p).forEach(([key, value]) => { if (key === "id") return; const group = /^(versions|files|artifacts|reviews|current_version|review_status|application_status)$/.test(key) ? "versionFields" : /(requirement|evidence|assessment|gate|decision|seniority|gap)/.test(key) ? "evidenceFields" : /(source|url|snapshot|dossier|provenance)/.test(key) ? "sourceFields" : "recordFields"; groups[group][key] = value; });
    Object.entries(groups).forEach(([name, fields]) => { if (!Object.keys(fields).length) return; const section = el("section", "detail-section"); section.append(el("h3", "", t(name)), renderValue(fields)); fragment.append(section); });
    const mentions = (candidate) => { const c = candidate.payload; return (Array.isArray(c.entity_ids) && c.entity_ids.includes(record.id)) || (Array.isArray(c.vacancy_ids) && c.vacancy_ids.includes(record.id)) || (Array.isArray(c.gaps) && c.gaps.some((gap) => Array.isArray(gap.vacancy_ids) && gap.vacancy_ids.includes(record.id))); };
    const related = allRecords().filter((candidate) => candidate !== record && !(candidate.id === record.id && candidate.kind === record.kind) && ((record.kind === "companies" && candidate.payload.company_id === record.id) || (record.kind === "vacancies" && candidate.payload.vacancy_id === record.id) || (record.kind === "packages" && candidate.payload.package_id === record.id) || (record.kind === "activities" && (candidate.payload.activity_id === record.id || candidate.payload.parent_activity_id === record.id)) || (!["activity_events", "legacy_files"].includes(candidate.kind) && mentions(candidate)))).sort((a, b) => (a.display?.current === false) - (b.display?.current === false) || dateValue(b).localeCompare(dateValue(a)));
    if (related.length) { const section = el("section", "detail-section"), items = el("div", "related-records"); related.slice(0, 40).forEach((candidate) => { const row = el("div", "related-row"); row.append(recordReference(candidate)); if (candidate.kind !== "vacancies" && formatDate(dateValue(candidate))) row.append(el("span", "muted related-date", formatDate(dateValue(candidate)))); if (candidate.display?.current === false) row.append(badge("superseded")); items.append(row); }); section.append(el("h3", "", t("related")), items); fragment.append(section); }
    const raw = el("details", "raw-details"); raw.append(el("summary", "", t("technical")), el("pre", "", JSON.stringify(p, null, 2))); fragment.append(raw); $("detail-content").replaceChildren(fragment);
  }
  function openLinkedRecord(reference) {
    if (!reference || !state.data) return; const split = reference.indexOf("/"); if (split < 1) return;
    const kind = reference.slice(0, split), id = reference.slice(split + 1), found = allRecords().find((record) => record.kind === kind && record.id === id);
    if (state.opened && state.opened.kind === kind && state.opened.id === id && $("record-dialog").open) return;
    openRecord(found || {kind, id, payload: {}, missing: true});
  }
  async function load() {
    const firstLoad = !state.data; $("refresh").disabled = true; $("refresh").textContent = t("refreshing"); $("main").setAttribute("aria-busy", "true");
    try { const response = await fetch("/api/workspace", {cache: "no-store", credentials: "same-origin"}); if (!response.ok) throw new Error("workspace unavailable"); const data = await response.json(); const normalized = {...data}; sections.filter((section) => !["overview", "pipeline"].includes(section)).forEach((section) => { const values = data[section] || data.entities?.[section] || data[kinds[section]] || []; normalized[section] = Array.isArray(values) ? values.map((record) => normalize(record, section)) : []; }); normalized.collection_runs = (normalized.sources || []).filter((record) => record.kind === "collection_runs"); normalized.sources = (normalized.sources || []).filter((record) => record.kind !== "collection_runs"); state.data = normalized; state.all = sections.filter((section) => section !== "pipeline").flatMap((section) => normalized[section] || []); state.index = new Map(); state.all.forEach((record) => { state.index.set(`${record.kind}/${record.id}`, record); if (!["activity_events", "legacy_files"].includes(record.kind) && !state.index.has(`*/${record.id}`)) state.index.set(`*/${record.id}`, record); }); state.loadedAt = new Date().toISOString(); state.artifacts = new Set((data.artifacts || []).map((artifact) => typeof artifact === "string" ? artifact : artifact.path)); state.artifactAliases = new Map(); [...(data.legacy_files || []), ...allRecords().filter((record) => record.kind === "legacy_files")].forEach((record) => { const p = unwrap(record); if (typeof p.path === "string") state.artifactAliases.set(String(p.id || record.id), p.path); }); $("refresh").disabled = false; render(); if (firstLoad) openLinkedRecord(pendingRecord); }
    catch (_) {
      if (state.data) { $("connection").textContent = ""; showNotice(t("refreshFailed")); }
      else { $("connection").textContent = ""; $("overview").hidden = true; $("collection").hidden = true; const error = emptyState("error", "errorDesc"); error.append(button(t("retry"), "primary-button", load)); $("load-state").replaceChildren(error); $("load-state").className = ""; $("load-state").hidden = false; }
    }
    finally { $("refresh").disabled = false; $("refresh").textContent = t("refresh"); $("main").removeAttribute("aria-busy"); }
  }
  let noticeTimer = 0;
  function showNotice(message, duration = 5000) { const notice = $("notice"); notice.textContent = message; notice.hidden = false; clearTimeout(noticeTimer); noticeTimer = setTimeout(() => { notice.hidden = true; }, duration); }
  async function copyLink() { const url = location.href; try { await navigator.clipboard.writeText(url); showNotice(t("linkCopied")); } catch (_) { window.prompt(t("copyLink"), url); } }
  $("refresh").addEventListener("click", load);
  $("copy-link").addEventListener("click", copyLink);
  $("content-language").addEventListener("click", () => { state.contentMode = state.contentMode === "original" ? "translated" : "original"; try { localStorage.setItem("career-copilot-content", state.contentMode); } catch (_) { /* Storage is optional. */ } render(); if ($("record-dialog").open && state.opened) renderDetail(state.opened); });
  $("language").addEventListener("click", () => { state.lang = state.lang === "ru" ? "en" : "ru"; try { localStorage.setItem("career-copilot-language", state.lang); } catch (_) { /* Storage is optional. */ } render(); if ($("record-dialog").open && state.opened) renderDetail(state.opened); });
  $("close-detail").addEventListener("click", () => $("record-dialog").close());
  $("close-document").addEventListener("click", () => $("document-dialog").close());
  $("document-dialog").addEventListener("click", (event) => { if (event.target === $("document-dialog")) { const rect = event.target.getBoundingClientRect(); if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) event.target.close(); } });
  $("record-dialog").addEventListener("close", () => { state.detailToken++; state.opened = null; state.detailTab = "vacancy"; syncHash(); });
  $("record-dialog").addEventListener("click", (event) => { if (event.target === $("record-dialog")) { const rect = event.target.getBoundingClientRect(); if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) event.target.close(); } });
  function onLocationChange() { if (location.hash === hashFor(state.section)) return; const reference = applyHash(); render(); if (reference) openLinkedRecord(reference); else if ($("record-dialog").open) $("record-dialog").close(); }
  window.addEventListener("hashchange", onLocationChange);
  window.addEventListener("popstate", onLocationChange);
  document.addEventListener("keydown", (event) => { if (event.key !== "/" || event.metaKey || event.ctrlKey || event.altKey || $("record-dialog").open) return; const target = event.target; if (target instanceof HTMLElement && (target.isContentEditable || ["INPUT", "SELECT", "TEXTAREA"].includes(target.tagName))) return; const search = $("record-search"); if (search && !$("collection").hidden) { event.preventDefault(); search.focus(); search.select(); } });
  const pendingRecord = applyHash();
  renderChrome(); load();
})();
