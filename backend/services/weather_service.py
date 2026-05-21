import requests
from utils.config import config
from utils.logger import logger
from typing import Dict, Any
from datetime import datetime, timedelta

class WeatherService:
    def __init__(self, api_key: str = config.WEATHER_API_KEY):
        self.api_key = api_key

    def get_weather_data(self, city: str) -> Dict[str, Any]:
        """
        Fetches current weather, 5-day forecast, and air quality index (AQI).
        Combines them into a unified, rich weather report.
        """
        city_clean = city.strip()
        logger.info(f"Fetching weather data for city: {city_clean}")
        
        # Check if api key is missing or dummy
        if not self.api_key or self.api_key == "your_openweathermap_api_key_here":
            logger.warning("Weather API key not configured, returning mock data.")
            return self._generate_mock_weather_data(city_clean)

        try:
            # 1. Current Weather
            curr_url = "http://api.openweathermap.org/data/2.5/weather"
            curr_params = {"q": city_clean, "appid": self.api_key, "units": "metric"}
            curr_resp = requests.get(curr_url, params=curr_params, timeout=5)
            
            if curr_resp.status_code == 404:
                return {"error": "City not found", "city": city_clean}
                
            curr_resp.raise_for_status()
            curr_data = curr_resp.json()
            
            lat = curr_data["coord"]["lat"]
            lon = curr_data["coord"]["lon"]
            city_name = curr_data["name"]
            country = curr_data["sys"]["country"]

            # 2. Air Pollution (AQI)
            aqi = 1  # Default Good
            try:
                poll_url = "http://api.openweathermap.org/data/2.5/air_pollution"
                poll_params = {"lat": lat, "lon": lon, "appid": self.api_key}
                poll_resp = requests.get(poll_url, params=poll_params, timeout=5)
                poll_resp.raise_for_status()
                poll_data = poll_resp.json()
                aqi = poll_data["list"][0]["main"]["aqi"]
            except Exception as e:
                logger.error(f"Error fetching air quality: {e}")

            # 3. 5-Day Forecast
            forecast_list = []
            try:
                fore_url = "http://api.openweathermap.org/data/2.5/forecast"
                fore_params = {"q": city_clean, "appid": self.api_key, "units": "metric"}
                fore_resp = requests.get(fore_url, params=fore_params, timeout=5)
                fore_resp.raise_for_status()
                fore_data = fore_resp.json()
                
                # Format forecast entries
                for entry in fore_data["list"]:
                    forecast_list.append({
                        "timestamp": entry["dt"],
                        "datetime_str": entry["dt_txt"],
                        "temperature": round(entry["main"]["temp"]),
                        "feels_like": round(entry["main"]["feels_like"]),
                        "humidity": entry["main"]["humidity"],
                        "description": entry["weather"][0]["description"],
                        "icon": entry["weather"][0]["icon"],
                        "wind_speed": entry["wind"]["speed"],
                        "rain_prob": entry.get("pop", 0) * 100
                    })
            except Exception as e:
                logger.error(f"Error fetching forecast: {e}")

            # Assemble clean output
            report = {
                "city": city_name,
                "country": country,
                "coords": {"lat": lat, "lon": lon},
                "current": {
                    "temperature": round(curr_data["main"]["temp"]),
                    "feels_like": round(curr_data["main"]["feels_like"]),
                    "humidity": curr_data["main"]["humidity"],
                    "pressure": curr_data["main"]["pressure"],
                    "wind_speed": curr_data["wind"]["speed"],
                    "description": curr_data["weather"][0]["description"],
                    "icon": curr_data["weather"][0]["icon"],
                    "clouds": curr_data["clouds"]["all"]
                },
                "aqi": aqi,
                "forecast": forecast_list,
                "source": "api"
            }
            
            return report

        except Exception as e:
            logger.error(f"Failed to fetch weather data for {city_clean}: {e}. Returning mock fallback.")
            return self._generate_mock_weather_data(city_clean)

    def _generate_mock_weather_data(self, city: str) -> Dict[str, Any]:
        """Generates realistic mock weather data if API fails or isn't configured."""
        city_name = city.strip().title()
        
        # Hardcode some nice defaults based on city
        temp_base = 28
        description = "partly cloudy"
        humidity = 60
        aqi = 2  # Fair
        rain_prob = 10
        
        # Tailor specific cities
        if "goa" in city_name.lower():
            temp_base = 31
            description = "scattered clouds"
            humidity = 78
            aqi = 1
        elif "pune" in city_name.lower():
            temp_base = 29
            description = "clear sky"
            humidity = 45
            aqi = 3
        elif "mumbai" in city_name.lower():
            temp_base = 32
            description = "haze"
            humidity = 80
            aqi = 4
        elif "delhi" in city_name.lower():
            temp_base = 38
            description = "smoke"
            humidity = 30
            aqi = 5
        elif "leh" in city_name.lower() or "trek" in city_name.lower():
            temp_base = 12
            description = "clear sky"
            humidity = 20
            aqi = 1
        
        # Build 5-day mock forecast
        forecast = []
        start_time = datetime.now()
        
        for i in range(12):  # Next 36 hours (every 3 hours)
            entry_time = start_time + timedelta(hours=i*3)
            hour = entry_time.hour
            temp_var = 4 * (1 if 10 <= hour <= 18 else -1)
            temp = temp_base + temp_var + (i % 3 - 1)
            
            desc = description
            if i % 4 == 2:
                desc = "light rain" if humidity > 70 else "broken clouds"
            
            forecast.append({
                "timestamp": int(entry_time.timestamp()),
                "datetime_str": entry_time.strftime("%Y-%m-%d %H:%M:%S"),
                "temperature": round(temp),
                "feels_like": round(temp + 1),
                "humidity": min(95, max(15, humidity + (i % 5 - 2))),
                "description": desc,
                "icon": "04d" if "cloud" in desc else "01d" if "clear" in desc else "10d" if "rain" in desc else "50d",
                "wind_speed": round(3.5 + (i % 4) * 0.8, 1),
                "rain_prob": 70 if "rain" in desc else rain_prob
            })

        return {
            "city": city_name,
            "country": "IN",
            "coords": {"lat": 18.52, "lon": 73.85},
            "current": {
                "temperature": temp_base,
                "feels_like": temp_base + 2,
                "humidity": humidity,
                "pressure": 1010,
                "wind_speed": 4.2,
                "description": description,
                "icon": "04d" if "cloud" in description else "01d" if "clear" in description else "10d" if "rain" in description else "50d",
                "clouds": 40
            },
            "aqi": aqi,
            "forecast": forecast,
            "source": "mock"
        }

weather_service = WeatherService()
