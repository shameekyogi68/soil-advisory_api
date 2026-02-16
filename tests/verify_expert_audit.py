import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.api_logic import process_request

# Test Case: Farmer in Kundapura
# Expectation: Potassium should be "Low", Texture should be "Sandy Loam" (from previous fix), pH Acidic.
# Fertilizer recommendation should show higher Potash (MOP) than if it were Medium.

payload = {
    "lat": 13.6223,  # Kundapura Centroid
    "lon": 74.6868,
    "crop": "Paddy",
    "sowing_date": "2026-06-15",
    "area_acres": 1.0, 
    "rain_forecast_mm": 10.0
}

print(f"🌍 Verifying Expert Audit for: Kundapura (Lat: {payload['lat']}, Lon: {payload['lon']})")
print("-" * 60)

try:
    response = process_request(payload)
    
    # Extract key values for validation
    soil_profile = response["meta"]["soil_profile"]
    k_status = soil_profile["potassium"]["en"]
    texture = soil_profile["type"]["en"]
    
    print(f"Soil Profile Detected:")
    print(f"  - Potassium: {k_status} (Expected: Low)")
    print(f"  - Texture:   {texture} (Expected: Sandy or Sandy Loam)")
    
    # Check Shopping List for MOP
    mop_item = next((item for item in response["advisory"]["shopping_list"] if "Potash" in item["name"]["en"]), None)
    if mop_item:
        print(f"Fertilizer Recommendation:")
        print(f"  - MOP (Potash): {mop_item['qty_display']['en']}")
    
    if k_status == "Low":
        print("\n✅ VERIFICATION PASSED: Potassium is LOW as per Expert Audit.")
    else:
        print(f"\n❌ VERIFICATION FAILED: Potassium is {k_status}, expected LOW.")
        
except Exception as e:
    print(f"❌ Error: {e}")
