# Как внедрить gstack в разработку taxi-bot

## Что такое gstack

gstack превращает Claude Code из одного универсального ассистента в **команду специалистов**, которых можно вызывать по требованию. Вместо одного "мягкого" режима работы, вы получаете явные когнитивные режимы:

- **Founder mode** (`/plan-ceo-review`) - думает о продукте с точки зрения пользователя
- **Engineering mode** (`/plan-eng-review`) - архитектура, диаграммы, edge cases
- **Paranoid reviewer** (`/review`) - ищет баги, которые пройдут CI но сломаются в продакшене
- **Release engineer** (`/ship`) - автоматизация релиза
- **QA engineer** (`/qa`) - тестирование + исправление багов
- **Browser automation** (`/browse`) - дает агенту "глаза" для тестирования UI

## Установка gstack

### Шаг 1: Установка глобально (для всех проектов)

Скопируйте эту команду в Claude Code:

```
Install gstack: run `git clone https://github.com/garrytan/gstack.git ~/.claude/skills/gstack && cd ~/.claude/skills/gstack && ./setup` then add a "gstack" section to CLAUDE.md that says to use the /browse skill from gstack for all web browsing, never use mcp__claude-in-chrome__* tools, and lists the available skills: /plan-ceo-review, /plan-eng-review, /plan-design-review, /design-consultation, /review, /ship, /browse, /qa, /qa-only, /qa-design-review, /setup-browser-cookies, /retro, /document-release.
```

### Шаг 2: Добавление в taxi-bot проект (опционально)

Если хотите, чтобы команда тоже получила gstack:

```
Add gstack to this project: run `cp -Rf ~/.claude/skills/gstack .claude/skills/gstack && rm -rf .claude/skills/gstack/.git && cd .claude/skills/gstack && ./setup` then add a "gstack" section to this project's CLAUDE.md that says to use the /browse skill from gstack for all web browsing, never use mcp__claude-in-chrome__* tools, lists the available skills, and tells Claude that if gstack skills aren't working, run `cd .claude/skills/gstack && ./setup` to build the binary and register skills.
```

## Как использовать gstack для taxi-bot

### Сценарий 1: Добавление новой функции

**БЕЗ gstack:**
```
Вы: Добавь функцию "Куда поехать на обед"
Claude: [сразу начинает писать код]
```

**С gstack:**
```
Вы: [enter plan mode] Добавь функцию "Куда поехать на обед"
Вы: /plan-ceo-review

Claude: "Куда поехать на обед" - это не просто список ресторанов.
        Настоящая задача - помочь таксисту максимизировать заработок
        во время обеденного перерыва. Вот что должна делать 10-звездочная
        версия:

        - Учитывать текущую зону и коэффициенты
        - Показывать рестораны рядом с зонами высокого спроса
        - Рассчитывать оптимальное время обеда (когда спрос падает)
        - Предлагать быстрые места (чтобы не терять много времени)
        - Учитывать предпочтения пользователя (кухня, бюджет)

Вы: /plan-eng-review

Claude: [Архитектурная диаграмма, state machine, edge cases, тесты]

        Архитектура:
        - Новая таблица user_lunch_preferences
        - API endpoint /api/lunch-recommendations
        - Интеграция с Yandex Maps API для ресторанов
        - Кэширование рекомендаций (Redis, 15 минут)
        - Фоновая задача обновления данных о ресторанах

        Edge cases:
        - Что если пользователь в зоне без ресторанов?
        - Что если все рестораны закрыты?
        - Как обрабатывать ошибки Yandex API?

Вы: [exit plan mode, implement]

Вы: /review

Claude: Race condition: два запроса могут перезаписать кэш одновременно.
        N+1 query: загрузка коэффициентов для каждого ресторана отдельно.
        Missing: обработка таймаута Yandex API.

Вы: [fix issues]

Вы: /ship

Claude: [Синхронизирует main, запускает тесты, пушит, создает PR]
```

### Сценарий 2: Тестирование админ-панели

**БЕЗ gstack:**
```
Вы: Проверь админку
Claude: Я не могу открыть браузер, опиши что не работает
```

**С gstack:**
```
Вы: /browse http://localhost:8000/admin

Claude: [Открывает браузер, логинится, кликает по вкладкам]

        > browse goto http://localhost:8000/admin
        > browse snapshot -i
        > browse fill @e3 "admin"
        > browse fill @e4 "password"
        > browse click @e5
        > browse screenshot /tmp/admin-dashboard.png

        Админка загружается. Все вкладки работают.
        Нашел 1 проблему: кнопка "Добавить мероприятие" не реагирует.
        Console error: "Uncaught TypeError: Cannot read property 'value' of null"

Вы: /qa http://localhost:8000/admin

Claude: [Полное QA тестирование + исправление багов]

        QA Report: Health Score 72/100

        Найдено 3 бага:
        1. CRITICAL: Кнопка "Добавить мероприятие" не работает
        2. HIGH: Мобильное меню не закрывается
        3. MEDIUM: График перекрывает сайдбар на <1024px

        Исправляю...

        fix(events): add null check for event form
        fix(ui): close mobile menu after selection
        fix(layout): adjust chart width for tablet

        Final Health Score: 72 → 94/100
```

### Сценарий 3: Код-ревью перед релизом

```
Вы: /review

Claude: [Анализирует diff против main]

        Найдено 4 проблемы:

        1. CRITICAL: bot/services/event_parser.py:334
           Race condition: два процесса могут создать дубликаты событий
           Рекомендация: добавить unique constraint на (name, end_time, zone_id)

        2. HIGH: bot/handlers/events.py:67
           N+1 query: загружаем пользователей для каждого события отдельно
           Рекомендация: использовать joinedload()

        3. MEDIUM: webapp/admin_dashboard.html:245
           XSS vulnerability: event.name вставляется без экранирования
           Рекомендация: использовать textContent вместо innerHTML

        4. LOW: bot/services/yandex_api.py:89
           Missing timeout: requests.get() без timeout может зависнуть навсегда
           Рекомендация: добавить timeout=30
```

## Какие skills наиболее полезны для taxi-bot

### Обязательные:

1. **`/review`** - перед каждым релизом
   - Находит race conditions, N+1 queries, SQL injection
   - Проверяет trust boundaries
   - Ловит баги, которые пройдут тесты

2. **`/ship`** - автоматизация релиза
   - Синхронизирует с main
   - Запускает тесты
   - Создает PR с правильным описанием
   - Обновляет CHANGELOG

3. **`/qa`** - тестирование админки и бота
   - Автоматически тестирует все страницы
   - Находит и исправляет баги
   - Делает скриншоты для доказательств
   - Дает health score до и после

### Очень полезные:

4. **`/browse`** - ручное тестирование
   - Проверка деплоя на продакшене
   - Тестирование сложных флоу (регистрация, оплата)
   - Проверка мобильной версии
   - Снятие скриншотов для багрепортов

5. **`/plan-eng-review`** - перед большими фичами
   - Архитектурные диаграммы
   - Проверка edge cases
   - Планирование тестов
   - Выявление узких мест

6. **`/retro`** - еженедельная ретроспектива
   - Анализ коммитов за неделю
   - Метрики по команде
   - Что сделано хорошо, что улучшить
   - Тренды производительности

### Опциональные:

7. **`/plan-ceo-review`** - для новых фич
   - Проверка продуктового видения
   - "Это правильная фича?"
   - Поиск 10-звездочной версии

8. **`/document-release`** - обновление документации
   - Автоматически обновляет README
   - Синхронизирует ARCHITECTURE.md
   - Обновляет CHANGELOG

## Создание кастомных skills для taxi-bot

Вы можете создать свои специализированные skills:

### Пример: `/taxi-deploy` skill

```markdown
---
name: taxi-deploy
version: 1.0.0
description: Deploy taxi-bot to production server
allowed-tools:
  - Bash
  - Read
  - AskUserQuestion
---

# Taxi-bot Production Deployment

## Step 1: Pre-deployment checks

1. Run tests locally:
   ```bash
   cd /opt/taxibot && python -m pytest tests/
   ```

2. Check current production status:
   ```bash
   ssh root@5.42.110.16 "cd /opt/taxibot && git log -1 --oneline"
   ```

3. Verify no users are currently active (check logs)

## Step 2: Deploy

1. SSH to server and pull latest:
   ```bash
   ssh root@5.42.110.16 "cd /opt/taxibot && git pull origin main"
   ```

2. Run database migrations if needed:
   ```bash
   ssh root@5.42.110.16 "cd /opt/taxibot && alembic upgrade head"
   ```

3. Restart bot:
   ```bash
   ssh root@5.42.110.16 "sudo systemctl restart taxibot"
   ```

4. Check logs for errors:
   ```bash
   ssh root@5.42.110.16 "sudo journalctl -u taxibot -n 50"
   ```

## Step 3: Smoke test

1. Send test message to bot
2. Check admin panel loads
3. Verify events are loading
4. Check coefficients are updating

## Step 4: Rollback if needed

If anything fails:
```bash
ssh root@5.42.110.16 "cd /opt/taxibot && git checkout <previous-commit> && sudo systemctl restart taxibot"
```
```

Сохраните как `.claude/skills/taxi-deploy/SKILL.md`

## Преимущества gstack для taxi-bot

### 1. Явные когнитивные режимы
Вместо "сделай код-ревью" → четкий режим параноидального ревьюера

### 2. Автоматизация рутины
`/ship` вместо ручного "git pull, test, push, create PR"

### 3. Реальное тестирование
`/qa` открывает браузер и тестирует админку как настоящий пользователь

### 4. Консистентность
Каждый раз одинаковый процесс ревью/деплоя/тестирования

### 5. Документация процессов
Skills = живая документация ваших workflow

## Следующие шаги

1. **Установите gstack** (команда выше)
2. **Попробуйте `/review`** на текущей ветке
3. **Используйте `/qa`** для тестирования админки
4. **Создайте `/taxi-deploy`** для автоматизации деплоя
5. **Добавьте `/retro`** в еженедельную рутину

## Пример workflow с gstack

```
Понедельник:
  - Новая фича → /plan-ceo-review → /plan-eng-review
  - Имплементация
  - /review перед коммитом
  - /ship для создания PR

Вторник-четверг:
  - Продолжение разработки
  - /qa после каждой большой фичи
  - /browse для ручной проверки

Пятница:
  - /review финального кода
  - /qa полное тестирование
  - /ship релиз
  - /retro анализ недели
  - /document-release обновление документации
```

Это превращает разработку из хаотичного процесса в четкую систему с явными этапами и проверками.
