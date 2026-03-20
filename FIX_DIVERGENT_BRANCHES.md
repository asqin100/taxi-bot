# 🔧 ИСПРАВЛЕНИЕ: Divergent Branches

## Проблема
На сервере есть локальные коммиты, которых нет на GitHub, и наоборот.

## ✅ РЕШЕНИЕ (выбери один вариант)

### Вариант 1: Merge (рекомендуется для production)
Сохраняет все изменения, создает merge commit.

```bash
cd /opt/taxibot
git config pull.rebase false
git pull origin main
systemctl restart taxibot
systemctl status taxibot
tail -50 bot.log
```

### Вариант 2: Rebase (чистая история)
Применяет локальные изменения поверх новых.

```bash
cd /opt/taxibot
git config pull.rebase true
git pull origin main
systemctl restart taxibot
systemctl status taxibot
tail -50 bot.log
```

### Вариант 3: Сброс локальных изменений (если они не важны)
**ВНИМАНИЕ:** Удалит все локальные коммиты на сервере!

```bash
cd /opt/taxibot
git fetch origin main
git reset --hard origin/main
systemctl restart taxibot
systemctl status taxibot
tail -50 bot.log
```

---

## 🔍 Сначала проверь что изменилось локально

```bash
cd /opt/taxibot
git log origin/main..HEAD --oneline
```

Это покажет локальные коммиты, которых нет на GitHub.

---

## 📋 РЕКОМЕНДАЦИЯ

Если на сервере нет важных изменений (обычно их не должно быть), используй **Вариант 3** (reset).

Если есть важные локальные изменения, используй **Вариант 1** (merge).

---

## 🚀 БЫСТРАЯ КОМАНДА (Вариант 3 - сброс)

```bash
cd /opt/taxibot && git fetch origin main && git reset --hard origin/main && systemctl restart taxibot && systemctl status taxibot && tail -50 bot.log
```
