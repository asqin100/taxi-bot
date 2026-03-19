# 🚀 Robokassa Integration - Quick Start

**Статус:** ✅ Готово к тестированию
**Дата:** 2026-03-08

---

## 📦 Что сделано

Интеграция Robokassa для приема платежей полностью реализована:

- ✅ Payment service (`bot/services/payment_robokassa.py`)
- ✅ Webhook endpoints (`bot/web/api.py`)
- ✅ Subscription handlers обновлены
- ✅ Тестовая кнопка "5₽ за 1 день Pro" добавлена
- ✅ Уведомления пользователям после оплаты
- ✅ Диагностические скрипты

---

## 🎯 Быстрый старт

### 1. Подключитесь к серверу

```bash
ssh root@5.42.110.16
cd /opt/taxibot
git pull origin main
```

### 2. Запустите диагностику

```bash
bash quick_test.sh
```

Скрипт проверит:
- ✓ Работает ли бот
- ✓ Слушает ли порт 8080
- ✓ Открыт ли порт в файрволе
- ✓ Доступен ли webhook
- ✓ Настроены ли пароли Robokassa

### 3. Исправьте проблемы (если есть)

**Если порт закрыт:**
```bash
sudo ufw allow 8080/tcp
sudo ufw reload
```

**Если бот не запущен:**
```bash
systemctl start taxibot
systemctl status taxibot
```

### 4. Настройте Result URL в Robokassa

1. Откройте: https://auth.robokassa.ru/
2. Магазин: **kefpulse** → Технические настройки
3. Раздел: **БОЕВОЙ РЕЖИМ** (не тестовый!)
4. Введите:
   - **Result URL:** `http://5.42.110.16:8080/webhook/robokassa/result`
   - **Метод:** GET
5. Нажмите **"Сохранить"**

### 5. Тестовый платеж

**На сервере запустите мониторинг:**
```bash
bash monitor_webhook.sh
```

**В боте сделайте тестовый платеж:**
1. Откройте @KefPulse_bot
2. `/menu` → 💎 Подписка → ⬆️ Улучшить тариф
3. Нажмите: **🧪 ТЕСТ — 5₽ (1 день)**
4. Оплатите 5 рублей

### 6. Проверьте результат

**В логах должно появиться:**
```
Received Robokassa Result callback: InvId=...
Successfully processed Robokassa payment...
Sent payment confirmation to user...
```

**В боте придет уведомление:**
```
✅ Подписка активирована!
Тариф: ⭐ Pro
Сумма: 5₽
Срок: 1 дней
```

---

## 📋 Полная документация

- **FINAL_CHECKLIST.md** - Подробный чек-лист со всеми шагами
- **SESSION_STATUS.md** - Текущий статус проекта и история
- **quick_test.sh** - Автоматическая диагностика
- **monitor_webhook.sh** - Мониторинг webhook в реальном времени

---

## 🔧 Технические детали

### Настройки Robokassa

- **Merchant Login:** kefpulse
- **Password #1:** Er1jVuWGOj0I9weDrs42
- **Password #2:** ED44A3KMHu6r7eGWhcGs
- **Test Mode:** False (боевой режим)

### Webhook URLs

- **Result URL:** `http://5.42.110.16:8080/webhook/robokassa/result` (GET)
- **Success URL:** `http://5.42.110.16:8080/webhook/robokassa/success` (GET)
- **Fail URL:** `http://5.42.110.16:8080/webhook/robokassa/fail` (GET)

### Цены подписок

- **Pro:** 299₽/месяц
- **Premium:** 499₽/месяц
- **Elite:** 999₽/месяц
- **Test:** 5₽/день (только для тестирования)

---

## 🐛 Troubleshooting

### Webhook не вызывается

**Проблема:** Платеж проходит, но подписка не активируется.

**Решение:**
1. Проверьте, что Result URL сохранен в Robokassa (БОЕВОЙ режим!)
2. Проверьте файрвол: `sudo ufw status`
3. Проверьте логи: `journalctl -u taxibot -f`

### Порт 8080 недоступен

**Проблема:** Webhook не отвечает извне.

**Решение:**
```bash
sudo ufw allow 8080/tcp
sudo ufw reload
```

### Бот не запускается

**Проблема:** Сервис taxibot не работает.

**Решение:**
```bash
systemctl status taxibot
journalctl -u taxibot -n 50
systemctl restart taxibot
```

---

## 📞 Контакты

- **Сервер:** 5.42.110.16
- **Бот:** @KefPulse_bot
- **Robokassa магазин:** kefpulse

---

## ✅ Чек-лист готовности

- [x] Код написан и протестирован
- [x] Webhook endpoints созданы
- [x] Тестовая кнопка добавлена
- [x] Диагностические скрипты созданы
- [x] Документация написана
- [x] Все закоммичено в main
- [ ] Порт 8080 открыт на сервере
- [ ] Result URL сохранен в Robokassa
- [ ] Тестовый платеж выполнен успешно

---

**Начните с команды:** `bash quick_test.sh`

Удачи! 🚀
