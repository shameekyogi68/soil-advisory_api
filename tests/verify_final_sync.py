import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.gps_resolver import GPSResolver

def verify_sync():
    resolver = GPSResolver()
    
    # Expected values from Strategic Report
    expectations = {
        "Kapu": {"p": "high", "k": "low", "texture": "sandy_clay_loam"},
        "Hebri": {"p": "low", "k": "medium", "texture": "clay_loam", "sh_ph": "slightly_acidic"}, # sh_ph = check json directly if possible, or infer from ph_class override
        "Byndoor": {"k": "low", "texture": "lateritic"},
        "Brahmavar": {"k": "low"}
    }
    
    print("🔎 Final Data Synchronization Check")
    print("-" * 50)
    
    all_pass = True
    
    # We will check the loaded profiles directly from the resolver's memory
    profiles = resolver.profiles
    
    for taluk, rules in expectations.items():
        data = profiles.get(taluk)
        if not data:
            print(f"❌ {taluk}: Profile NOT FOUND")
            all_pass = False
            continue
            
        print(f"Checking {taluk}...")
        
        # Check P
        if "p" in rules:
            actual = data.get("phosphorus_class")
            if actual != rules["p"]:
                print(f"  ❌ Phosphorus Mismatch! Expected: {rules['p']}, Got: {actual}")
                all_pass = False
            else:
                print(f"  ✅ Phosphorus: {actual}")
                
        # Check K
        if "k" in rules:
            actual = data.get("potassium_class")
            if actual != rules["k"]:
                print(f"  ❌ Potassium Mismatch! Expected: {rules['k']}, Got: {actual}")
                all_pass = False
            else:
                print(f"  ✅ Potassium: {actual}")
                
        # Check Texture
        if "texture" in rules:
            actual = data.get("soil_texture_class")
            if actual != rules["texture"]:
                print(f"  ❌ Texture Mismatch! Expected: {rules['texture']}, Got: {actual}")
                all_pass = False
            else:
                print(f"  ✅ Texture: {actual}")
                
    if all_pass:
        print("-" * 50)
        print("✅ SUCCESS: All profiles match the Strategic Report.")
    else:
        print("-" * 50)
        print("❌ FAILURE: Discrepancies found.")

if __name__ == "__main__":
    verify_sync()
