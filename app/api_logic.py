import json
from datetime import datetime
from typing import Dict, Any, Union, List

# Imports from Core Modules
from app.core.gps_resolver import GPSResolver
from app.core.stcr_fertilizer import calculate_fertilizer
from app.core.lime_calculator import calculate_lime
from app.core.farmer_view import simplify_advisory

# Initialize Resolver (relies on default path logic in GPSResolver)
resolver = GPSResolver()

def generate_physical_advice(profile: Dict) -> Dict:
    """
    Generates advice on Moisture, Drainage, and Erosion based on soil physics.
    """
    texture = profile.get("texture", "lateritic")
    topo = profile.get("topography", "Upland")
    depth = profile.get("depth_class", "0-25")
    
    advice = {
        "moisture": "Moderate retention.",
        "drainage": "Well drained.",
        "erosion": "Low risk.",
        "suitability": "Suitable for most crops."
    }
    
    # 1. Texture Rules
    if texture == "sandy":
        advice["moisture"] = "⚠️ Low water holding. Irrigate frequently."
        advice["drainage"] = "Excessive drainage. Nutrients leach easily."
    elif texture == "clay_loam":
        advice["moisture"] = "✅ High water retention."
        advice["drainage"] = "⚠️ Slow drainage. Risk of waterlogging."
    
    # 2. Topography Rules
    if topo == "Upland":
        advice["erosion"] = "⚠️ High erosion risk. Use contour bunds/vegetative barriers."
    elif topo == "Lowland":
        advice["drainage"] = "⚠️ Risk of water stagnation. Ensure drainage channels."
        advice["erosion"] = "Low risk (Deposition zone)."
        
    return advice

def generate_crop_suitability(profile: Dict, current_crop: str) -> Dict:
    """
    Evaluates if the soil is suitable for the current crop.
    """
    texture = profile.get("texture", "lateritic")
    drainage = "poor" if texture == "clay_loam" else "good"
    
    score = "High"
    warnings = []
    
    # Paddle Rule
    if current_crop.lower() == "paddy":
        if texture == "sandy":
            score = "Medium"
            warnings.append("⚠️ Sandy soil loses water fast. Puddling is difficult.")
        elif texture == "clay_loam":
            score = "Excellent"
            
    # Arecanut/Coconut Rule
    elif current_crop.lower() in ["arecanut", "coconut"]:
        if drainage == "poor":
            score = "Low"
            warnings.append("⚠️ Risk of root rot due to poor drainage.")
            
    return {
        "score": score,
        "warnings": warnings
    }

def generate_management_tips(sowing_date: str) -> List[str]:
    """
    Generates seasonal soil management tips.
    """
    # Simply heuristic: If sowing date is close, give pre-sowing tips
    tips = [
        "🚜 Pre-Sowing: Plough 15cm deep to break hard pans.",
        "🌿 Organic: Apply Green Manure (Daincha) 2 weeks before planting.",
        "💧 Post-Harvest: Retain stubble to improve soil carbon."
    ]
    return tips

def _get_status(val: Any, nutrient: str) -> str:
    # Simple helper to convert numeric to low/medium/high
    try:
        val = float(val)
    except (ValueError, TypeError):
        return "medium" # Default fallback
        
    # Thresholds adapted from STCR standards
    if nutrient == "n":
        return "low" if val < 280 else "high" if val > 560 else "medium"
    elif nutrient == "p":
        return "low" if val < 22 else "high" if val > 55 else "medium"
    elif nutrient == "k":
        return "low" if val < 140 else "high" if val > 330 else "medium"
    return "medium"

def process_request(request_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main Entry Point for Flutter App.
    Accepts JSON input, returns JSON advisory.
    """
    
    # 1. Parse Inputs
    crop = request_json.get("crop", "Paddy")
    sowing_date = request_json.get("sowing_date", datetime.now().strftime("%Y-%m-%d"))
    lat = request_json.get("lat")
    lon = request_json.get("lon")
    
    # 2. Determine Data Source (Lab vs GPS)
    used_gps_mode = False
    
    if "ph" in request_json and "nitrogen_kg_ha" in request_json:
        # A. PRECISION MODE (Lab Data)
        try:
            ph = float(request_json["ph"])
            n_status = _get_status(request_json["nitrogen_kg_ha"], "n")
            p_status = _get_status(request_json["phosphorus_kg_ha"], "p")
            k_status = _get_status(request_json["potassium_kg_ha"], "k")
            soil_type = request_json.get("texture", "lateritic")
            zinc_val = float(request_json.get("zinc_ppm", 0.5))
            
            # Micros for Lab Mode (Defaults if not provided)
            fe_status = "Sufficient" 
            mn_status = "Sufficient"
            b_status = "Unknown"
            s_status = "Unknown"
            
        except (ValueError, TypeError):
             return {"error": "Invalid numeric values in Soil Data"}
    
    elif lat is not None and lon is not None:
        # B. GPS MODE (Zonal Average)
        used_gps_mode = True
        try:
            lat = float(lat)
            lon = float(lon)
        except (ValueError, TypeError):
            return {"error": "Invalid Latitude/Longitude"}
            
        zinc_val = 0.5 
        
        land_type_input = request_json.get("land_type")
        profile = resolver.get_profile(lat, lon, land_type_override=land_type_input)
        
        ph = 5.5 if profile["ph_class"] == "acidic" else 6.5
        n_status = profile["n"]
        p_status = profile["p"]
        k_status = profile["k"]
        soil_type = profile["texture"]
        
        # Micro-Nutient Heuristics
        fe_status = "Sufficient"
        mn_status = "Sufficient"
        b_status = "Deficient" if crop.lower() in ["arecanut", "coconut"] else "Sufficient"
        s_status = "Deficient" if soil_type == "sandy" else "Sufficient"
            
    else:
        return {"error": "Missing Soil Data or GPS Coordinates"}

    # 3. Run Scientific Models
    
    # Lime
    lime_result = calculate_lime(ph, 6.0, soil_type)
    lime_t_ha = lime_result.lime_required_t_ha 
    
    # NPK (STCR)
    target_yield = 5.0 if crop.lower() == "paddy" else 2.5
    
    stcr_result = calculate_fertilizer(
        crop=crop,
        target_yield=target_yield,
        soil_n=n_status,
        soil_p=p_status,
        soil_k=k_status,
        soil_type=soil_type
    )
    
    # 4. Generate Farmer Advisory
    try:
        manure_loads = float(request_json.get("manure_loads", 0))
    except:
        manure_loads = 0
        
    manure_tons = manure_loads * 3 
    
    advisory = simplify_advisory(
        crop=crop,
        sowing_date_str=sowing_date,
        urea_kg=stcr_result.urea_kg,
        dap_kg=stcr_result.dap_kg,
        mop_kg=stcr_result.mop_kg,
        zinc_kg=25 if zinc_val < 0.6 else 0,
        lime_t_ha=lime_t_ha,
        splits=stcr_result.splits,
        raw_warnings=[f"GPS Mode: Used average data for {profile['taluk']}" if used_gps_mode else "Precise Lab Mode"],
        weather_forecast_mm=float(request_json.get("rain_forecast_mm", 0.0) or 0.0),
        manure_type=request_json.get("manure_type"),
        manure_tons=manure_tons
    )
    
    # 5. Helper Funcs
    physical_tips = generate_physical_advice(profile if used_gps_mode else request_json)
    suitability = generate_crop_suitability(profile if used_gps_mode else request_json, crop)
    mgmt_tips = generate_management_tips(sowing_date)
    
    # 6. Format Response
    
    response = {
        "status": "success",
        "meta": {
            "mode": "GPS Zone" if used_gps_mode else "Lab Report",
            "region": profile["taluk"] if used_gps_mode else "User Field",
            "zone": profile.get("zone", "Unknown") if used_gps_mode else "Field Specific",
            "topography": profile.get("topography", "Unknown") if used_gps_mode else "User Input",
            "crop": crop,
            "soil_profile": {
                "nitrogen": n_status,
                "phosphorus": p_status,
                "potassium": k_status,
                "zinc": "Deficient" if zinc_val < 0.6 else "Sufficient",
                "iron": fe_status,
                "boron": b_status,
                "sulphur": s_status,
                "ph_status": "acidic" if ph < 6.0 else "neutral",
                "ph_value": ph,
                "type": soil_type 
            }
        },
        "advisory": {
            "summary_card": [
                {"label": "Soil Health", "value": advisory.soil_health_card[0]},
                {"label": "Suitability", "value": suitability["score"]}
            ],
            "soil_health_checklist": {
                "moisture": physical_tips["moisture"],
                "drainage": physical_tips["drainage"],
                "erosion": physical_tips["erosion"],
                "crop_suitability": f"{suitability['score']} - {', '.join(suitability['warnings'])}" if suitability['warnings'] else f"{suitability['score']} for {crop}"
            },
            "management_tips": mgmt_tips,

            "shopping_list": [
                {
                    "name": item.product_local,
                    "qty_display": f"{item.bags} Bags + {item.loose_kg:.1f} kg" if item.bags > 0 else f"{item.loose_kg:.1f} kg (Loose)",
                    "bags": item.bags,
                    "loose_kg": item.loose_kg
                } for item in advisory.shopping_list
            ],
            "schedule": [
                {
                    "date": s.date_range,
                    "activity": s.stage_kannada,
                    "products": s.products
                } for s in advisory.schedule
            ],
            "substitutes": advisory.substitutes,
            "voice_script": advisory.voice_script,
            "alerts": advisory.simple_warnings,
            "savings_msg": advisory.manure_credit_msg
        }
    }
    
    return response

# Test
if __name__ == "__main__":
    test_payload = {
        "crop": "Paddy",
        "lat": 13.3409, 
        "lon": 74.7421, # Udupi
        "area_acres": 2.0,
        "manure_type": "fym",
        "manure_loads": 2
    }
    print(json.dumps(process_request(test_payload), indent=2, ensure_ascii=False))
