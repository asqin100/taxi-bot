from pydantic_settings import BaseSettings
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    bot_token: str
    bot_username: str = "KefPulse_bot"  # Bot username for referral links
    channel_id: str = "@kefpulsechannel"  # Channel ID for mandatory subscription
    admin_ids: str = ""  # Comma-separated admin Telegram IDs
    yandex_api_key: str = ""
    yandex_traffic_api_key: str = ""  # Yandex Traffic/Jams API key
    yandex_bearer_token: str = ""
    yandex_uuid: str = ""
    yandex_device_id: str = ""
    yandex_mob_id: str = ""
    # Multiple device credentials for load distribution (pipe-separated)
    yandex_bearer_tokens: str = ""  # Multiple tokens: token1|token2|token3
    yandex_uuids: str = ""  # Multiple UUIDs: uuid1|uuid2|uuid3
    yandex_device_ids: str = ""  # Multiple device IDs: id1|id2|id3
    yandex_mob_ids: str = ""  # Multiple mob IDs: id1|id2|id3
    yandex_geocoder_key: str = ""  # Yandex Geocoder API key
    tomtom_api_key: str = ""  # TomTom Traffic API key
    gemini_api_key: str = ""  # Google Gemini API key for AI advisor
    yookassa_shop_id: str = ""  # YooKassa shop ID
    yookassa_secret_key: str = ""  # YooKassa secret key
    robokassa_merchant_login: str = ""  # Robokassa merchant login
    robokassa_password1: str = ""  # Robokassa password #1 (for payment link)
    robokassa_password2: str = ""  # Robokassa password #2 (for result verification)
    robokassa_test_mode: bool = True  # Robokassa test mode (True for testing, False for production)
    payment_provider: str = "robokassa"  # Payment provider: "yookassa" or "robokassa"
    admin_password: str = "admin123!@#"  # Admin panel password
    database_url: str = f"sqlite+aiosqlite:///{BASE_DIR / 'data' / 'bot.db'}"  # Production uses PostgreSQL
    db_url: str = ""  # Deprecated, use database_url
    parse_interval_seconds: int = 480  # 8 minutes - parallel batching allows faster updates
    default_surge_threshold: float = 1.5
    webapp_url: str = ""
    web_host: str = "0.0.0.0"  # Web server host
    web_port: int = 8080
    redis_url: str = "redis://localhost:6379/0"  # Redis connection URL
    environment: str = "development"  # development or production

    model_config = {"env_file": str(BASE_DIR / ".env"), "env_file_encoding": "utf-8", "extra": "allow"}

    @property
    def effective_db_url(self) -> str:
        """Return the effective database URL (database_url takes precedence over db_url)"""
        return self.database_url or self.db_url


settings = Settings()
