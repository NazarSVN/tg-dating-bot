import aiohttp
from config import GOOGLE_API_KEY
import requests
import os

ALLOWED_COUNTRIES = {
    "AL", "AD", "AT", "BA", "BE", "BG", "CH", "CY", "CZ", "DE", "DK", "EE", "ES", "FI", "FR",
    "GR", "HR", "HU", "IE", "IS", "IT", "LI", "LT", "LU", "LV", "MC", "MD", "ME", "MK", "MT",
    "NL", "NO", "PL", "PT", "RO", "RS", "SE", "SI", "SK", "SM", "UA", "VA", "XK", "CA", "TR",
    "UK", "US", "BR"
}

def coords_to_city(lat: float, lon: float) -> str | None:
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "latlng": f"{lat},{lon}",
        "key": GOOGLE_API_KEY,
        "language": "uk"
    }
    r = requests.get(url, params=params)
    if r.status_code != 200:
        return None

    data = r.json()
    if data.get("status") != "OK":
        return None

    for component in data["results"][0]["address_components"]:
        if "locality" in component["types"]:
            return component["long_name"]
        if "administrative_area_level_1" in component["types"]:
            return component["long_name"]

    return None


async def validate_city(city_name: str) -> str | None:
    async with aiohttp.ClientSession() as session:
        url = "https://maps.googleapis.com/maps/api/place/autocomplete/json"
        params = {
            "input": city_name,
            "types": "(cities)",
            "language": "uk",
            "key": GOOGLE_API_KEY,
        }
        async with session.get(url, params=params) as resp:
            data = await resp.json()
            if data.get("status") != "OK" or not data.get("predictions"):
                return None
            place_id = data["predictions"][0]["place_id"]

        url_details = "https://maps.googleapis.com/maps/api/place/details/json"
        params = {
            "place_id": place_id,
            "fields": "name,address_components",
            "language": "uk",
            "key": GOOGLE_API_KEY,
        }
        async with session.get(url_details, params=params) as resp:
            detail_data = await resp.json()
            if detail_data.get("status") != "OK":
                return None

            address_components = detail_data["result"].get("address_components", [])
            for comp in address_components:
                if "country" in comp.get("types", []):
                    country_code = comp.get("short_name")
                    break
            else:
                return None

            if country_code not in ALLOWED_COUNTRIES:
                return None

            return detail_data["result"]["name"]