#!/bin/bash
echo "════════════════════════════════════════════════════════════"
echo "  ПРОВЕРКА: КАКОЙ ПАРОЛЬ ИСПОЛЬЗУЕТ ROBOKASSA"
echo "════════════════════════════════════════════════════════════"
echo ""

# Параметры из реального платежа
OUT_SUM="5.00"
INV_ID="1773012323"
SIGNATURE_FROM_ROBOKASSA="79C73BA47400F27E39A471AFE1BF7F61"

# Получаем пароли из .env
PASSWORD1=$(grep "ROBOKASSA_PASSWORD1" /opt/taxibot/.env | cut -d= -f2)
PASSWORD2=$(grep "ROBOKASSA_PASSWORD2" /opt/taxibot/.env | cut -d= -f2)

echo "Password1: $PASSWORD1"
echo "Password2: $PASSWORD2"
echo ""

# Рассчитываем подпись с Password1
SIG_STRING1="${OUT_SUM}:${INV_ID}:${PASSWORD1}:Shp_duration=1:Shp_tier=pro:Shp_user_id=244638301"
CALC_SIG1=$(echo -n "$SIG_STRING1" | md5sum | awk '{print toupper($1)}')

# Рассчитываем подпись с Password2
SIG_STRING2="${OUT_SUM}:${INV_ID}:${PASSWORD2}:Shp_duration=1:Shp_tier=pro:Shp_user_id=244638301"
CALC_SIG2=$(echo -n "$SIG_STRING2" | md5sum | awk '{print toupper($1)}')

echo "Подпись от Robokassa: $SIGNATURE_FROM_ROBOKASSA"
echo ""
echo "С Password1: $CALC_SIG1"
if [ "$CALC_SIG1" = "$SIGNATURE_FROM_ROBOKASSA" ]; then
    echo "✅ СОВПАДАЕТ! Robokassa использует Password1"
else
    echo "❌ Не совпадает"
fi
echo ""
echo "С Password2: $CALC_SIG2"
if [ "$CALC_SIG2" = "$SIGNATURE_FROM_ROBOKASSA" ]; then
    echo "✅ СОВПАДАЕТ! Robokassa использует Password2"
else
    echo "❌ Не совпадает"
fi
echo ""
echo "════════════════════════════════════════════════════════════"
