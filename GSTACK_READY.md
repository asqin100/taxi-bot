# gstack установлен и готов к использованию! ✅

## Что работает

### ✅ Установленные skills (доступны глобально)

Следующие gstack skills установлены и готовы к использованию:

1. **`/review`** - Параноидальное код-ревью
   - Ищет race conditions, N+1 queries, SQL injection
   - Проверяет trust boundaries
   - Анализирует diff против base branch

2. **`/ship`** - Автоматизация релиза
   - Синхронизирует с main
   - Запускает тесты
   - Создает PR
   - Обновляет CHANGELOG

3. **`/plan-eng-review`** - Технический архитектор
   - Архитектурные диаграммы
   - Граничные случаи
   - Failure modes
   - Тестовая стратегия

4. **`/plan-ceo-review`** - Продуктовое мышление
   - Проверка продуктового видения
   - Поиск 10-star версии продукта
   - User empathy

5. **`/retro`** - Еженедельная ретроспектива
   - Анализ коммитов
   - Метрики команды
   - Персональный фидбек

6. **`/document-release`** - Обновление документации
   - Синхронизирует README, ARCHITECTURE
   - Обновляет CHANGELOG
   - Проверяет консистентность

7. **`/plan-design-review`** - Дизайн-аудит
   - Проверка UI/UX
   - AI Slop detection
   - Design system inference

8. **`/design-consultation`** - Создание дизайн-системы
   - Полная визуальная идентичность
   - Typography, colors, spacing
   - Интерактивный preview

### ✅ Кастомные skills для taxi-bot

1. **`/taxi-deploy`** - Деплой на продакшен
   - Pre-deployment checks
   - Автоматический деплой
   - Smoke tests
   - Rollback при ошибках

2. **`/taxi-test`** - Комплексное тестирование
   - Unit tests с coverage
   - Integration tests (APIs)
   - Performance tests
   - Manual QA checklist

## ❌ Что НЕ работает на Windows

**Browser-based skills** требуют компиляции нативного бинарника, что не работает на Windows:
- `/browse` - Browser automation
- `/qa` - QA testing + bug fixing
- `/qa-only` - Report-only QA
- `/setup-browser-cookies` - Cookie import

**Решение:** Используйте эти skills на Linux/macOS или используйте альтернативы:
- Вместо `/qa` → используйте `/taxi-test` для тестирования
- Вместо `/browse` → ручное тестирование в браузере

## Как использовать

### Пример 1: Код-ревью перед коммитом

```
/review
```

Я проанализирую ваш diff и найду:
- Race conditions
- N+1 queries
- Security issues
- Missing error handling
- Test coverage gaps

### Пример 2: Планирование новой фичи

```
[Войдите в plan mode]
Опишите фичу: "Добавить прогноз спроса на такси"

/plan-eng-review
```

Я создам:
- Архитектурную диаграмму
- Список граничных случаев
- Failure modes
- Тестовую стратегию

### Пример 3: Релиз

```
/ship
```

Я автоматически:
1. Синхронизирую с main
2. Запущу тесты
3. Запушу ветку
4. Создам PR с описанием

### Пример 4: Деплой на продакшен

```
/taxi-deploy
```

Я автоматически:
1. Проверю что вы на main
2. Запущу тесты
3. Задеплою на сервер
4. Проверю что все работает
5. Откачу если что-то сломалось

### Пример 5: Еженедельная ретроспектива

```
/retro
```

Я проанализирую:
- Коммиты за неделю
- Метрики (LOC, test coverage, PR count)
- Что сделано хорошо
- Что улучшить

## Следующие шаги

1. **Попробуйте `/review`** на текущей ветке
2. **Используйте `/taxi-test`** для запуска тестов
3. **Запустите `/retro`** в конце недели
4. **Используйте `/ship`** для следующего релиза

## Технические детали

- **Установлено:** `~/.claude/skills/gstack/`
- **Symlinks:** `~/.claude/skills/{review,ship,plan-eng-review,...}`
- **Конфигурация:** `.claude/CLAUDE.md` обновлен
- **Документация:** `GSTACK_INTEGRATION.md`

Все готово к работе! 🚀
