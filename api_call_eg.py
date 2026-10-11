import os
from pathlib import Path
import requests
from dotenv import load_dotenv
#load env variables from .env file
load_dotenv(Path(__file__).resolve().parent / ".env")

API_KEY = os.getenv("FRED_API_KEY")
if not API_KEY:
    raise RuntimeError("FRED_API_KEY is missing from the .env file")

url = "https://api.stlouisfed.org/fred/series/observations"
params = {
    "series_id": "CPIAUCSL",
    "api_key": API_KEY,
    "file_type": "json",
}
response = requests.get(url, params=params, timeout=30)
response.raise_for_status()
 # Give a useful error if the server returns non-JSON content.
content_type = response.headers.get("content-type", "")
if "json" not in content_type.lower():
        raise RuntimeError(
            f"FRED returned {content_type or 'unknown content'}: "
            f"{response.text[:300]}"
        )
page = response.json()
page_observations = page.get("observations", [])
print(page_observations[-1])
