"use strict";

// All journal values enter the document as text. No source HTML is executed.
(() => {
  const sections = ["overview", "pipeline", "vacancies", "companies", "documents", "activities", "preparations", "sources", "history"];
  const kinds = {documents: "packages", preparations: "learning", sources: "source_health", history: "events"};
  const icons = ["◫", "⇉", "↗", "▦", "▤", "◷", "◎", "⊞", "≡"];
  const copy = {
    ru: {
      overview: "Обзор", vacancies: "Вакансии", companies: "Компании", documents: "Документы", activities: "Активности", preparations: "Подготовка", sources: "Источники", history: "История",
      workspace: "РАБОЧЕЕ ПРОСТРАНСТВО", privateJournal: "Личный журнал", sidebarNote: "Факты, решения и следующий шаг — в одном месте.", skip: "К содержимому", refresh: "Обновить", footer: "Основано на вашем журнале. Неизвестное остаётся неизвестным.", loading: "Открываем рабочее пространство…", connected: "ЖУРНАЛ ПОДКЛЮЧЁН", updated: "Обновлено", overviewTitle: "Ваша следующая глава.", overviewDesc: "Поиск работы как последовательная работа: от первого источника до следующего разговора.", vacanciesDesc: "Роли, требования и решения. Откройте вакансию, чтобы увидеть детали и основания оценки.", companiesDesc: "Бизнес, продукты, масштаб и найм — с сохранёнными источниками.", documentsDesc: "Пакеты, версии и проверки. Готовность документа и отправка учитываются отдельно.", activitiesDesc: "Выполненная работа, фактические участники и следующие действия.", preparationsDesc: "Планы, практика и подтверждённый прогресс подготовки к интервью.", sourcesDesc: "Состояние источников, успешные проверки и ограничения доступа.", historyDesc: "Сохранённая история решений и действий в вашем журнале.", search: "Поиск по названию, компании и содержимому…", newest: "Сначала новые", alphabetical: "По алфавиту", country: "Страна", city: "Город", remote: "Формат", status: "Статус", track: "Направление", all: "Все", unknown: "Не указано", unknownStatus: "Неизвестно", reset: "Сбросить фильтры", found: "Найдено", records: "записей", open: "Подробнее", original: "Источник ↗", originalLocation: "Локация в источнике", latestVacancies: "Последние вакансии", viewAll: "Все записи ↗", nextSteps: "Следующие действия", focus: "В ФОКУСЕ", focusTitle: "Ясность перед следующим шагом.", focusDesc: "Вакансии с неизвестной доступностью требуют проверки источника. Оценка соответствия и актуальность найма — отдельные решения.", unknownAvailability: "вакансий требуют проверки доступности", companyNote: "сохранённые профили", vacancyNote: "сохранённые роли", documentNote: "пакеты и отдельные тексты", activityNote: "записи работы", noRecords: "Здесь пока нет записей", noRecordsDesc: "Раздел заполнится, когда соответствующие записи появятся в журнале.", noResults: "Ничего не найдено", noResultsDesc: "Попробуйте другой запрос или сбросьте фильтры.", noActions: "Следующие действия не записаны", noActionsDesc: "Зафиксированные следующие шаги появятся здесь.", error: "Не удалось открыть журнал", errorDesc: "Проверьте доступность сервера и повторите загрузку.", retry: "Повторить", previous: "← Назад", next: "Далее →", page: "Страница", of: "из", detailError: "Не удалось получить свежую запись. Показана версия из загруженного обзора.", detailLoading: "Загружаем полную запись…", recordFields: "Сведения", sourceFields: "Источники и материалы", evidenceFields: "Оценка и доказательства", versionFields: "Версии и файлы", related: "Связанные записи", technical: "Исходная запись JSON", yes: "Да", no: "Нет", empty: "Нет данных", remoteLabel: "Удалённо", hybrid: "Гибрид", onsite: "Офис", close: "Закрыть", relatedCompany: "Компания", relatedVacancies: "Вакансии компании", about: "О компании", size: "Масштаб", versions: "Версии", assessed: "Оценка", availability: "Доступность", registeredFile: "Открыть файл ↗", source: "Источник", activeFilters: "с учётом фильтров", current: "Текущая", showMore: "Показать ещё", unknownRecord: "Запись", privacy: "ЛИЧНОЕ ПРОСТРАНСТВО", countriesNote: "География указана по сохранённым данным.", readyNote: "Проверки и отправки — в карточках документов.", noDate: "Дата не указана"
    },
    en: {
      overview: "Overview", vacancies: "Vacancies", companies: "Companies", documents: "Documents", activities: "Activities", preparations: "Preparation", sources: "Sources", history: "History", workspace: "WORKSPACE", privateJournal: "Private journal", sidebarNote: "Facts, decisions and the next step, together.", skip: "Skip to content", refresh: "Refresh", footer: "Based on your journal. Unknowns stay unknown.", loading: "Opening your workspace…", connected: "JOURNAL CONNECTED", updated: "Updated", overviewTitle: "Your next chapter.", overviewDesc: "A deliberate job search: from the first source to your next conversation.", vacanciesDesc: "Roles, requirements and decisions. Open a vacancy to inspect its details and assessment evidence.", companiesDesc: "Business, products, scale and hiring, with retained sources.", documentsDesc: "Packages, versions and reviews. Document readiness and submission are separate.", activitiesDesc: "Recorded work, actual contributors and next actions.", preparationsDesc: "Plans, practice and demonstrated interview preparation progress.", sourcesDesc: "Source health, successful checks and access limitations.", historyDesc: "The retained history of decisions and actions in your journal.", search: "Search titles, companies and record contents…", newest: "Newest first", alphabetical: "Alphabetically", country: "Country", city: "City", remote: "Work mode", status: "Status", track: "Track", all: "All", unknown: "Not specified", unknownStatus: "Unknown", reset: "Reset filters", found: "Found", records: "records", open: "Details", original: "Source ↗", originalLocation: "Original location", latestVacancies: "Latest vacancies", viewAll: "View all ↗", nextSteps: "Next actions", focus: "IN FOCUS", focusTitle: "Clarity before the next step.", focusDesc: "Vacancies with unknown availability need a source check. Role fit and current hiring are separate decisions.", unknownAvailability: "vacancies need an availability check", companyNote: "retained profiles", vacancyNote: "retained roles", documentNote: "packages and standalone texts", activityNote: "work records", noRecords: "No records yet", noRecordsDesc: "This section will populate when records are added to the journal.", noResults: "No matching records", noResultsDesc: "Try another search or reset the filters.", noActions: "No next actions recorded", noActionsDesc: "Recorded next steps will appear here.", error: "Could not open the journal", errorDesc: "Check the server connection and try again.", retry: "Retry", previous: "← Previous", next: "Next →", page: "Page", of: "of", detailError: "Could not fetch the latest record. Showing the version from the loaded overview.", detailLoading: "Loading the full record…", recordFields: "Details", sourceFields: "Sources and materials", evidenceFields: "Assessment and evidence", versionFields: "Versions and files", related: "Related records", technical: "Original JSON record", yes: "Yes", no: "No", empty: "No data", remoteLabel: "Remote", hybrid: "Hybrid", onsite: "On-site", close: "Close", relatedCompany: "Company", relatedVacancies: "Company vacancies", about: "About", size: "Scale", versions: "Versions", assessed: "Assessment", availability: "Availability", registeredFile: "Open file ↗", source: "Source", activeFilters: "filtered", current: "Current", showMore: "Show more", unknownRecord: "Record", privacy: "PRIVATE WORKSPACE", countriesNote: "Geography follows the retained evidence.", readyNote: "Review and submission details are in document records.", noDate: "No date recorded"
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
  const state = {lang: "ru", section: "overview", data: null, query: "", filters: {}, sort: "newest", page: 1, pageSize: 24, detailToken: 0, opened: null, filtersOpen: false, loadedAt: null, showSuperseded: false, contentMode: "translated"};
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
  const records = (section) => section === "pipeline" ? (state.data?.vacancies || []).filter((record) => record.kind === "vacancies") : state.data?.[section] || [];
  const primaryRecords = (section) => ["companies", "vacancies", "activities"].includes(section) ? records(section).filter((record) => record.kind === section) : section === "documents" ? records(section).filter((record) => record.kind !== "legacy_files") : records(section);
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
  const badge = (value) => { const tone = /^(active|open|completed|healthy|ok|approved|ready|verified|success|pass|passed|enabled|current)$/.test(value) ? "good" : /^(blocked|failed|needs_clarification|pending_review|partial|cooldown|fail|rejected|timeout|needs_check|never_checked|conflicting|expired_copy|unverified)$/.test(value) ? "attention" : /^(priority|running|in_progress|product|technical-leadership|follow_up|todo)$/.test(value) ? "blue" : ""; return el("span", `badge ${tone}`, translated(value)); };
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
    if (withRecord && state.opened) params.set("record", `${state.opened.kind}/${state.opened.id}`);
    const query = params.toString(); return `#${section}${query ? `?${query}` : ""}`;
  }
  function syncHash() { const hash = hashFor(state.section); if (location.hash !== hash) history.replaceState(null, "", hash); }
  function applyHash() {
    const raw = location.hash.slice(1), split = raw.indexOf("?"), name = split < 0 ? raw : raw.slice(0, split), params = new URLSearchParams(split < 0 ? "" : raw.slice(split + 1));
    state.section = sections.includes(name) ? name : "overview"; state.query = params.get("q") || ""; state.sort = params.get("sort") === "name" ? "name" : "newest"; state.page = Math.max(1, Number.parseInt(params.get("page") || "1", 10) || 1);
    state.filters = defaultFilters(state.section); ["kind", "country", "city", "remote", "status", "track", "availability", "review", "type", "freshness"].forEach((key) => { if (params.has(key)) state.filters[key] = params.get(key) === "all" ? "" : params.get(key); });
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
    const row = el("div", "filter-row"), filterKeys = state.section === "vacancies" ? ["kind", "availability", "freshness", "review", "track", "country", "city", "remote"] : state.section === "pipeline" ? ["track"] : state.section === "companies" ? ["kind", "country", "city", "status", "track"] : state.section === "history" ? ["type"] : state.section === "sources" ? [] : state.section === "preparations" ? ["kind", "track"] : ["kind", "status", "track"]; row.id = "filter-row";
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
  function filterValues(record, key) { if (key === "kind") return [record.kind]; if (["country", "city", "remote"].includes(key)) return [geography(record)[key]]; if (key === "track") return tracks(record).length ? tracks(record) : ["unknown"]; if (key === "freshness") return [record.kind === "vacancies" ? freshness(record) : "never"]; if (key === "type") return [record.kind === "events" ? known(record.payload.type) || "unknown" : record.kind]; if (key === "review") return [known(record.payload.review_status) || "unknown"]; if (key === "availability") { const value = known(record.display?.availability || record.payload.availability) || "unknown"; return needsCheck(record) ? [value, "needs_check"] : [value]; } return [status(record)]; }
  function renderResults() {
    const query = state.query.trim().toLocaleLowerCase(state.lang);
    const filtered = records(state.section).filter((record) => (!query || `${recordTitle(record)} ${companyName(record)} ${JSON.stringify(record.payload)}`.toLocaleLowerCase(state.lang).includes(query)) && Object.entries(state.filters).every(([key, value]) => !value || filterValues(record, key).includes(value)));
    filtered.sort(state.sort === "name" ? (a, b) => recordTitle(a).localeCompare(recordTitle(b), state.lang) : (a, b) => dateValue(b).localeCompare(dateValue(a)) || recordTitle(a).localeCompare(recordTitle(b), state.lang));
    const totalPages = Math.max(1, Math.ceil(filtered.length / state.pageSize)); state.page = Math.min(state.page, totalPages);
    const active = filtersActive(), reset = document.querySelector(".reset-button"); if (reset) reset.disabled = !active;
    $("results-heading").replaceChildren(el("span", "", `${t("found")}: ${filtered.length.toLocaleString(state.lang)} ${recordsWord(filtered.length)}`), el("span", "", active ? t("activeFilters") : `${String(sections.indexOf(state.section) + 1).padStart(2, "0")} / ${t(state.section)}`));
    if (state.section === "sources" || (filtered.length && ["preparations", "history", "pipeline"].includes(state.section))) {
      $("results").replaceChildren(state.section === "sources" ? renderSources(filtered) : state.section === "history" ? renderHistory(filtered) : state.section === "pipeline" ? renderPipeline(filtered) : renderPreparations(filtered));
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
    const container = el("div", "plans"), plans = list.filter((record) => ["learning", "interview_plans"].includes(record.kind)), others = list.filter((record) => !plans.includes(record));
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
    card.append(factList([[label("market"), p.market ? translated(p.market) : ""], [t("schedule"), p.enabled === false ? translated("disabled") : scheduleText(p.interval_seconds)], [t("lastCheck"), health.last_attempt ? formatDateTime(health.last_attempt) : t("never")], [t("nextCheck"), health.next_attempt && p.enabled !== false ? formatDateTime(health.next_attempt) : ""], [t("foundCount"), health.count ?? ""], [t("titleFilter"), scalar(p.include_title)], [label("error"), scalar(health.error)]]));
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
    container.append(configured, all); return container;
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
  function vacancyActions(record, {details = true, extras = true} = {}) {
    const row = el("div", "vacancy-actions"), link = postingLink(record); if (link) row.append(link);
    if (!extras) return row;
    const doc = record.display?.description; if (doc?.path) row.append(button(t("fullDescription"), "text-button", () => openDocument(doc.path, doc.kind === "research" ? {heading: doc.heading, title: recordTitle(record), record} : {title: recordTitle(record)})));
    learningFor(record).slice(0, 1).forEach((plan) => row.append(button(t("learningPlanLink"), "text-button", () => openPlan(plan))));
    if (details) row.append(button(`${t("open")} →`, "text-button", () => openRecord(record)));
    return row;
  }
  function vacancyCard(record) {
    const card = el("article", "record-card vacancy-card"), top = el("div", "card-top");
    top.append(employerLine(record), badge(status(record))); card.append(top, button(recordTitle(record), "record-title", () => openRecord(record)));
    const text = record.display?.description?.excerpt; card.append(el("p", `record-summary vacancy-description${text ? "" : " muted"}`, text || t("noDescription")));
    const age = el("div", "card-age"); age.append(ageBadge(record)); card.append(age, vacancyActions(record)); return card;
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
  function renderVacancyDetail(record, notice) {
    const fragment = document.createDocumentFragment(); $("detail-kind").textContent = kindName("vacancies");
    const title = el("h2", "detail-heading", recordTitle(record)); title.id = "detail-title";
    const statusRow = el("div", "status-line"); statusRow.append(badge(status(record)), ageBadge(record)); if (canCheck() && !record.missing && !inactiveVacancy(record)) statusRow.append(checkButton([record.id]));
    fragment.append(employerLine(record), title, statusRow);
    if (notice === "detailLoading") { const message = el("p", "muted", t(notice)); message.setAttribute("role", "status"); fragment.append(message); }
    const doc = record.display?.description, about = el("section", "vacancy-about");
    about.append(el("h3", "", t("descriptionTitle")), el("p", "vacancy-description-full", doc?.excerpt || t("noDescription")));
    if (doc?.path) {
      const full = el("details", "full-description"), holder = el("div", "markdown-holder"); full.append(el("summary", "", t("showFullDescription")), holder);
      full.addEventListener("toggle", () => { if (!full.open || holder.dataset.loaded) return; holder.dataset.loaded = "1"; holder.replaceChildren(el("p", "muted", t("planLoading"))); artifactText(doc.path).then((text) => { holder.replaceChildren(documentBody(doc.path, text)); if (doc.kind === "research") highlightHeading(holder, doc.heading, record); }).catch(() => { delete holder.dataset.loaded; holder.replaceChildren(el("p", "detail-warning", t("planUnavailable"))); }); });
      about.append(full);
    }
    fragment.append(about, vacancyActions(record, {details: false, extras: false}));
    const plans = learningFor(record);
    if (plans.length) { const section = el("section", "vacancy-plans"); section.append(el("h3", "", t("preparationTitle"))); plans.forEach((plan) => { const row = el("div", "vacancy-actions"); row.append(button(recordTitle(plan), "record-reference", () => openPlan(plan))); const pdf = el("a", "text-button", t("downloadPdf")); pdf.href = `/api/plans/learning/${encodeURIComponent(plan.id)}.pdf${state.lang === "en" ? "?lang=en" : ""}`; pdf.setAttribute("download", ""); row.append(pdf); section.append(row); }); fragment.append(section); }
    const tech = el("details", "technical-details"); tech.append(el("summary", "", t("technicalDetails")), technicalSections(record, notice)); fragment.append(tech);
    $("detail-content").replaceChildren(fragment);
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
  async function openRecord(record) {
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
    try { const response = await fetch("/api/workspace", {cache: "no-store", credentials: "same-origin"}); if (!response.ok) throw new Error("workspace unavailable"); const data = await response.json(); const normalized = {...data}; sections.filter((section) => !["overview", "pipeline"].includes(section)).forEach((section) => { const values = data[section] || data.entities?.[section] || data[kinds[section]] || []; normalized[section] = Array.isArray(values) ? values.map((record) => normalize(record, section)) : []; }); state.data = normalized; state.all = sections.filter((section) => section !== "pipeline").flatMap((section) => normalized[section] || []); state.index = new Map(); state.all.forEach((record) => { state.index.set(`${record.kind}/${record.id}`, record); if (!["activity_events", "legacy_files"].includes(record.kind) && !state.index.has(`*/${record.id}`)) state.index.set(`*/${record.id}`, record); }); state.loadedAt = new Date().toISOString(); state.artifacts = new Set((data.artifacts || []).map((artifact) => typeof artifact === "string" ? artifact : artifact.path)); state.artifactAliases = new Map(); [...(data.legacy_files || []), ...allRecords().filter((record) => record.kind === "legacy_files")].forEach((record) => { const p = unwrap(record); if (typeof p.path === "string") state.artifactAliases.set(String(p.id || record.id), p.path); }); $("refresh").disabled = false; render(); if (firstLoad) openLinkedRecord(pendingRecord); }
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
  $("record-dialog").addEventListener("close", () => { state.detailToken++; state.opened = null; syncHash(); });
  $("record-dialog").addEventListener("click", (event) => { if (event.target === $("record-dialog")) { const rect = event.target.getBoundingClientRect(); if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) event.target.close(); } });
  function onLocationChange() { if (location.hash === hashFor(state.section)) return; const reference = applyHash(); render(); if (reference) openLinkedRecord(reference); else if ($("record-dialog").open) $("record-dialog").close(); }
  window.addEventListener("hashchange", onLocationChange);
  window.addEventListener("popstate", onLocationChange);
  document.addEventListener("keydown", (event) => { if (event.key !== "/" || event.metaKey || event.ctrlKey || event.altKey || $("record-dialog").open) return; const target = event.target; if (target instanceof HTMLElement && (target.isContentEditable || ["INPUT", "SELECT", "TEXTAREA"].includes(target.tagName))) return; const search = $("record-search"); if (search && !$("collection").hidden) { event.preventDefault(); search.focus(); search.select(); } });
  const pendingRecord = applyHash();
  renderChrome(); load();
})();
