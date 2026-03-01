from bot.services.yandex_api import SurgeData
from bot.services.zones import get_zone_names_map

TARIFF_LABELS = {"econom": "Эконом", "comfort": "Комфорт", "business": "Бизнес"}


def format_surge_table(data: list[SurgeData], tariff: str | None = None) -> str:
    """Format surge data as a readable text table."""
    zone_names = get_zone_names_map()
    if tariff:
        data = [d for d in data if d.tariff == tariff]

    # Group by zone
    by_zone: dict[str, dict[str, float]] = {}
    for d in data:
        by_zone.setdefault(d.zone_id, {})[d.tariff] = d.coefficient

    if not by_zone:
        return "Нет данных о коэффициентах. Попробуйте позже."

    lines = ["📊 Коэффициенты Яндекс Такси\n"]
    for zone_id, tariffs in sorted(by_zone.items(), key=lambda x: max(x[1].values()), reverse=True):
        zone_name = zone_names.get(zone_id, zone_id)
        parts = [f"{TARIFF_LABELS.get(t, t)}: x{c}" for t, c in sorted(tariffs.items())]
        lines.append(f"📍 {zone_name}\n   {' | '.join(parts)}")

    return "\n".join(lines)


def format_top_zones(data: list[SurgeData]) -> str:
    zone_names = get_zone_names_map()
    if not data:
        return "Нет данных."

    lines = ["🏆 <b>ТОП-5 ЖИРНЫХ ТОЧЕК</b>\n"]

    for i, d in enumerate(data, 1):
        zone_name = zone_names.get(d.zone_id, d.zone_id)
        tariff = TARIFF_LABELS.get(d.tariff, d.tariff)

        # Emoji based on coefficient level
        if d.coefficient >= 2.5:
            emoji = "🔥🔥🔥"
            status = "ОГОНЬ"
        elif d.coefficient >= 2.0:
            emoji = "🔥🔥"
            status = "ЖИРНО"
        elif d.coefficient >= 1.5:
            emoji = "🔥"
            status = "ХОРОШО"
        else:
            emoji = "⚡"
            status = "НОРМ"

        # Medal emoji for top 3
        medal = ""
        if i == 1:
            medal = "🥇 "
        elif i == 2:
            medal = "🥈 "
        elif i == 3:
            medal = "🥉 "

        lines.append(
            f"{medal}<b>{i}. {zone_name}</b>\n"
            f"   {emoji} <code>x{d.coefficient}</code> • {tariff} • {status}"
        )

    lines.append("\n💡 <i>Совет: проверьте пробки перед выездом</i>")
    return "\n".join(lines)
