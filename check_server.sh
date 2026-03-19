#!/bin/bash
echo "=== Git status on server ==="
cd ~/taxi-bot && git log --oneline -5
echo ""
echo "=== Current branch ==="
git branch
echo ""
echo "=== Check if Finance button exists ==="
grep -n "💰 Финансы" ~/taxi-bot/bot/keyboards/inline.py
echo ""
echo "=== Bot process ==="
ps aux | grep python | grep -v grep
