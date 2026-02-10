import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # Add root to path

from app.api_logic import process_request

TEST_CASES = [
    {
        "name": "Coastal Lowland (Swarna River)",
        "input": {"lat": 13.37, "lon": 74.745, "crop": "Paddy", "sowing_date": "2026-06-01"},
        "expected": {"zone": "coastal", "topography": "Lowland", "type": "sandy", "ph_status": "neutral"}
    },
    {
        "name": "Coastal Upland (Beachside)",
        "input": {"lat": 13.35, "lon": 74.70, "crop": "Coconut", "sowing_date": "2026-06-01"},
        "expected": {"zone": "coastal", "topography": "Upland", "type": "sandy", "ph_status": "neutral"}
    },
    {
        "name": "Midland Lowland (Swarna River)",
        "input": {"lat": 13.36, "lon": 74.78, "crop": "Arecanut", "sowing_date": "2026-06-01"},
        "expected": {"zone": "midland", "topography": "Lowland", "type": "clay_loam", "n": "medium"}  # Lateritic -> Clay Loam
    },
    {
        "name": "Midland Upland (Rocky)",
        "input": {"lat": 13.55, "lon": 74.85, "crop": "Paddy", "sowing_date": "2026-06-01"},
        "expected": {"zone": "midland", "topography": "Upland", "type": "lateritic", "ph_status": "acidic"}
    },
    {
        "name": "Ghats Forest (Hebri)",
        "input": {"lat": 13.45, "lon": 75.05, "crop": "Paddy", "sowing_date": "2026-06-01"},
        "expected": {"zone": "ghats", "topography": "Upland", "type": "clay_loam", "ph_status": "acidic"}
    }
]

print(f"{'TEST CASE':<30} | {'ZONE':<10} | {'TOPO':<10} | {'SOIL':<10} | {'pH':<8} | {'STATUS':<10}")
print("-" * 90)

for test in TEST_CASES:
    res = process_request(test["input"])
    meta = res["meta"]
    profile = meta["soil_profile"]
    
    # Check Expectations
    exp = test["expected"]
    passed = True
    
    if meta["zone"] != exp["zone"]: passed = False
    if meta["topography"] != exp["topography"]: passed = False
    if profile["type"] != exp["type"]: passed = False
    if "ph_status" in exp and profile["ph_status"] != exp["ph_status"]: passed = False
    
    status_icon = "✅ PASS" if passed else "❌ FAIL"
    
    print(f"{test['name']:<30} | {meta['zone']:<10} | {meta['topography']:<10} | {profile['type']:<10} | {profile['ph_status']:<8} | {status_icon}")
    
    if not passed:
        print(f"   🔴 Got: Zone={meta['zone']}, Topo={meta['topography']}, Type={profile['type']}, pH={profile['ph_status']}")
        print(f"   🟢 Exp: {json.dumps(exp)}")

print("-" * 90)
print("Validation Complete.")
