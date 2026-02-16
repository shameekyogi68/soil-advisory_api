import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.api_logic import process_request

# Diverse Real World Scenarios
scenarios = [
    {
        "name": "COASTAL STRIP (Malpe, Udupi)",
        "desc": "Expected: Sandy Texture, Neutral pH (Sea Proximity)",
        "payload": {
            "lat": 13.3525, "lon": 74.6943,
            "crop": "Coconut", "sowing_date": "2026-06-15",
            "area_acres": 1.0
        },
        "expected": {"texture": "Sandy", "k": "Low", "taluk": "Udupi", "taluk_alt": "Brahmavar"}
    },
    {
        "name": "MIDLAND PLAINS (Brahmavar)",
        "desc": "Expected: Sandy Clay Loam, Low Potassium",
        "payload": {
            "lat": 13.4105, "lon": 74.7460,
            "crop": "Paddy", "sowing_date": "2026-06-15",
            "area_acres": 2.0
        },
        "expected": {"texture": "Sandy Clay Loam", "k": "Low", "taluk": "Brahmavar"}
    },
    {
        "name": "INTERIOR HIGHLAND (Hebri)",
        "desc": "Expected: Clay Loam, Medium K, Low P",
        "payload": {
            "lat": 13.4593, "lon": 74.9868,
            "crop": "Arecanut", "sowing_date": "2026-06-15",
            "area_acres": 5.0
        },
        "expected": {"texture": "Clay Loam", "k": "Medium", "taluk": "Hebri"}
    },
    {
        "name": "NORTH COASTAL (Maravanthe, Byndoor)",
        "desc": "Expected: Sandy (Strip), Low K (Deficient)",
        "payload": {
            "lat": 13.6967, "lon": 74.6464,
            "crop": "Coconut", "sowing_date": "2026-06-15",
            "area_acres": 1.5
        },
        "expected": {"texture": "Sandy", "k": "Low", "taluk": "Byndoor"}
    }
]

print("🌍 RUNNING COMPREHENSIVE GEOGRAPHIC VERIFICATION")
print("=" * 60)

for sc in scenarios:
    print(f"\n📍 Location: {sc['name']}")
    print(f"   Coords: {sc['payload']['lat']}, {sc['payload']['lon']}")
    print(f"   Context: {sc['desc']}")
    
    try:
        response = process_request(sc['payload'])
        
        prof = response['meta']['soil_profile']
        adv = response['advisory']
        
        # Validation Logic
        actual_tex = prof['type']['en']
        actual_tex_clean = actual_tex.lower().replace("_", " ")
        expected_tex_clean = sc['expected']['texture'].lower().replace("_", " ")
        
        actual_k = prof['potassium']['en']
        actual_taluk = response['meta']['region']
        
        print(f"   👉 Output: Texture='{actual_tex}', K='{actual_k}', Taluk='{actual_taluk}'")
        
        # Simple Check
        match_tex = (expected_tex_clean in actual_tex_clean)
        match_k = (sc['expected']['k'].lower() == actual_k.lower())
        
        # Allow adjacent taluk overlap for border cases (e.g. Malpe)
        match_taluk = True
        if 'taluk_alt' in sc['expected']:
             match_taluk = (actual_taluk == sc['expected']['taluk'] or actual_taluk == sc['expected']['taluk_alt'])
        
        if match_tex and match_k and match_taluk:
            print("   ✅ VERIFIED: Matches Geographical Expectations.")
        else:
            print(f"   ❌ MISMATCH: Expected {sc['expected']}, Got {actual_tex}, {actual_k}, {actual_taluk}")
            
        # Fertilizer Check (Quick Glance)
        mop = next((i for i in adv['shopping_list'] if "Potash" in i['name']['en']), None)
        if mop:
            print(f"   💊 Fertilizer: {mop['qty_display']['en']} MOP")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        
    print("-" * 60)
