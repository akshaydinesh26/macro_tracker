from functools import lru_cache
from pathlib import Path

from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings for the MacroTracker project.

    Attributes:
        fred_api_key (str): API key for accessing FRED data.
        database (Path): Path to the database directory.
        indicator_list (Path): Path to the YAML file containing the list of indicators.
        fred_endpoint (str): URL endpoint for accessing FRED series observations.
    """
    model_config = SettingsConfigDict(env_file=".env",extra="ignore")

    fred_api_key: str
    database: Path = Path("database")
    indicator_list: Path = Path("config/indicator.yaml")
    fred_endpoint: str = "https://api.stlouisfed.org/fred/series/observations"

@lru_cache
def get_settings() -> Settings:
    """
    Get the application settings, using caching to avoid repeated instantiation.

    Returns:
        Settings: The application settings instance.
    """

    try:
        return Settings()
    except ValidationError as e:
        raise RuntimeError(f"Invalid settings: {e}") from e

def load_indicator_list(Path_to_indicator_list: Path) -> dict:
    """
    Load the indicator list from the YAML file specified in the settings.

    Args:
        Path_to_indicator_list (Path): Path to the YAML file containing the list of indicators.

    Returns:
        dict: The loaded indicator list.
        {'indicator': 
            [
                {'name': 'Unemployment Rate', 'fred_code': 'UNRATE'},
                {'name': 'GDP', 'fred_code': 'GDP'}
            ]
        }
    """
    import yaml

    with open(Path_to_indicator_list, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
