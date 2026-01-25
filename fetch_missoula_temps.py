import requests
import pandas as pd

url = "https://archive-api.open-meteo.com/v1/archive"
params = {
    "latitude": 46.87,
    "longitude": -113.99,
    "start_date": "2025-01-01",
    "end_date": "2026-01-20",  # Set a few days back to ensure data availability
    "hourly": "temperature_2m",
    "temperature_unit": "fahrenheit",
    "timezone": "America/Denver"
}

print("Fetching data...")
response = requests.get(url, params=params)

if response.status_code == 200:
    data = response.json()

    if 'hourly' in data:
        hourly = data['hourly']
        df = pd.DataFrame({
            'Time': hourly['time'],
            'Temperature_F': hourly['temperature_2m']
        })

        filename = "missoula_temps_2025-2026.csv"
        df.to_csv(filename, index=False)
        print(f"Success! Data saved to '{filename}' with {len(df)} rows.")
    else:
        print(f"Unexpected response format: {data}")
else:
    print(f"Error: {response.status_code} - {response.text}")
