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
    Main Entry Point for Soil Health and Correction Intelligence.
    Returns structured soil intelligence in English/Kannada.
    """
    
    # 1. Parse Inputs
    crop = request_json.get("crop", "Paddy")
    language = request_json.get("language", "en").lower()
    if language not in ["en", "kn"]:
        language = "en"
        
    lat = request_json.get("lat") or request_json.get("latitude")
    lon = request_json.get("lon") or request_json.get("longitude")
    
    # 2. Determine Data Source
    if "ph" in request_json and "nitrogen_kg_ha" in request_json:
        # A. PRECISION MODE (Lab)
        try:
            ph = float(request_json["ph"])
            n_status = _get_status(request_json["nitrogen_kg_ha"], "n")
            p_status = _get_status(request_json["phosphorus_kg_ha"], "p")
            k_status = _get_status(request_json["potassium_kg_ha"], "k")
            soil_type = request_json.get("texture", "lateritic")
            oc_status = request_json.get("organic_carbon", "medium")
            zinc_val = float(request_json.get("zinc_ppm", 0.5))
            
            fe_status = "Sufficient" 
            mn_status = "Sufficient"
            b_status = "Unknown"
            s_status = "Unknown"
            
            profile = {"taluk": "Lab", "zone": "User", "topography": "User", "salinity": "Normal"}
            
        except (ValueError, TypeError):
             return {"error": "Invalid numeric values in Soil Data"}
    
    elif lat is not None and lon is not None:
        # B. GPS MODE
        try:
            lat = float(lat)
            lon = float(lon)
        except (ValueError, TypeError):
            return {"error": "Invalid Latitude/Longitude"}
            
        zinc_val = 0.5 
        land_type_input = request_json.get("land_type")
        sowing_date = request_json.get("sowing_date", datetime.now().strftime("%Y-%m-%d"))
        
        try:
            sow_dt = datetime.strptime(sowing_date, "%Y-%m-%d")
            sow_month = sow_dt.month
        except:
            sow_month = datetime.now().month

        profile = resolver.get_profile(lat, lon, land_type_override=land_type_input, month=sow_month)
        
        ph = 5.5 if profile["ph_class"] == "acidic" else 6.5
        if profile.get("ph_class") == "alkaline":
            ph = 7.5
            
        n_status = profile["n"]
        p_status = profile["p"]
        k_status = profile["k"]
        soil_type = profile["texture"]
        oc_status = profile.get("organic_carbon", "medium")
        
        fe_status = "Sufficient"
        mn_status = "Sufficient"
        b_status = "Deficient" if crop.lower() in ["arecanut", "coconut"] else "Sufficient"
        s_status = "Deficient" if soil_type == "sandy" else "Sufficient"
            
    else:
        return {"error": "Missing Soil Data or GPS Coordinates"}

    # 3. Scientific Models
    lime_result = calculate_lime(ph, None, soil_type)
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
    
    # 4. Translations & Mappings
    def localize(val: str) -> Dict[str, str]:
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
            "Unknown": {"en": "Unknown", "kn": "ಗೊತ್ತಿಲ್ಲ"},
            "Moderate": {"en": "Moderate", "kn": "ಮಧ್ಯಮ"},
            "Excellent": {"en": "Excellent", "kn": "ಅತ್ಯುತ್ತಮ"},
            "Good": {"en": "Good", "kn": "ಉತ್ತಮ"}
        }
        return mappings.get(val, {"en": val, "kn": val})

    whc_map = {
        "sandy": {"en": "Low", "kn": "ಕಡಿಮೆ"},
        "lateritic": {"en": "Medium", "kn": "ಮಧ್ಯಮ"},
        "clay_loam": {"en": "High", "kn": "ಹೆಚ್ಚು"}
    }
    
    # 5. Build Response
    response = {
        "status": "success",
        "soil_profile": {
            "soil_type": localize(soil_type),
            "texture_classification": localize(soil_type),
            "water_holding_capacity": whc_map.get(soil_type, {"en": "Medium", "kn": "ಮಧ್ಯಮ"})
        },
        "soil_chemical_properties": {
            "ph_value": ph,
            "ph_classification": localize("acidic" if ph < 6.0 else "neutral" if ph < 7.5 else "alkaline"),
            "organic_carbon_status": localize(oc_status)
        },
        "nutrient_status": {
            "primary": {
                "nitrogen": localize(n_status),
                "phosphorus": localize(p_status),
                "potassium": localize(k_status)
            },
            "secondary": {
                "sulphur": localize(s_status)
            },
            "micronutrients": {
                "zinc": localize("Deficient" if zinc_val < 0.6 else "Sufficient"),
                "iron": localize(fe_status),
                "boron": localize(b_status),
                "manganese": localize(mn_status)
            }
        },
        "deficiency_report": [],
        "soil_correction_recommendations": {
            "recommended_fertilizer": [
                {
                    "name": {"en": "Urea", "kn": "ಯೂರಿಯಾ"},
                    "quantity": {"en": f"{stcr_result.urea_kg} kg/ha", "kn": f"{stcr_result.urea_kg} ಕೆ.ಜಿ/ಹೆಕ್ಟೇರ್"},
                    "method": {"en": "Broadcasting in split doses", "kn": "ಕಂತುಗಳಲ್ಲಿ ಮೇಲೆರಚುವುದು"}
                },
                {
                    "name": {"en": "DAP", "kn": "ಡಿ.ಎ.ಪಿ"},
                    "quantity": {"en": f"{stcr_result.dap_kg} kg/ha", "kn": f"{stcr_result.dap_kg} ಕೆ.ಜಿ/ಹೆಕ್ಟೇರ್"},
                    "method": {"en": "Basal application at sowing", "kn": "ಬಿತ್ತನೆ ಸಮಯದಲ್ಲಿ ಅಡಿಗೊಬ್ಬರವಾಗಿ"}
                },
                {
                    "name": {"en": "MOP", "kn": "ಪೊಟ್ಯಾಷ್"},
                    "quantity": {"en": f"{stcr_result.mop_kg} kg/ha", "kn": f"{stcr_result.mop_kg} ಕೆ.ಜಿ/ಹೆಕ್ಟೇರ್"},
                    "method": {"en": "Basal and top dressing", "kn": "ಅಡಿಗೊಬ್ಬರ ಮತ್ತು ಮೇಲುಗೊಬ್ಬರವಾಗಿ"}
                }
            ],
            "recommended_organic_amendment": {
                "type": {"en": "Farm Yard Manure (FYM)", "kn": "ಕೊಟ್ಟಿಗೆ ಗೊಬ್ಬರ"},
                "quantity": {"en": "10-12 tons/ha", "kn": "10-12 ಟನ್/ಹೆಕ್ಟೇರ್"},
                "method": {"en": "Incorporate during final ploughing", "kn": "ಕೊನೆಯ ಉಳಿಮೆಯ ಸಮಯದಲ್ಲಿ ಮಣ್ಣಿಗೆ ಸೇರಿಸಿ"}
            },
            "ph_correction": {
                "suggestion": {"en": "Apply Dolomite/Lime" if ph < 6.0 else "Not required", "kn": "ಡೋಲೋಮೈಟ್/ಸುಣ್ಣ ಬಳಸಿ" if ph < 6.0 else "ಅಗತ್ಯವಿಲ್ಲ"},
                "quantity": {"en": f"{lime_t_ha} tons/ha", "kn": f"{lime_t_ha} ಟನ್/ಹೆಕ್ಟೇರ್"} if ph < 6.0 else {"en": "0", "kn": "0"},
                "method": {"en": "Apply 2 weeks before sowing", "kn": "ಬಿತ್ತನೆಗೆ 2 ವಾರ ಮೊದಲು ಮಣ್ಣಿಗೆ ಸೇರಿಸಿ"}
            }
        },
        "soil_suitability_index": {
            "score": generate_crop_suitability(profile, crop)["score"],
            "limiting_factors": [w for w in generate_crop_suitability(profile, crop)["warnings"]]
        }
    }

    # Populate deficiency report
    if n_status == "low": response["deficiency_report"].append({"nutrient": localize("n"), "severity": {"en": "High", "kn": "ಹೆಚ್ಚು"}})
    if p_status == "low": response["deficiency_report"].append({"nutrient": localize("p"), "severity": {"en": "High", "kn": "ಹೆಚ್ಚು"}})
    if k_status == "low": response["deficiency_report"].append({"nutrient": localize("k"), "severity": {"en": "High", "kn": "ಹೆಚ್ಚು"}})
    if zinc_val < 0.6: response["deficiency_report"].append({"nutrient": localize("zinc"), "severity": {"en": "Moderate", "kn": "ಮಧ್ಯಮ"}})
    if s_status == "Deficient": response["deficiency_report"].append({"nutrient": localize("sulphur"), "severity": {"en": "Moderate", "kn": "ಮಧ್ಯಮ"}})
    if b_status == "Deficient": response["deficiency_report"].append({"nutrient": localize("boron"), "severity": {"en": "Moderate", "kn": "ಮಧ್ಯಮ"}})
    
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
