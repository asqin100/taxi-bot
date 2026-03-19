# 🚀 ИСПРАВЛЕНИЕ ROBOKASSA - ФИНАЛЬНАЯ ИНСТРУКЦИЯ

## ⚡ Быстрый старт (1 команда)

Скопируйте и выполните эту команду на своем компьютере:

```bash
ssh root@5.42.110.16 'cd /opt/taxibot && git pull origin main && bash fix_webhook_complete.sh'
```

Эта команда:
1. ✅ Подключится к серверу
2. ✅ Обновит код
3. ✅ Перезапустит бота
4. ✅ Определит правильные URL для Robokassa
5. ✅ Покажет URL, которые нужно вставить в Robokassa

---

## 📋 Что делать после выполнения команды

Скрипт покажет вам URL в таком формате:

```
Result URL (обязательно!):
  http://5.42.110.16/webhook/robokassa/result

Success URL:
  http://5.42.110.16/webhook/robokassa/success

Fail URL:
  http://5.42.110.16/webhook/robokassa/fail
```

**ИЛИ** (если nginx не настроен):

```
Result URL (обязательно!):
  http://5.42.110.16:8080/webhook/robokassa/result

Success URL:
  http://5.42.110.16:8080/webhook/robokassa/success

Fail URL:
  http://5.42.110.16:8080/webhook/robokassa/fail
```

---

## 🔧 Настройка Robokassa

1. Зайдите в личный кабинет Robokassa: https://auth.robokassa.ru/
2. Откройте настройки магазина **kefpulse**
3. Найдите поля:
   - **Result URL** (самое важное!)
   - **Success URL**
   - **Fail URL**
4. Вставьте URL, которые показал скрипт
5. **ОБЯЗАТЕЛЬНО нажмите кнопку "Сохранить"!**

---

## ✅ Тестирование

1. Откройте бота в Telegram: @KefPulse_bot
2. Выберите любую подписку (Pro/Premium/Elite)
3. Нажмите "Оплатить картой"
4. Используйте тестовую карту: **5555 5555 5555 5599**
5. Завершите оплату

### Что должно произойти:

✅ После оплаты откроется страница "Оплата успешна"
✅ Бот пришлет сообщение: "✅ Подписка активирована!"
✅ В /menu появятся новые функции подписки

---

## ❌ Если что-то не работает

### Проблема: Скрипт показывает ошибку "Webhook недоступен"

```bash
ssh root@5.42.110.16
sudo systemctl status taxibot
netstat -tlnp | grep 8080
journalctl -u taxibot -n 50
```

### Проблема: Страница Success не загружается

Значит URL указаны неправильно. Повторите команду:
```bash
ssh root@5.42.110.16 'bash /opt/taxibot/fix_webhook_complete.sh'
```

### Проблема: Бот не присылает сообщение после оплаты

Проверьте логи:
```bash
ssh root@5.42.110.16
journalctl -u taxibot --since "5 minutes ago" | grep -i robokassa
```

---

## 📞 Нужна помощь?

Пришлите вывод команды:
```bash
ssh root@5.42.110.16 'bash /opt/taxibot/fix_webhook_complete.sh'
```

И я помогу разобраться!
