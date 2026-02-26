import json
from datetime import datetime
from typing import Any, Dict
from app.api_logic import process_request

def has_bilingual_leak(data: Any) -> bool:
    """
    Recursively checks if any dictionary contains both 'en' and 'kn' keys,
    which indicates a failure in localization flattening.
    """
    if isinstance(data, dict):
        if "en" in data and "kn" in data and len(data) == 2:
            return True
        return any(has_bilingual_leak(v) for v in data.values())
    elif isinstance(data, list):
        return any(has_bilingual_leak(item) for item in data)
    return False

def run_test_case(name: str, payload: Dict[str, Any]):
    print(f"\n--- Testing: {name} ({payload.get('language', 'default')}) ---")
    try:
        response = process_request(payload)
        
        # 1. Check for bilingual leaks
        if has_bilingual_leak(response):
            print("❌ FAIL: Bilingual leak detected in response!")
            # print(json.dumps(response, indent=2, ensure_ascii=False)) # Debug only
            return False
            
        # 2. Check for language consistency
        lang = payload.get("language", "en")
        
        # Spot check some known localized fields
        soil_profile = response.get("meta", {}).get("soil_profile", {})
        nitrogen = soil_profile.get("nitrogen")
        
        if lang == "kn":
            if nitrogen not in ["ಕಡಿಮೆ", "ಮಧ್ಯಮ", "ಹೆಚ್ಚು"]:
                 print(f"❌ FAIL: Expected Kannada nitrogen status, got '{nitrogen}'")
                 return False
            # Check a nested advisory field
            summary_label = response.get("advisory", {}).get("summary_card", [{}])[0].get("label")
            if summary_label != "ಮಣ್ಣಿನ ಆರೋಗ್ಯ":
                 print(f"❌ FAIL: Expected Kannada summary label, got '{summary_label}'")
                 return False
        else:
            if nitrogen not in ["Low", "Medium", "High"]:
                 print(f"❌ FAIL: Expected English nitrogen status, got '{nitrogen}'")
                 return False
            summary_label = response.get("advisory", {}).get("summary_card", [{}])[0].get("label")
            if summary_label != "Soil Health":
                 print(f"❌ FAIL: Expected English summary label, got '{summary_label}'")
                 return False

        print("✅ PASS: No leaks and strings localized correctly.")
        return True
    except Exception as e:
        print(f"❌ FAIL: Exception occurred: {str(e)}")
        return False

def validate_all():
    results = []
    
    # Define Scenarios
    scenarios = [
        {
            "name": "Coastal Pre-monsoon (High Salinity)",
            "base_payload": {
                "crop": "Paddy",
                "latitude": 13.62, # Kundapura
                "longitude": 74.69,
                "sowing_date": "2024-04-15"
            }
        },
        {
            "name": "Coastal Monsoon (Low Salinity)",
            "base_payload": {
                "crop": "Paddy",
                "latitude": 13.62,
                "longitude": 74.69,
                "sowing_date": "2024-07-15"
            }
        },
        {
            "name": "Inland Safety",
            "base_payload": {
                "crop": "Paddy",
                "latitude": 13.4593, # Hebri
                "longitude": 74.9868,
                "sowing_date": "2024-04-15"
            }
        },
        {
            "name": "Lab Mode (Precision)",
            "base_payload": {
                "crop": "Paddy",
                "ph": 5.5,
                "nitrogen_kg_ha": 300,
                "phosphorus_kg_ha": 30,
                "potassium_kg_ha": 200,
                "texture": "lateritic"
            }
        },
        {
            "name": "Manure Credit",
            "base_payload": {
                "crop": "Paddy",
                "latitude": 13.34,
                "longitude": 74.74,
                "manure_type": "fym",
                "manure_loads": 5
            }
        }
    ]
    
    for s in scenarios:
        for lang in ["en", "kn"]:
            payload = s["base_payload"].copy()
            payload["language"] = lang
            results.append(run_test_case(f"{s['name']}", payload))
            
    # Final Summary
    total = len(results)
    passed = sum(1 for r in results if r)
    print(f"\n==============================")
    print(f"VERIFICATION SUMMARY: {passed}/{total} Passed")
    print(f"==============================")
    
    if passed != total:
        exit(1)

if __name__ == "__main__":
    validate_all()
