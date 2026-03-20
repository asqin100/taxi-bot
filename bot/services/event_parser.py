"""Event parser service - fetches events from various sources."""
import json
import logging
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import aiohttp
from bs4 import BeautifulSoup

from bot.services import events as event_service
from bot.utils.timezone import now, from_timestamp, MOSCOW_TZ

logger = logging.getLogger(__name__)

VENUES_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "venues.json"

# Event duration by type (in hours)
EVENT_DURATIONS = {
    "concert": 3,
    "sport": 2,
    "conference": 4,
    "theater": 2.5,
    "other": 2,
}


class VenueMapper:
    """Maps venue names to zones."""

    def __init__(self):
        self.venues = []
        self._load_venues()

    def _load_venues(self):
        """Load venue mappings from JSON."""
        try:
            with open(VENUES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.venues = data.get("venues", [])
            logger.info("Loaded %d venue mappings", len(self.venues))
        except Exception as e:
            logger.error("Failed to load venues: %s", e)
            self.venues = []

    def find_zone(self, venue_name: str) -> Optional[str]:
        """Find zone ID for a venue name."""
        venue_lower = venue_name.lower().strip()

        for venue in self.venues:
            # Check main name
            if venue["name"].lower() in venue_lower or venue_lower in venue["name"].lower():
                return venue["zone_id"]

            # Check aliases
            for alias in venue.get("aliases", []):
                if alias.lower() in venue_lower or venue_lower in alias.lower():
                    return venue["zone_id"]

        return None

    def get_venue_info(self, venue_name: str) -> Optional[dict]:
        """Get full venue info (name, lat, lon) for a venue name."""
        venue_lower = venue_name.lower().strip()

        for venue in self.venues:
            # Check main name
            if venue["name"].lower() in venue_lower or venue_lower in venue["name"].lower():
                return {
                    "name": venue["name"],
                    "lat": venue.get("lat"),
                    "lon": venue.get("lon"),
                    "zone_id": venue["zone_id"]
                }

            # Check aliases
            for alias in venue.get("aliases", []):
                if alias.lower() in venue_lower or venue_lower in alias.lower():
                    return {
                        "name": venue["name"],
                        "lat": venue.get("lat"),
                        "lon": venue.get("lon"),
                        "zone_id": venue["zone_id"]
                    }

        return None


venue_mapper = VenueMapper()


async def parse_kudago_events() -> list[dict]:
    """Parse events from KudaGo API."""
    events = []

    # Categories to fetch: concerts, sports, theater, exhibitions, festivals
    categories = ["concert", "theater", "exhibition", "festival", "recreation"]

    try:
        url = "https://kudago.com/public-api/v1.4/events/"

        # Get events for next 30 days
        current_time = now()
        future_date = current_time + timedelta(days=30)

        # Convert to Unix timestamps
        actual_since = int(current_time.timestamp())
        actual_until = int(future_date.timestamp())

        # Fetch events for each category
        for category in categories:
            try:
                params = {
                    "location": "msk",
                    "categories": category,
                    "fields": "id,title,place,dates",
                    "expand": "place",
                    "page_size": 100,
                    "actual_since": actual_since,
                    "actual_until": actual_until,
                }

                logger.info(f"Fetching {category} events from KudaGo API")

                async with aiohttp.ClientSession() as session:
                    async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                        logger.info(f"KudaGo API response for {category}: status {resp.status}")

                        if resp.status != 200:
                            text = await resp.text()
                            logger.error("KudaGo API failed for %s with status %d: %s", category, resp.status, text[:500])
                            continue

                        data = await resp.json()
                        results = data.get("results", [])

                        logger.info("Fetched %d %s events from KudaGo API", len(results), category)

                        for event_json in results:
                            try:
                                event_data = _parse_kudago_event(event_json)
                                if event_data:
                                    events.append(event_data)
                            except Exception as e:
                                logger.debug("Failed to parse KudaGo event: %s", e)

            except Exception as e:
                logger.error("Failed to fetch %s events: %s", category, e)

        logger.info("Parsed %d total events from KudaGo", len(events))

    except Exception as e:
        logger.error("Failed to parse KudaGo API: %s", e)

    return events


async def parse_yandex_afisha() -> list[dict]:
    """Parse events from Yandex.Afisha using embedded JSON data (DEPRECATED - use KudaGo instead)."""
    events = []

    try:
        # Yandex.Afisha concerts page
        url = "https://afisha.yandex.ru/moscow/concert"

        # Add browser headers to avoid blocking
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
        }

        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status != 200:
                    logger.warning("Yandex.Afisha returned status %d", resp.status)
                    return events

                html = await resp.text()

                # Extract JSON data from Apollo cache or __NEXT_DATA__
                events_data = _extract_json_events(html)

                for event_json in events_data[:50]:  # Limit to first 50 events
                    try:
                        event_data = _parse_json_event(event_json)
                        if event_data:
                            events.append(event_data)
                    except Exception as e:
                        logger.debug("Failed to parse event: %s", e)

        logger.info("Parsed %d events from Yandex.Afisha", len(events))

    except Exception as e:
        logger.error("Failed to parse Yandex.Afisha: %s", e)

    return events


def _parse_event_card(card) -> Optional[dict]:
    """Parse individual event card (deprecated - kept for compatibility)."""
    return None


def _extract_json_events(html: str) -> list[dict]:
    """Extract event data from embedded JSON in HTML."""
    events = []

    try:
        # Look for Apollo cache data
        apollo_match = re.search(r'window\.__APOLLO_STATE__\s*=\s*({.+?});', html, re.DOTALL)
        if apollo_match:
            apollo_data = json.loads(apollo_match.group(1))
            events.extend(_parse_apollo_cache(apollo_data))

        # Look for __NEXT_DATA__
        next_data_match = re.search(r'<script id="__NEXT_DATA__"[^>]*>({.+?})</script>', html, re.DOTALL)
        if next_data_match:
            next_data = json.loads(next_data_match.group(1))
            events.extend(_parse_next_data(next_data))

    except Exception as e:
        logger.error("Failed to extract JSON events: %s", e)

    return events


def _parse_apollo_cache(apollo_data: dict) -> list[dict]:
    """Parse events from Apollo GraphQL cache."""
    events = []

    for key, value in apollo_data.items():
        if isinstance(value, dict) and value.get("__typename") == "Event":
            try:
                # Extract event fields
                event = {
                    "id": value.get("id"),
                    "title": value.get("title") or value.get("name"),
                    "venue": None,
                    "dates": [],
                }

                # Extract venue
                if "place" in value and isinstance(value["place"], dict):
                    event["venue"] = value["place"].get("title") or value["place"].get("name")
                elif "venue" in value:
                    if isinstance(value["venue"], dict):
                        event["venue"] = value["venue"].get("title") or value["venue"].get("name")
                    else:
                        event["venue"] = value["venue"]

                # Extract dates
                if "schedule" in value and isinstance(value["schedule"], dict):
                    dates_list = value["schedule"].get("dates", [])
                    if isinstance(dates_list, list):
                        event["dates"] = dates_list
                elif "date" in value:
                    event["dates"] = [value["date"]]
                elif "dates" in value:
                    event["dates"] = value.get("dates", [])

                if event["title"] and event["venue"] and event["dates"]:
                    events.append(event)

            except Exception as e:
                logger.debug("Failed to parse Apollo event: %s", e)

    return events


def _parse_next_data(next_data: dict) -> list[dict]:
    """Parse events from __NEXT_DATA__."""
    events = []

    try:
        # Navigate through Next.js data structure
        props = next_data.get("props", {})
        page_props = props.get("pageProps", {})

        # Look for events in various possible locations
        if "events" in page_props:
            events_list = page_props["events"]
        elif "initialData" in page_props:
            events_list = page_props["initialData"].get("events", [])
        else:
            events_list = []

        for event_data in events_list:
            if isinstance(event_data, dict):
                event = {
                    "id": event_data.get("id"),
                    "title": event_data.get("title") or event_data.get("name"),
                    "venue": None,
                    "dates": [],
                }

                # Extract venue
                place = event_data.get("place") or event_data.get("venue")
                if isinstance(place, dict):
                    event["venue"] = place.get("title") or place.get("name")
                elif isinstance(place, str):
                    event["venue"] = place

                # Extract dates
                schedule = event_data.get("schedule", {})
                if isinstance(schedule, dict):
                    event["dates"] = schedule.get("dates", [])
                elif "date" in event_data:
                    event["dates"] = [event_data["date"]]

                if event["title"] and event["venue"] and event["dates"]:
                    events.append(event)

    except Exception as e:
        logger.debug("Failed to parse Next.js data: %s", e)

    return events


def _parse_kudago_event(event_json: dict) -> Optional[dict]:
    """Parse individual event from KudaGo API."""
    try:
        title = event_json.get("title")
        place = event_json.get("place")
        dates = event_json.get("dates", [])

        if not title or not place or not dates:
            return None

        # Extract venue name and coordinates from place object
        venue_name = None
        venue_lat = None
        venue_lon = None

        if isinstance(place, dict):
            venue_name = place.get("title") or place.get("name")
            # Try to get coordinates from place
            if "coords" in place and place["coords"]:
                coords = place["coords"]
                if "lat" in coords and "lon" in coords:
                    venue_lat = coords["lat"]
                    venue_lon = coords["lon"]
        elif isinstance(place, str):
            venue_name = place

        if not venue_name:
            logger.debug("No venue name for event: %s", title)
            return None

        # Try to detect sports team and use their home venue
        zone_id, detected_venue = _detect_sports_venue(title, venue_name)

        # If sports venue detected, use it
        if detected_venue:
            venue_name = detected_venue
            venue_info = venue_mapper.get_venue_info(venue_name)
            if venue_info:
                venue_lat = venue_info.get("lat")
                venue_lon = venue_info.get("lon")

        # If no zone found yet, try regular venue mapping
        if not zone_id:
            zone_id = venue_mapper.find_zone(venue_name)

        if not zone_id:
            logger.debug("No zone found for venue: %s", venue_name)
            return None

        # If we don't have coordinates from API, try to get from venues.json
        if not venue_lat or not venue_lon:
            venue_info = venue_mapper.get_venue_info(venue_name)
            if venue_info:
                venue_lat = venue_info.get("lat")
                venue_lon = venue_info.get("lon")

        # Get the earliest future date
        now_timestamp = now().timestamp()
        future_dates = [d for d in dates if isinstance(d, dict) and d.get("end", 0) > now_timestamp]

        if not future_dates:
            return None

        # Use the earliest date
        first_date = min(future_dates, key=lambda d: d.get("start", 0))
        end_timestamp = first_date.get("end")

        if not end_timestamp:
            return None

        # Convert Unix timestamp to datetime in Moscow timezone
        # KudaGo API returns UTC timestamps, convert to Moscow time
        end_time = from_timestamp(end_timestamp)

        # Determine event type
        event_type = _guess_event_type(title)

        return {
            "name": title,
            "zone_id": zone_id,
            "event_type": event_type,
            "end_time": end_time,
            "venue_name": venue_name,
            "venue_lat": venue_lat,
            "venue_lon": venue_lon,
        }

    except Exception as e:
        logger.debug("Failed to parse KudaGo event: %s", e)
        return None


def _parse_json_event(event_json: dict) -> Optional[dict]:
    """Parse individual event from JSON data (Yandex.Afisha format - DEPRECATED)."""
    try:
        title = event_json.get("title")
        venue_name = event_json.get("venue")
        dates = event_json.get("dates", [])

        if not title or not venue_name or not dates:
            return None

        # Find zone for this venue
        zone_id = venue_mapper.find_zone(venue_name)
        if not zone_id:
            logger.debug("No zone found for venue: %s", venue_name)
            return None

        # Parse first date (use earliest date if multiple)
        first_date = dates[0] if isinstance(dates, list) else dates
        start_time = _parse_russian_datetime(first_date)

        if not start_time:
            logger.debug("Could not parse date: %s", first_date)
            return None

        # Determine event type and calculate end time
        event_type = _guess_event_type(title)
        duration_hours = EVENT_DURATIONS.get(event_type, 2)
        end_time = start_time + timedelta(hours=duration_hours)

        return {
            "name": title,
            "zone_id": zone_id,
            "event_type": event_type,
            "end_time": end_time,
        }

    except Exception as e:
        logger.debug("Failed to parse JSON event: %s", e)
        return None


def _parse_datetime(date_text: str) -> Optional[datetime]:
    """Parse datetime from various formats."""
    # Remove extra whitespace
    date_text = " ".join(date_text.split())

    # Try common formats
    formats = [
        "%d.%m %H:%M",
        "%d.%m.%Y %H:%M",
        "%d %B %H:%M",
        "%d %b %H:%M",
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(date_text, fmt)
            # If year not specified, use current year
            if dt.year == 1900:
                dt = dt.replace(year=datetime.now().year)
            # If date is in the past, assume next year
            if dt < datetime.now():
                dt = dt.replace(year=datetime.now().year + 1)
            return dt
        except ValueError:
            continue

    return None


def _parse_russian_datetime(date_text: str) -> Optional[datetime]:
    """Parse datetime from Russian date formats."""
    if not date_text or not isinstance(date_text, str):
        return None

    # Russian month names mapping
    russian_months = {
        "января": 1, "февраля": 2, "марта": 3, "апреля": 4,
        "мая": 5, "июня": 6, "июля": 7, "августа": 8,
        "сентября": 9, "октября": 10, "ноября": 11, "декабря": 12,
    }

    try:
        # Clean up the text
        date_text = date_text.strip().lower()

        # Handle "8 и 9 марта" - take first date
        if " и " in date_text:
            date_text = date_text.split(" и ")[0].strip()

        # Extract time if present (e.g., "28 марта, 20:00")
        time_match = re.search(r'(\d{1,2}):(\d{2})', date_text)
        hour = int(time_match.group(1)) if time_match else 20  # Default to 20:00
        minute = int(time_match.group(2)) if time_match else 0

        # Extract day and month
        # Pattern: "28 марта" or "28 марта, 20:00"
        date_match = re.search(r'(\d{1,2})\s+([а-яё]+)', date_text)
        if not date_match:
            return None

        day = int(date_match.group(1))
        month_name = date_match.group(2)

        # Find month number
        month = None
        for ru_month, month_num in russian_months.items():
            if ru_month in month_name:
                month = month_num
                break

        if not month:
            return None

        # Create datetime
        year = datetime.now().year
        dt = datetime(year, month, day, hour, minute)

        # If date is in the past, assume next year
        if dt < datetime.now():
            dt = dt.replace(year=year + 1)

        return dt

    except Exception as e:
        logger.debug("Failed to parse Russian date '%s': %s", date_text, e)
        return None


def _detect_sports_venue(title: str, venue_name: str) -> tuple[str, str]:
    """Detect sports team and return their home venue and zone."""
    title_lower = title.lower()

    # Football teams
    if any(word in title_lower for word in ["спартак", "spartak"]) and "хоккей" not in title_lower:
        return "northwest", "Спартак Стадион"

    if "цска" in title_lower:
        if "хоккей" in title_lower or "hockey" in title_lower:
            return "northwest", "ЦСКА Арена"
        elif "баскетбол" in title_lower or "basketball" in title_lower:
            return "west", "Мегаспорт"
        else:  # Football
            return "north", "ВТБ Арена"

    if "динамо" in title_lower or "dynamo" in title_lower:
        return "north", "ВТБ Арена"

    if "локомотив" in title_lower or "lokomotiv" in title_lower:
        return "northeast", "Локомотив Стадион"

    # General sports venues
    if "лужники" in title_lower or "luzhniki" in title_lower:
        return "south", "Лужники"

    if "олимпийский" in title_lower or "olympic" in title_lower:
        return "center", "Олимпийский"

    # Return None if no specific venue detected
    return None, None


def _guess_event_type(title: str) -> str:
    """Guess event type from title."""
    title_lower = title.lower()

    # Sport events - expanded keywords
    sport_keywords = [
        # General
        "матч", "игра", "турнир", "чемпионат", "кубок", "лига", "финал", "полуфинал", "плей-офф",
        # Football
        "футбол", "football", "рпл", "премьер-лига", "спартак", "цска", "динамо", "локомотив",
        # Hockey
        "хоккей", "hockey", "кхл", "нхл",
        # Basketball
        "баскетбол", "basketball", "втб", "единая лига",
        # Other sports
        "волейбол", "volleyball", "теннис", "tennis", "бокс", "boxing", "бой",
        "мма", "mma", "ufc", "fight", "единоборств",
        "фигурное катание", "figure skating", "легкая атлетика", "athletics",
        "гимнастика", "gymnastics", "плавание", "swimming",
        "биатлон", "biathlon", "лыжи", "skiing",
        # Sports venues
        "стадион", "stadium", "арена", "arena", "дворец спорта", "sports palace",
        # General sports terms
        "спорт", "sport", "олимпиада", "olympic"
    ]

    if any(word in title_lower for word in sport_keywords):
        return "sport"

    # Concerts and music
    elif any(word in title_lower for word in ["концерт", "concert", "шоу", "show", "фестиваль", "festival", "музык"]):
        return "concert"

    # Theater and performances
    elif any(word in title_lower for word in ["спектакль", "театр", "theater", "play", "опера", "балет", "мюзикл"]):
        return "theater"

    # Conferences and exhibitions
    elif any(word in title_lower for word in ["конференция", "форум", "выставка", "conference", "expo", "exhibition"]):
        return "conference"

    else:
        return "other"


async def fetch_and_store_events():
    """Fetch events from all sources and store in database."""
    logger.info("Starting event parsing...")

    # Parse from KudaGo API
    events = await parse_kudago_events()

    # Store events (avoid duplicates)
    stored_count = 0
    for event_data in events:
        try:
            # Check if event already exists (same name and end time within 1 hour)
            existing = await event_service.get_upcoming_events(limit=100)
            is_duplicate = False

            for existing_event in existing:
                if (existing_event.name == event_data["name"] and
                    abs((existing_event.end_time - event_data["end_time"]).total_seconds()) < 3600):
                    is_duplicate = True
                    break

            if not is_duplicate:
                await event_service.create_event(**event_data)
                stored_count += 1
                logger.info("Added event: %s at %s (zone: %s)",
                           event_data["name"],
                           event_data["end_time"].strftime("%d.%m %H:%M"),
                           event_data["zone_id"])

        except Exception as e:
            logger.error("Failed to store event %s: %s", event_data.get("name"), e)

    logger.info("Stored %d new events from KudaGo", stored_count)
    return stored_count
