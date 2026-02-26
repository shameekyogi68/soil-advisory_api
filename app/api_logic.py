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

def flatten_localization(data: Any, lang: str = "en") -> Any:
    """
    Recursively flattens dictionaries containing 'en' and 'kn' keys 
    to return only the string for the requested language.
    """
    if isinstance(data, dict):
        # If it's a localization object, return the specific language
        if "en" in data and "kn" in data and len(data) == 2:
            return data.get(lang, data.get("en"))
        # Otherwise, recurse into dictionary values
        return {k: flatten_localization(v, lang) for k, v in data.items()}
    elif isinstance(data, list):
        # Recurse into list elements
        return [flatten_localization(item, lang) for item in data]
    return data


def generate_physical_advice(profile: Dict) -> Dict:
    """
    Generates advice on Moisture, Drainage, and Erosion based on soil physics.
    """
    texture = profile.get("texture", "lateritic")
    topo = profile.get("topography", "Upland")
    
    advice = {
        "moisture": {"en": "Moderate retention.", "kn": "ಮಧ್ಯಮ ತೇವಾಂಶ ಧಾರಣ."},
        "drainage": {"en": "Well drained.", "kn": "ಉತ್ತಮ ಬಸಿಯುವಿಕೆ."},
        "erosion": {"en": "Low risk.", "kn": "ಕಡಿಮೆ ಸವೆತ."},
        "suitability": {"en": "Suitable for most crops.", "kn": "ಹೆಚ್ಚಿನ ಬೆಳೆಗಳಿಗೆ ಸೂಕ್ತ."}
    }
    
    # 1. Texture Rules
    if texture == "sandy":
        advice["moisture"] = {"en": "⚠️ Low water holding. Irrigate frequently.", "kn": "⚠️ ಕಡಿಮೆ ತೇವಾಂಶ. ಆಗಾಗ್ಗೆ ನೀರು ಹಾಯಿಸಿ."}
        advice["drainage"] = {"en": "Excessive drainage. Nutrients leach easily.", "kn": "ಅತಿಯಾದ ಬಸಿಯುವಿಕೆ. ಪೋಷಕಾಂಶ ನಷ್ಟವಾಗಬಹುದು."}
    elif texture == "clay_loam":
        advice["moisture"] = {"en": "✅ High water retention.", "kn": "✅ ಉತ್ತಮ ತೇವಾಂಶ ಧಾರಣ."}
        advice["drainage"] = {"en": "⚠️ Slow drainage. Risk of waterlogging.", "kn": "⚠️ ನಿಧಾನ ಬಸಿಯುವಿಕೆ. ನೀರು ನಿಲ್ಲುವ ಸಾಧ್ಯತೆ."}
    
    # 2. Topography Rules
    if topo == "Upland":
        advice["erosion"] = {"en": "⚠️ High erosion risk. Use contour bunds.", "kn": "⚠️ ಮಣ್ಣು ಸವೆತದ ಅಪಾಯ. ಬದುಗಳನ್ನು ನಿರ್ಮಿಸಿ."}
    elif topo == "Lowland":
        advice["drainage"] = {"en": "⚠️ Risk of water stagnation. Ensure drainage.", "kn": "⚠️ ನೀರು ನಿಲ್ಲುವ ಅಪಾಯ. ಬಸಿಯುವಿಕೆ ವ್ಯವಸ್ಥೆ ಮಾಡಿ."}
        advice["erosion"] = {"en": "Low risk (Deposition zone).", "kn": "ಕಡಿಮೆ ಸವೆತ."}
        
    return advice

def generate_crop_suitability(profile: Dict, current_crop: str) -> Dict:
    """
    Evaluates if the soil is suitable for the current crop.
    """
    texture = profile.get("texture", "lateritic")
    drainage = "poor" if texture == "clay_loam" else "good"
    
    score = {"en": "High", "kn": "ಉತ್ತಮ"}
    warnings = []
    
    # Paddle Rule
    if current_crop.lower() == "paddy":
        if texture == "sandy":
            score = {"en": "Medium", "kn": "ಮಧ್ಯಮ"}
            warnings.append({"en": "⚠️ Sandy soil loses water fast.", "kn": "⚠️ ಮರಳು ಮಿಶ್ರಿತ ಮಣ್ಣಿನಲ್ಲಿ ನೀರು ನಿಲ್ಲುವುದಿಲ್ಲ."})
        elif texture == "clay_loam":
            score = {"en": "Excellent", "kn": "ಅತ್ಯುತ್ತಮ"}
            
    # Arecanut/Coconut Rule
    elif current_crop.lower() in ["arecanut", "coconut"]:
        if drainage == "poor":
            score = {"en": "Low", "kn": "ಕಡಿಮೆ"}
            warnings.append({"en": "⚠️ Risk of root rot due to poor drainage.", "kn": "⚠️ ನೀರು ನಿಲ್ಲುವುದರಿಂದ ಬೇರು ಕೊಳೆ ರೋಗದ ಅಪಾಯ."})
            
    return {
        "score": score,
        "warnings": warnings
    }

def generate_management_tips(sowing_date: str) -> List[Dict[str, str]]:
    """
    Generates seasonal soil management tips.
    """
    return [
        {
            "en": "🚜 Pre-Sowing: Plough 15cm deep to break hard pans.",
            "kn": "🚜 ಬಿತ್ತನೆಗೆ ಮುನ್ನ: ಗಟ್ಟಿಯಾದ ಮಣ್ಣನ್ನು ಒಡೆಯಲು 15 ಸೆಂ.ಮೀ ಆಳವಾಗಿ ಉಳಿಮೆ ಮಾಡಿ."
        },
        {
            "en": "🌿 Organic: Apply Green Manure (Daincha) 2 weeks before planting.",
            "kn": "🌿 ಸಾವಯವ: ಬಿತ್ತನೆಗೆ 2 ವಾರಗಳ ಮೊದಲು ಹಸಿರೆಲೆ ಗೊಬ್ಬರ ಹಾಕಿ."
        },
        {
            "en": "💧 Post-Harvest: Retain stubble to improve soil carbon.",
            "kn": "💧 ಕಟಾವಿನ ನಂತರ: ಮಣ್ಣಿನ ಇಂಗಾಲ ಹೆಚ್ಚಿಸಲು ಕೂಳೆಗಳನ್ನು ಉಳಿಸಿ."
        }
    ]

def _get_status(val: Any, nutrient: str) -> str:
    # Helper remains same, output is localized in process_request
    try:
        val = float(val)
    except (ValueError, TypeError):
        return "medium"
        
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
    language = request_json.get("language", "en").lower()
    if language not in ["en", "kn"]:
        language = "en"
        
    lat = request_json.get("lat") or request_json.get("latitude")
    lon = request_json.get("lon") or request_json.get("longitude")
    
    # 2. Determine Data Source
    used_gps_mode = False
    
    if "ph" in request_json and "nitrogen_kg_ha" in request_json:
        # A. PRECISION MODE
        try:
            ph = float(request_json["ph"])
            n_status = _get_status(request_json["nitrogen_kg_ha"], "n")
            p_status = _get_status(request_json["phosphorus_kg_ha"], "p")
            k_status = _get_status(request_json["potassium_kg_ha"], "k")
            soil_type = request_json.get("texture", "lateritic")
            zinc_val = float(request_json.get("zinc_ppm", 0.5))
            
            fe_status = "Sufficient" 
            mn_status = "Sufficient"
            b_status = "Unknown"
            s_status = "Unknown"
            
            profile = {"taluk": "Lab", "zone": "User", "topography": "User"} # Dummy for logic
            
        except (ValueError, TypeError):
             return {"error": "Invalid numeric values in Soil Data"}
    
    elif lat is not None and lon is not None:
        # B. GPS MODE
        used_gps_mode = True
        try:
            lat = float(lat)
            lon = float(lon)
        except (ValueError, TypeError):
            return {"error": "Invalid Latitude/Longitude"}
            
        zinc_val = 0.5 
        
        land_type_input = request_json.get("land_type")
        
        # Extract month for seasonal logic
        try:
            sow_dt = datetime.strptime(sowing_date, "%Y-%m-%d")
            sow_month = sow_dt.month
        except:
            sow_month = datetime.now().month

        profile = resolver.get_profile(lat, lon, land_type_override=land_type_input, month=sow_month)
        
        ph = 5.5 if profile["ph_class"] == "acidic" else 6.5
        # If alkaline due to salinity
        if profile.get("ph_class") == "alkaline":
            ph = 7.5
            
        n_status = profile["n"]
        p_status = profile["p"]
        k_status = profile["k"]
        soil_type = profile["texture"]
        salinity = profile.get("salinity", "Normal")
        
        fe_status = "Sufficient"
        mn_status = "Sufficient"
        b_status = "Deficient" if crop.lower() in ["arecanut", "coconut"] else "Sufficient"
        s_status = "Deficient" if soil_type == "sandy" else "Sufficient"
            
    else:
        return {"error": "Missing Soil Data or GPS Coordinates"}

    # 3. Run Scientific Models
    lime_result = calculate_lime(ph, 6.0, soil_type)
    lime_t_ha = lime_result.lime_required_t_ha 
    
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
        raw_warnings=[f"GPS Mode used for {profile['taluk']}" if used_gps_mode else "Lab Mode"],
        weather_forecast_mm=float(request_json.get("rain_forecast_mm", 0.0) or 0.0),
        manure_type=request_json.get("manure_type"),
        manure_tons=manure_tons
    )
    
    # 5. Helper Funcs
    physical_tips = generate_physical_advice(profile if used_gps_mode else request_json)
    suitability = generate_crop_suitability(profile if used_gps_mode else request_json, crop)
    mgmt_tips = generate_management_tips(sowing_date)
    
    # 6. Format Response
    
    # Translation Helpers
    def localize(val: str) -> Dict[str, str]:
        # Simple mapping for status values
        mappings = {
            "low": {"en": "Low", "kn": "ಕಡಿಮೆ"},
            "medium": {"en": "Medium", "kn": "ಮಧ್ಯಮ"},
            "high": {"en": "High", "kn": "ಹೆಚ್ಚು"},
            "acidic": {"en": "Acidic", "kn": "ಆಮ್ಲೀಯ"},
            "neutral": {"en": "Neutral", "kn": "ತಟಸ್ಥ"},
            "alkaline": {"en": "Alkaline", "kn": "ಕ್ಷಾರೀಯ"},
            "sandy": {"en": "Sandy", "kn": "ಮರಳು ಮಿಶ್ರಿತ"},
            "clay_loam": {"en": "Clay Loam", "kn": "ಜೇಡಿ ಮಣ್ಣು"},
            "lateritic": {"en": "Lateritic", "kn": "ಕೆಂಪು ಮಣ್ಣು"},
            "Deficient": {"en": "Deficient", "kn": "ಕೊರತೆ ಇದೆ"},
            "Sufficient": {"en": "Sufficient", "kn": "ಸಾಕಷ್ಟು ಇದೆ"},
            "Unknown": {"en": "Unknown", "kn": "ಗೊತ್ತಿಲ್ಲ"}
        }
        return mappings.get(val, {"en": val, "kn": val})

    response = {
        "status": "success",
        "meta": {
            "mode": "GPS Zone" if used_gps_mode else "Lab Report",
            "region": profile["taluk"] if used_gps_mode else "User Field",
            "zone": profile.get("zone", "Unknown"),
            "topography": profile.get("topography", "Unknown"),
            "crop": crop,
            "soil_profile": {
                "nitrogen": localize(n_status),
                "phosphorus": localize(p_status),
                "potassium": localize(k_status),
                "zinc": localize("Deficient" if zinc_val < 0.6 else "Sufficient"),
                "iron": localize(fe_status),
                "boron": localize(b_status),
                "sulphur": localize(s_status),
                "ph_status": localize("acidic" if ph < 6.0 else "neutral" if ph < 7.5 else "alkaline"),
                "ph_value": ph,
                "type": localize(soil_type),
                "salinity": localize(profile.get("salinity", "Normal"))
            }
        },
        "advisory": {
            "summary_card": [
                {"label": {"en": "Soil Health", "kn": "ಮಣ್ಣಿನ ಆರೋಗ್ಯ"}, "value": advisory.soil_health_card[0]},
                {"label": {"en": "Sowing Date", "kn": "ಬಿತ್ತನೆ ದಿನಾಂಕ"}, "value": advisory.soil_health_card[1]}
            ],
            
            "soil_health_checklist": {
                "moisture": physical_tips["moisture"],
                "drainage": physical_tips["drainage"],
                "erosion": physical_tips["erosion"],
                "crop_suitability": {
                    "score": suitability["score"],
                    "warnings": suitability["warnings"]
                }
            },
            
            "management_tips": mgmt_tips,

            "shopping_list": [
                {
                    "name": {"en": item.product_en, "kn": item.product_kn},
                    "qty_display": {
                        "en": f"{item.bags} Bags + {item.loose_kg:.1f} kg" if item.bags > 0 else f"{item.loose_kg:.1f} kg (Loose)",
                        "kn": f"{item.bags} ಬ್ಯಾಗ್ + {item.loose_kg:.1f} ಕೆ.ಜಿ" if item.bags > 0 else f"{item.loose_kg:.1f} ಕೆ.ಜಿ (ಬಿಡಿ)"
                    },
                    "bags": item.bags,
                    "loose_kg": item.loose_kg
                } for item in advisory.shopping_list
            ],
            "schedule": [
                {
                    "date": s.date_range,
                    "activity": {"en": s.stage_name, "kn": s.stage_kannada},
                    "products": {
                        "en": s.products_en,
                        "kn": s.products_kn
                    },
                    "instructions": s.instructions
                } for s in advisory.schedule
            ],
            "substitutes": advisory.substitutes,
            "voice_script": advisory.voice_script,
            "alerts": advisory.simple_warnings + ([{
                "en": "⚠️ Seasonal Salinity Warning: Saltwater intrusion likely. Flush field or use green manure.",
                "kn": "⚠️ ಉಪ್ಪುನೀರು ನುಗ್ಗುವ ಸಾಧ್ಯತೆ: ಹಸಿರೆಲೆ ಗೊಬ್ಬರ ಬಳಸಿ ಅಥವಾ ಹೊಲಕ್ಕೆ ನೀರು ಹಾಯಿಸಿ ಹೊರಬಿಡಿ."
            }] if profile.get("salinity") == "High" else []),
            "savings_msg": advisory.manure_credit_msg
        },
        "disclaimer": "⚠️ Data based on regional averages. Actual field status may vary. Verify with Soil Health Card."
    }
    
    return flatten_localization(response, language)

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
