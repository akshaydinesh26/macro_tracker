from pathlib import Path

import pandas as pd
import requests

from macrotracker.config.source import Settings
from macrotracker.database.create_db import Database
from macrotracker.database.storage import DatabaseNotFound


# fuction to sync indicators in the path -  from respective source
# storage has the database connection path - database_path
def sync(storage: Database, indicators: dict, base_cfg: Settings):
    # Sync each indicator in the database
    indicator_list = indicators.get("indicator",[])
    for indicator in indicator_list:
        # db created in Database class
        indicator_db = Path(storage.database_path) / f"{indicator['fred_code']}.db"
        # sync database
        params = make_params(indicator['fred_code'], base_cfg.fred_api_key)
        query = query_api(base_cfg.fred_endpoint, params, timeout=30)
        # extract observation
        data_json = query.get("observations", [])
        data_table = pd.DataFrame(data_json)
        data_table['date'] = pd.to_datetime(data_table['date'])
        data_table['value'] = pd.to_numeric(data_table['value'])
        data_table.to_csv(indicator_db, index=False, header=True)

def make_params(indicator_id: str, api_key: str) -> dict:
    return {
        "series_id": indicator_id,
        "api_key": api_key,
        "file_type": "json",
    }

def query_api(endpoint: str, params: dict, timeout: int = 30) -> dict:
    response = requests.get(endpoint, params=params, timeout=timeout)
    response.raise_for_status()
    content_type = response.headers.get("content-type", "")
    if response.status_code == 404:
        raise DatabaseNotFound(
            f"FRED returned 404 Not Found: {response.text[:300]}"
        )
    if "json" not in content_type.lower():
        raise RuntimeError(
            f"FRED returned {content_type or 'unknown content'}: "
            f"{response.text[:300]}"
        )
    return response.json()






