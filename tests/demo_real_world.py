import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.api_logic import process_request

# Real World Scenario: Small Farmer in Brahmavara (Udupi)
# Crop: Paddy (Rice)
# Season: Kharif (Monsoon)
# Soil: Unknown (GPS Mode)
# Rain: 5.0mm forecast

payload = {
    "lat": 13.4105,  # Brahmavara, Udupi
    "lon": 74.7460,
    "crop": "Paddy",
    "sowing_date": "2026-06-15",
    "area_acres": 2.0,
    "rain_forecast_mm": 5.0
}

print(f"🌍 Simulating Real World Request for: Brahmavara, Udupi (Lat: {payload['lat']}, Lon: {payload['lon']})")
print(f"🌾 Crop: {payload['crop']}, Area: {payload['area_acres']} acres")
print("-" * 60)

try:
    response = process_request(payload)
    print(json.dumps(response, indent=2, ensure_ascii=False))
except Exception as e:
    print(f"❌ Error: {e}")
