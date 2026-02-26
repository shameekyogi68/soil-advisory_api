import sys
import os
import json

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.api_logic import process_request

def test_salinity():
    print("🌍 RUNNING SEASONAL SALINITY VERIFICATION")
    print("=========================================")

    # Case 1: Kundapura Coast on April 15 (Pre-Monsoon) -> HIGH SALINITY EXPECTED
    req_apr = {
        "crop": "Paddy",
        "lat": 13.6269, # Kundapura
        "lon": 74.6924, # Coastal
        "sowing_date": "2024-04-15", # Pre-Monsoon
        "area_acres": 1.0
    }
    
    print("\n📍 Case 1: Kundapura Coast (April 15 - Pre-Monsoon)")
    res_apr = process_request(req_apr)
    salinity_apr = res_apr["meta"]["soil_profile"].get("salinity", {}).get("en", "Unknown")
    alerts_apr = res_apr["advisory"]["alerts"]
    has_warning_apr = any("Salinity" in a.get("en", "") for a in alerts_apr)
    
    print(f"   👉 Salinity Status: {salinity_apr}")
    print(f"   👉 Warning Present: {has_warning_apr}")
    
    if salinity_apr == "High" and has_warning_apr:
        print("   ✅ PASS: High Salinity detected correctly.")
    else:
        print("   ❌ FAIL: Expected High Salinity.")

    # Case 2: Kundapura Coast on July 15 (Monsoon) -> NORMAL SALINITY EXPECTED
    req_jul = {
        "crop": "Paddy",
        "lat": 13.6269,
        "lon": 74.6924,
        "sowing_date": "2024-07-15", # Monsoon
        "area_acres": 1.0
    }
    
    print("\n📍 Case 2: Kundapura Coast (July 15 - Monsoon)")
    res_jul = process_request(req_jul)
    salinity_jul = res_jul["meta"]["soil_profile"].get("salinity", {}).get("en", "Unknown")
    
    print(f"   👉 Salinity Status: {salinity_jul}")
    
    if salinity_jul == "Normal":
        print("   ✅ PASS: Normal Salinity (washed out).")
    else:
        print("   ❌ FAIL: Expected Normal Salinity.")
        
    # Case 3: Hebri Inland on April 15 -> NORMAL SALINITY EXPECTED (No intrusion)
    req_heb = {
        "crop": "Paddy",
        "lat": 13.4593, # Hebri
        "lon": 74.9868, # Inland
        "sowing_date": "2024-04-15",
        "area_acres": 1.0
    }
    
    print("\n📍 Case 3: Hebri Inland (April 15 - Pre-Monsoon)")
    res_heb = process_request(req_heb)
    salinity_heb = res_heb["meta"]["soil_profile"].get("salinity", {}).get("en", "Unknown")
    
    print(f"   👉 Salinity Status: {salinity_heb}")
    
    if salinity_heb == "Normal":
        print("   ✅ PASS: Normal Salinity (Inland safe).")
    else:
        print("   ❌ FAIL: Expected Normal, got High.")

if __name__ == "__main__":
    test_salinity()
