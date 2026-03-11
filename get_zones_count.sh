cd /opt/taxibot && python3 -c "from bot.services.zones import get_zones; zones = get_zones(); print(f'Всего зон: {len(zones)}'); print(f'Зоны: {[z.id for z in zones[:10]]}...')"
