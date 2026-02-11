#!/usr/bin/env python3
"""
GrowMate Farmer View Module v5.0
Translates research data into practical farmer advice.

Includes:
- Bag converter (kg -> bags)
- Application calendar
- simplified advisory
- Shopping list generation

"Think like a farmer, verify like a scientist."
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta

# =============================================================================
# CONSTANTS & CONFIGURATION
# =============================================================================


# =============================================================================
# CONSTANTS & CONFIGURATION
# =============================================================================

BAG_SIZES = {
    "urea": 45,
    "dap": 50,
    "mop": 50,
    "ssp": 50,
    "zinc_sulfate": 10,
    "borax": 1,
    "dolomite": 50,
    "gypsum": 50,
    "magnesium_sulfate": 25,
}

# Structured Names
LOCAL_NAMES = {
    "urea": {"en": "Urea", "kn": "ಯೂರಿಯಾ"},
    "dap": {"en": "DAP", "kn": "ಡಿ.ಎ.ಪಿ"},
    "mop": {"en": "MOP (Potash)", "kn": "ಪೊಟ್ಯಾಷ್ (MOP)"},
    "ssp": {"en": "SSP", "kn": "ಸೂಪರ್ (SSP)"},
    "dolomite": {"en": "Dolomite Lime", "kn": "ಡೋಲೋಮೈಟ್ ಸುಣ್ಣ"},
    "zinc_sulfate": {"en": "Zinc Sulfate", "kn": "ಜಿಂಕ್ (Zinc)"},
    "borax": {"en": "Borax", "kn": "ಬೋರಾಕ್ಸ್"},
    "magnesium_sulfate": {"en": "Magnesium Sulfate", "kn": "ಮೆಗ್ನೀಸಿಯಮ್ (Epsom)"},
}

# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class ShoppingItem:
    product_name: str
    product_en: str
    product_kn: str
    total_kg: float
    bags: int
    loose_kg: float
    bag_size: int

@dataclass
class ScheduleItem:
    stage_name: str
    stage_kannada: str
    timing: str
    date_range: str
    products_en: List[str]
    products_kn: List[str]
    instructions: Dict[str, str] # {en:.., kn:..}

@dataclass
class FarmerAdvisory:
    crop_name: str
    sowing_date: str
    shopping_list: List[ShoppingItem]
    schedule: List[ScheduleItem]
    # Changed to Dicts
    simple_warnings: List[Dict[str, str]] 
    soil_health_card: List[Dict[str, str]]
    # v5.2 Enhancements
    substitutes: List[Dict[str, str]]
    voice_script: str
    manure_credit_msg: Dict[str, str]

# ... (Colloquial Units & Mixing Guide omitted for brevity, logic remains similar but localized)

MIXING_COMPATIBILITY = {
    ("calcium", "phosphate"): False,
    ("urea", "lime"): False,
    ("ammonium", "lime"): False,
    ("zinc", "phosphate"): False,
    ("urea", "mop"): True,
    ("urea", "dap"): True,
    ("dap", "mop"): True,
}

RAIN_THRESHOLDS = {
    "light": 2.5,
    "moderate": 10.0,
    "heavy": 20.0,
}

def get_colloquial_measure(product: str, kg_amount: float) -> Dict[str, str]:
    """Convert to mugs/buckets (EN/KN)."""
    # ... (Simplified for brevity, assuming standard unit lookup)
    # For now returning simple string, ideally should be structured.
    return {"en": f"{kg_amount} kg", "kn": f"{kg_amount} ಕೆ.ಜಿ"}

def check_compatibility(shopping_list: List[ShoppingItem]) -> List[Dict[str, str]]:
    """Check mixing rules."""
    warnings = []
    products = [item.product_name.lower() for item in shopping_list if item.total_kg > 0]
    
    has_lime = any("lime" in p or "dolomite" in p for p in products)
    has_dap = any("dap" in p or "phosphate" in p for p in products)
    has_urea = any("urea" in p or "ammonium" in p for p in products)
    has_zinc = any("zinc" in p for p in products)
    
    if has_lime and has_dap:
        warnings.append({
            "en": "⚠️ DO NOT MIX Lime and DAP. Apply Lime 2 weeks before.",
            "kn": "⚠️ ಸುಣ್ಣ ಮತ್ತು ಡಿ.ಎ.ಪಿ ಮಿಶ್ರಣ ಮಾಡಬೇಡಿ. ಸುಣ್ಣವನ್ನು 2 ವಾರಗಳ ಮೊದಲು ಹಾಕಿ."
        })
    if has_lime and has_urea:
        warnings.append({
            "en": "⚠️ DO NOT MIX Lime and Urea. Nitrogen loss occurs.",
            "kn": "⚠️ ಸುಣ್ಣ ಮತ್ತು ಯೂರಿಯಾ ಮಿಶ್ರಣ ಮಾಡಬೇಡಿ. ಸಾರಜನಕ ನಷ್ಟವಾಗುತ್ತದೆ."
        })
    if has_zinc and has_dap:
        warnings.append({
            "en": "⚠️ DO NOT MIX Zinc and DAP. Apply Zinc separately.",
            "kn": "⚠️ ಜಿಂಕ್ ಮತ್ತು ಡಿ.ಎ.ಪಿ ಮಿಶ್ರಣ ಮಾಡಬೇಡಿ. ಜಿಂಕ್ ಅನ್ನು ಪ್ರತ್ಯೇಕವಾಗಿ ಹಾಕಿ."
        })
        
    return warnings

def check_weather_rule(forecast_mm: float) -> Dict[str, str]:
    if forecast_mm > RAIN_THRESHOLDS["heavy"]:
        return {
            "en": "🔴 HEAVY RAIN FORECAST: STOP! Do not apply fertilizer today.",
            "kn": "🔴 ಭಾರೀ ಮಳೆ ಮುನ್ಸೂಚನೆ: ನಿಲ್ಲಿಸಿ! ಇಂದು ಗೊಬ್ಬರ ಹಾಕಬೇಡಿ."
        }
    elif forecast_mm > RAIN_THRESHOLDS["moderate"]:
        return {
            "en": "⚠️ Rain expected: Avoid Urea/Nitrogen application today.",
            "kn": "⚠️ ಮಳೆ ನಿರೀಕ್ಷೆ: ಇಂದು ಯೂರಿಯಾ ಹಾಕುವುದನ್ನು ತಡೆಯಿರಿ."
        }
    else:
        return {
            "en": "✅ Weather suitable for application.",
            "kn": "✅ ಗೊಬ್ಬರ ಹಾಕಲು ಹವಾಮಾನ ಸೂಕ್ತವಾಗಿದೆ."
        }

# =============================================================================
# MANURE CREDITS & SUBSTITUTES (v5.2)
# =============================================================================

MANURE_NUTRIENTS = {
    "fym": {"n_pct": 0.5, "p_pct": 0.25, "k_pct": 0.5, "availability": 0.3}, # 30% available in 1st year
    "vermicompost": {"n_pct": 1.5, "p_pct": 1.0, "k_pct": 1.5, "availability": 0.4},
    "poultry": {"n_pct": 3.0, "p_pct": 2.5, "k_pct": 1.5, "availability": 0.5},
}

SUBSTITUTES = {
    # If Primary is missing -> Use Alternatives
    "dap": [
        {"name": "SSP + Urea", "ratio_n": 0.0, "ratio_p": 1.0, "note": "Use 3 bags SSP for 1 bag DAP"} 
        # Logic is complex, handled in function
    ],
    "mop": [
        {"name": "SOP (Sulphate of Potash)", "factor": 1.2, "note": "Costlier but better quality"}
    ]
}

def calculate_manure_credit(manure_type: str, quantity_tons: float) -> Dict[str, float]:
    """
    Calculate nutrient credit from organic manure.
    Returns kg/ha of effective N, P, K.
    """
    if manure_type not in MANURE_NUTRIENTS:
        return {"n": 0, "p": 0, "k": 0}
        
    data = MANURE_NUTRIENTS[manure_type]
    eff = data["availability"]
    
    # Tons to Kg
    kg_total = quantity_tons * 1000
    
    n_credit = kg_total * (data["n_pct"] / 100) * eff
    p_credit = kg_total * (data["p_pct"] / 100) * eff
    k_credit = kg_total * (data["k_pct"] / 100) * eff
    
    return {"n": n_credit, "p": p_credit, "k": k_credit}


def get_substitute_advice(product: str, bag_count: int) -> Dict[str, str]:
    """Get Plan B if product is unavailable."""
    if bag_count == 0:
        return {}
        
    if product.lower() == "dap":
        ssp_bags = bag_count * 3
        urea_bags = round(bag_count * 0.4, 1)
        return {
            "en": f"💡 **Plan B**: If DAP unavailable, use **{ssp_bags} bags SSP + {urea_bags} bags Urea**.",
            "kn": f"💡 **ಬದಲಿ ವಿಧಾನ**: ಡಿ.ಎ.ಪಿ ಸಿಗ ದಿದ್ದರೆ, **{ssp_bags} ಬ್ಯಾಗ್ ಸೂಪರ್ + {urea_bags} ಬ್ಯಾಗ್ ಯೂರಿಯಾ** ಬಳಸಿ."
        }
        
    return {}

def generate_voice_script(advisory: FarmerAdvisory) -> str:
    """Generate phonetic Kannada script."""
    # Logic uses Kannada fields
    script = f"Namaskara. Nimma {advisory.crop_name} belege..."
    script += f" Bithane dina: {advisory.sowing_date}..."
    
    script += " Neevu khareedi madbekada gobbara: "
    for item in advisory.shopping_list:
        if item.bags > 0:
            script += f"{item.bags} bag {item.product_kn}, "
            
    if any("Lime" in w.get('en', '') for w in advisory.simple_warnings):
        script += " Manninalli amla amsha hecchige ide, sunna haakodu kaddaya."
        
    script += " Dhanyavadagalu."
    return script

def convert_to_bags(product: str, kg_amount: float) -> ShoppingItem:
    """
    Convert raw kg to bags + loose kg.
    """
    bag_size = BAG_SIZES.get(product.lower(), 50)
    kg_amount = round(kg_amount, 1)
    
    bags = int(kg_amount // bag_size)
    loose = round(kg_amount % bag_size, 1)
    
    if loose > (bag_size * 0.95):
        bags += 1
        loose = 0
    
    names = LOCAL_NAMES.get(product.lower(), {"en": product.title(), "kn": product.title()})
    
    return ShoppingItem(
        product_name=product,
        product_en=names["en"],
        product_kn=names["kn"],
        total_kg=kg_amount,
        bags=bags,
        loose_kg=loose,
        bag_size=bag_size
    )

def generate_schedule(
    sowing_date: datetime,
    splits: Dict,
    n_kg: float,
    p_kg: float,
    k_kg: float,
    urea_total: float,
    dap_total: float,
    mop_total: float
) -> List[ScheduleItem]:
    """
    Generate a calendar-based schedule from splits.
    """
    schedule_items = []
    
    for stage, details in splits.items():
        # Timing logic
        days_offset = 0
        if "basal" in stage:
            days_offset = 0
            timing_str = "ಬಿತ್ತನೆ/ನಾಟಿ ಸಮಯದಲ್ಲಿ"
        elif "tillering" in stage or "vegetative" in stage:
            days_offset = 25
            timing_str = "ನಾಟಿಯಾದ 20-25 ದಿನಗಳಿಗೆ"
        elif "panicle" in stage or "flowering" in stage:
            days_offset = 55
            timing_str = "ನಾಟಿಯಾದ 50-60 ದಿನಗಳಿಗೆ"
        else:
            days_offset = 45 # Default
            timing_str = "ಮುಂದಿನ ಹಂತ"
            
        target_date = sowing_date + timedelta(days=days_offset)
        date_str = target_date.strftime("%d-%b-%Y")
        
        p_pct = details.get("p_pct", 0)
        n_pct = details.get("n_pct", 0)
        k_pct = details.get("k_pct", 0)
        
        split_dap = dap_total * (p_pct / 100)
        split_mop = mop_total * (k_pct / 100)
        split_urea = urea_total * (n_pct / 100)
        
        products_en = []
        products_kn = []
        
        if split_urea > 1:
            bags = convert_to_bags("urea", split_urea)
            qty_en = f"{bags.bags} Bags" if bags.bags > 0 else ""
            qty_kn = f"{bags.bags} ಬ್ಯಾಗ್" if bags.bags > 0 else ""
            if bags.loose_kg > 0:
                qty_en += f" + {bags.loose_kg:.0f} kg"
                qty_kn += f" + {bags.loose_kg:.0f} kg"
            products_en.append(f"Urea: {qty_en.strip(' + ')}")
            products_kn.append(f"ಯೂರಿಯಾ: {qty_kn.strip(' + ')}")
            
        if split_dap > 1:
            bags = convert_to_bags("dap", split_dap)
            qty_en = f"{bags.bags} Bags" if bags.bags > 0 else ""
            qty_kn = f"{bags.bags} ಬ್ಯಾಗ್" if bags.bags > 0 else ""
            if bags.loose_kg > 0:
                qty_en += f" + {bags.loose_kg:.0f} kg"
                qty_kn += f" + {bags.loose_kg:.0f} kg"
            products_en.append(f"DAP: {qty_en.strip(' + ')}")
            products_kn.append(f"ಡಿ.ಎ.ಪಿ: {qty_kn.strip(' + ')}")

        if split_mop > 1:
            bags = convert_to_bags("mop", split_mop)
            qty_en = f"{bags.bags} Bags" if bags.bags > 0 else ""
            qty_kn = f"{bags.bags} ಬ್ಯಾಗ್" if bags.bags > 0 else ""
            if bags.loose_kg > 0:
                qty_en += f" + {bags.loose_kg:.0f} kg"
                qty_kn += f" + {bags.loose_kg:.0f} kg"
            products_en.append(f"MOP: {qty_en.strip(' + ')}")
            products_kn.append(f"ಪೊಟ್ಯಾಷ್: {qty_kn.strip(' + ')}")
            
        if not products_en:
            continue
            
        schedule_items.append(ScheduleItem(
            stage_name=stage,
            stage_kannada=timing_str,
            timing=f"Day {days_offset}",
            date_range=date_str,
            products_en=products_en,
            products_kn=products_kn,
            instructions={
                "en": details.get("timing_en", details.get("timing", "")),
                "kn": details.get("timing_kn", details.get("timing", ""))
            }
        ))
        
    return schedule_items

def simplify_advisory(
    crop: str,
    sowing_date_str: str,
    urea_kg: float,
    dap_kg: float,
    mop_kg: float,
    zinc_kg: float = 0,
    lime_t_ha: float = 0,
    splits: Dict = {},
    raw_warnings: List[str] = [],
    weather_forecast_mm: float = 0.0, 
    manure_type: str = None,
    manure_tons: float = 0.0,
    area_acres: float = 1.0
) -> FarmerAdvisory:
    """
    Create the full farmer advisory structure.
    """
    try:
        sowing_date = datetime.strptime(sowing_date_str, "%Y-%m-%d")
    except:
        sowing_date = datetime.now()
        
    acre_factor = 2.5 
    
    urea_acre = urea_kg / acre_factor
    dap_acre = dap_kg / acre_factor
    mop_acre = mop_kg / acre_factor
    zinc_acre = zinc_kg / acre_factor
    lime_tons_acre = lime_t_ha / acre_factor
    
    manure_msg = {}
    net_urea_acre = urea_acre
    net_dap_acre = dap_acre
    net_mop_acre = mop_acre
    
    if manure_type and manure_tons > 0:
        manure_tons_acre = manure_tons 
        credits = calculate_manure_credit(manure_type, manure_tons_acre) 
        
        urea_reduction = credits['n'] / 0.46
        dap_reduction = credits['p'] / 0.46 
        mop_reduction = credits['k'] / 0.60
        
        net_urea_acre = max(0, urea_acre - urea_reduction)
        net_dap_acre = max(0, dap_acre - dap_reduction)
        net_mop_acre = max(0, mop_acre - mop_reduction)
        
        manure_msg = {
            "en": f"✅ Manure Credit: Reduced Urea by {round(urea_reduction,1)}kg & DAP by {round(dap_reduction,1)}kg",
            "kn": f"✅ ಕೊಟ್ಟಿಗೆ ಗೊಬ್ಬರ ಲಾಭ: ಯೂರಿಯಾ {round(urea_reduction,1)} ಕೆ.ಜಿ ಹಾಗೂ ಡಿ.ಎ.ಪಿ {round(dap_reduction,1)} ಕೆ.ಜಿ ಕಡಿಮೆ ಬಳಸಬಹುದು"
        }

    # 1. Shopping List
    shopping = []
    
    if lime_tons_acre > 0.1:
        lime_kg_acre = lime_tons_acre * 1000
        shopping.append(convert_to_bags("dolomite", lime_kg_acre))
        
    shopping.append(convert_to_bags("urea", net_urea_acre))
    shopping.append(convert_to_bags("dap", net_dap_acre))
    shopping.append(convert_to_bags("mop", net_mop_acre))
    
    if zinc_acre > 2:
        shopping.append(convert_to_bags("zinc_sulfate", zinc_acre))
        
    # 2. Schedule
    schedule = generate_schedule(
        sowing_date, splits, 
        0, 0, 0, 
        net_urea_acre, net_dap_acre, net_mop_acre
    )
    
    # 3. Simple Soil Health Card
    health_card_status = {
        "en": "✅ Soil Health: Good" if not any("Critical" in w for w in raw_warnings) else "⚠️ Soil Health: Needs Improvement",
        "kn": "✅ ಮಣ್ಣಿನ ಆರೋಗ್ಯ: ಉತ್ತಮವಾಗಿದೆ" if not any("Critical" in w for w in raw_warnings) else "⚠️ ಮಣ್ಣಿನ ಆರೋಗ್ಯ: ಸುಧಾರಣೆ ಅಗತ್ಯ"
    }
    
    health_card = [
        health_card_status,
        {
            "en": f"📅 Sowing Date: {sowing_date.strftime('%d-%m-%Y')}",
            "kn": f"📅 ಬಿತ್ತನೆ ದಿನಾಂಕ: {sowing_date.strftime('%d-%m-%Y')}"
        }
    ]
    
    # 4. Warnings
    simple_warnings = []
    
    # A. Weather Rule
    weather_msg = check_weather_rule(weather_forecast_mm)
    simple_warnings.append(weather_msg)
    
    # B. Compatibility Rule
    mix_warnings = check_compatibility(shopping)
    simple_warnings.extend(mix_warnings)
    
    # C. Existing Soil Warnings
    for w in raw_warnings:
        # Translate commonly known warnings
        if "Al toxicity" in w or "Al ವಿಷತ್ವ" in w:
            simple_warnings.append({
                "en": "⚠️ High Acidity - Lime application mandatory.",
                "kn": "⚠️ ಮಣ್ಣಿನಲ್ಲಿ ಆಮ್ಲತೆ ಹೆಚ್ಚಾಗಿದೆ - ಸುಣ್ಣ ಹಾಕುವುದು ಕಡ್ಡಾಯ."
            })
        elif "Drainage" in w or "ನೀರು ಬಸಿಯುವಿಕೆ" in w:
            simple_warnings.append({
                "en": "⚠️ Improve drainage to avoid waterlogging.",
                "kn": "⚠️ ಹೊಲದಲ್ಲಿ ನೀರು ನಿಲ್ಲದಂತೆ ನೋಡಿಕೊಳ್ಳಿ."
            })
        elif "GPS Mode" in w:
             # Extract Taluk/Region if present
             region = w.split("for")[-1].strip() if "for" in w else ""
             simple_warnings.append({
                "en": w,
                "kn": f"⚠️ GPS ವಿಧಾನ ({region} ಭಾಗದ ಸರಾಸರಿ ಮಾಹಿತಿ) ಬಳಸಲಾಗಿದೆ." if region else "⚠️ GPS ವಿಧಾನ ಬಳಸಲಾಗಿದೆ."
             })
        else:
            simple_warnings.append({"en": w, "kn": w}) # Fallback
            
    # D. Substitutes
    substitutes = []
    for item in shopping:
        sub = get_substitute_advice(item.product_name, item.bags)
        if sub:
            substitutes.append(sub)
            
    return FarmerAdvisory(
        crop_name=crop,
        sowing_date=sowing_date.strftime("%d-%m-%Y"),
        shopping_list=shopping,
        schedule=schedule,
        simple_warnings=simple_warnings,
        soil_health_card=health_card,
        substitutes=substitutes,
        voice_script="",
        manure_credit_msg=manure_msg
    )
    # Generate Script
    partial_advisory.voice_script = generate_voice_script(partial_advisory)
    
    return partial_advisory

def generate_quick_decisions(forecast_mm: float, soil_moisture: str) -> Dict[str, Any]:
    """
    Generate YES/NO decisions based on weather/soil.
    """
    # Logic
    can_irrigate = True
    can_fertilize = True
    can_spray = True
    
    irrigate_reason = {"en": "Soil is dry.", "kn": "ಮಣ್ಣು ಒಣಗಿದೆ."}
    fertilize_reason = {"en": "Weather is clear.", "kn": "ಹವಾಮಾನ ಸ್ವಚ್ಛವಾಗಿದೆ."}
    spray_reason = {"en": "Low wind/rain.", "kn": "ಗಾಳಿ/ಮಳೆ ಕಡಿಮೆ."}
    
    # 1. Rain Rules
    if forecast_mm > 5.0:
        can_irrigate = False
        irrigate_reason = {"en": "Rain expected.", "kn": "ಮಳೆ ಬರುವ ಸಾಧ್ಯತೆ."}
        
    if forecast_mm > 2.0:
        can_spray = False
        spray_reason = {"en": "Rain may wash off spray.", "kn": "ಮಳೆಯಿಂದ ಔಷಧಿ ಕೊಚ್ಚಿ ಹೋಗಬಹುದು."}
        
    if forecast_mm > 10.0:
        can_fertilize = False
        fertilize_reason = {"en": "Heavy rain forecast.", "kn": "ಭಾರೀ ಮಳೆ ಮುನ್ಸೂಚನೆ."}
        
    # 2. Soil Rules
    if "High" in soil_moisture or "Wet" in soil_moisture:
        can_irrigate = False
        irrigate_reason = {"en": "Soil has enough moisture.", "kn": "ಮಣ್ಣಿನಲ್ಲಿ ಸಾಕಷ್ಟು ತೇವಾಂಶವಿದೆ."}

    return {
        "irrigation": {
            "action": {"en": "Irrigate" if can_irrigate else "Do Not Irrigate", "kn": "ನೀರು ಹಾಯಿಸಿ" if can_irrigate else "ನೀರು ಹಾಯಿಸಬೇಡಿ"},
            "allowed": can_irrigate,
            "reason": irrigate_reason
        },
        "fertilizer": {
            "action": {"en": "Apply Fertilizer" if can_fertilize else "Wait", "kn": "ಗೊಬ್ಬರ ಹಾಕಿ" if can_fertilize else "ಕಾಯಿರಿ"},
            "allowed": can_fertilize,
            "reason": fertilize_reason
        },
        "spray": {
            "action": {"en": "Spray Pesticide" if can_spray else "Avoid Spraying", "kn": "ಔಷಧಿ ಸಿಂಪಡಿಸಿ" if can_spray else "ಸಿಂಪಡಣೆ ಬೇಡ"},
            "allowed": can_spray,
            "reason": spray_reason
        }
    }
    
# =============================================================================
# DEMO
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("GrowMate Farmer View v5.1 (Enhanced)")
    print("=" * 60)
    
    # Mock inputs
    advisory = simplify_advisory(
        crop="Paddy (ಭತ್ತ)",
        sowing_date_str="2024-06-15",
        urea_kg=232,
        dap_kg=260,
        mop_kg=173,
        lime_t_ha=2.75,
        zinc_kg=25,
        splits={
            "basal": {"n_pct": 50, "p_pct": 100, "k_pct": 50, "timing": "ನಾಟಿಯ ಸಮಯದಲ್ಲಿ"},
            "top1": {"n_pct": 50, "p_pct": 0, "k_pct": 50, "timing": "ತೆಂಡೆ ಒಡೆಯುವಾಗ"}, 
        },
        raw_warnings=["⚠️ Al ವಿಷತ್ವ ಅಪಾಯ"],
        weather_forecast_mm=5.0 # Light rain
    )
    
    print("\n📋 1. SHOPPING LIST (ಪ್ರತಿ ಎಕರೆಗೆ)")
    print("-" * 40)
    for item in advisory.shopping_list:
        if item.bags > 0 or item.loose_kg > 0:
            qty = f"{item.bags} ಬ್ಯಾಗ್"
            if item.loose_kg > 0:
                # NEW: Colloquial units
                noun_units = get_colloquial_measure(item.product_name, item.loose_kg)
                qty += f" + {noun_units}"
            print(f"🛒 {item.product_local:<20} : {qty}")
            
    print("\n⚠️ 2. ALERTS (ಗಮನಿಸಿ)")
    print("-" * 40)
    for w in advisory.simple_warnings:
        print(w)
        
    print("\n✅ Enhanced Farmer View Ready!")
