import requests

def get_weather():
    # San Antonio Coordinates
    lat, lon = 29.4241, -98.4936
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,weather_code&daily=temperature_2m_max,temperature_2m_min&timezone=auto"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        # Current conditions
        curr_temp = round(data['current']['temperature_2m'])
        humidity = data['current']['relative_humidity_2m']
        
        # Daily High/Low
        high = round(data['daily']['temperature_2m_max'][0])
        low = round(data['daily']['temperature_2m_min'][0])
        
        # Simple Weather Code Mapping
        code = data['current']['weather_code']
        conditions = {
            0: "Clear Sky ☀️", 1: "Mainly Clear 🌤", 2: "Partly Cloudy ⛅", 3: "Overcast ☁️",
            45: "Foggy 🌫️", 48: "Rime Fog 🌫️", 51: "Light Drizzle 🌦️", 
            61: "Rain 🌧️", 71: "Snow ❄️", 80: "Rain Showers 🌦️", 95: "Thunderstorm ⛈️"
        }
        status = conditions.get(code, "Clear")

        report = [
            f"Currently: {curr_temp}°C - {status}",
            f"High: {high}°C | Low: {low}°C",
            f"Humidity: {humidity}%"
        ]
        
        return "\n".join([f"* {line}" for line in report])
        
    except Exception as e:
        return f"* Weather data unavailable ({e})"

def main():
    weather_info = get_weather()
    return f"### 🌤 Weather (San Antonio)\n{weather_info}"

if __name__ == "__main__":
    print(main())