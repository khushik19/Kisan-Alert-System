"""
weather.py — Step 2: Weather fetch function
Fetches current weather for a given lat/lon via OpenWeatherMap API.
"""

import requests


def get_weather(lat: float, lon: float, api_key: str) -> dict:
    """
    Fetch current weather for the given coordinates.

    Returns:
        {
            "condition": "Rain",   # main weather condition
            "temp": 32.5,          # temperature in °C
            "humidity": 78         # humidity percentage
        }
    Raises:
        Exception if the API call fails or returns an error.
    """
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": api_key,
        "units": "metric"   # Celsius
    }

    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()

    return {
        "condition": data["weather"][0]["main"],        # e.g. "Rain", "Clear", "Clouds"
        "description": data["weather"][0]["description"], # e.g. "light rain"
        "temp": data["main"]["temp"],                   # °C
        "humidity": data["main"]["humidity"],            # %
        "city": data.get("name", "Unknown")             # city name for logging
    }


# --- Quick standalone test ---
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    load_dotenv()
    api_key = os.getenv("OPENWEATHER_API_KEY")
    lat = float(os.getenv("DEMO_LAT", 22.7196))
    lon = float(os.getenv("DEMO_LON", 75.8577))

    print(f"Fetching weather for Indore ({lat}, {lon})...")
    result = get_weather(lat, lon, api_key)
    print("Weather result:")
    for k, v in result.items():
        print(f"  {k}: {v}")
