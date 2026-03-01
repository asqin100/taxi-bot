from pydantic_settings import BaseSettings
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    bot_token: str
    yandex_api_key: str = ""
    yandex_traffic_api_key: str = ""  # Yandex Traffic/Jams API key
    yandex_bearer_token: str = ""
    yandex_uuid: str = ""
    yandex_device_id: str = ""
    yandex_mob_id: str = ""
    yandex_geocoder_key: str = ""  # Yandex Geocoder API key
    tomtom_api_key: str = ""  # TomTom Traffic API key
    anthropic_api_key: str = ""  # Claude API key for AI advisor
    yookassa_shop_id: str = ""  # YooKassa shop ID
    yookassa_secret_key: str = ""  # YooKassa secret key
    db_url: str = f"sqlite+aiosqlite:///{BASE_DIR / 'data' / 'bot.db'}"
    parse_interval_seconds: int = 120
    default_surge_threshold: float = 1.5
    webapp_url: str = ""
    web_port: int = 8080

    model_config = {"env_file": str(BASE_DIR / ".env"), "env_file_encoding": "utf-8"}


settings = Settings()
