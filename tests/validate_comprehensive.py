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
        "expected": {"zone": "midland", "topography": "Lowland", "type": "clay loam", "n": "medium"}  # Display name
    },
    {
        "name": "Midland Upland (Rocky)",
        "input": {"lat": 13.55, "lon": 74.85, "crop": "Paddy", "sowing_date": "2026-06-01"},
        "expected": {"zone": "midland", "topography": "Upland", "type": "lateritic", "ph_status": "acidic"}
    },
    {
        "name": "Ghats Forest (Hebri)",
        "input": {"lat": 13.45, "lon": 75.05, "crop": "Paddy", "sowing_date": "2026-06-01"},
        "expected": {"zone": "ghats", "topography": "Upland", "type": "clay loam", "ph_status": "acidic"}
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
    
    # Helper to get EN value safely
    def get_en(val):
        if isinstance(val, dict): return val.get("en", "").lower()
        return str(val).lower()
    
    zone_val = res["meta"]["zone"] 
    topo_val = res["meta"]["topography"] 
    
    type_val = get_en(profile["type"])
    ph_val = get_en(profile["ph_status"])
    
    # New Field Checks (REMOVED)
    adv = res["advisory"]
    # has_quick = "quick_decisions" in adv
    # has_water = "water_insights" in adv
    # has_crop = "crop_advice" in adv
    
    # Check for Checklist
    has_checklist = "soil_health_checklist" in adv
    if not has_checklist:
        passed = False
        print(f"   🔴 Missing Checklist")

    if zone_val != exp["zone"]: 
        passed = False
        print(f"   🔴 Zone Mismatch: Got {zone_val}, Exp {exp['zone']}")
        
    if topo_val != exp["topography"]: 
        passed = False
        print(f"   🔴 Topo Mismatch: Got {topo_val}, Exp {exp['topography']}")
        
    if type_val != exp["type"].lower(): 
        passed = False
        print(f"   🔴 Type Mismatch: Got {type_val}, Exp {exp['type']}")
        
    if "ph_status" in exp:
        if ph_val != exp["ph_status"].lower(): 
            passed = False
            print(f"   🔴 pH Mismatch: Got {ph_val}, Exp {exp['ph_status']}")
            
    status_icon = "✅ PASS" if passed else "❌ FAIL"
    
    print(f"{test['name']:<30} | {zone_val:<10} | {topo_val:<10} | {type_val:<10} | {ph_val:<8} | {status_icon}")
print("-" * 90)
print("Validation Complete.")
