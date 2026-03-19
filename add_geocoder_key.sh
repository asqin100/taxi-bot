#!/bin/bash
# Add Yandex Geocoder API key to server .env

echo "Adding YANDEX_GEOCODER_KEY to .env..."

cd /opt/taxibot

# Check if key already exists
if grep -q "YANDEX_GEOCODER_KEY" .env; then
    echo "Key already exists, updating..."
    sed -i 's/YANDEX_GEOCODER_KEY=.*/YANDEX_GEOCODER_KEY=dc8e2921-b988-4e32-b1f2-b8da88737339/' .env
else
    echo "Adding new key..."
    echo "YANDEX_GEOCODER_KEY=dc8e2921-b988-4e32-b1f2-b8da88737339" >> .env
fi

echo "✅ Done! Key added to .env"
echo ""
echo "Now deploy with:"
echo "cd /opt/taxibot && ./update_bot.sh"
