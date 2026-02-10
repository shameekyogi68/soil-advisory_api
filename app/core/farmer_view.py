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
from typing import Dict, List, Optional, Union
from datetime import datetime, timedelta

# =============================================================================
# CONSTANTS & CONFIGURATION
# =============================================================================

BAG_SIZES = {
    "urea": 45,           # New neem coated urea bag size
    "dap": 50,
    "mop": 50,
    "ssp": 50,
    "zinc_sulfate": 10,   # Common bag size
    "borax": 1,           # Packet size
    "dolomite": 50,
    "gypsum": 50,
    "magnesium_sulfate": 25,
}

LOCAL_NAMES = {
    "urea": "ಯೂರಿಯಾ (Urea)",
    "dap": "ಡಿ.ಎ.ಪಿ (DAP)",
    "mop": "ಪೊಟ್ಯಾಷ್ (MOP)",
    "ssp": "ಸೂಪರ್ (SSP)",
    "dolomite": "ಡೋಲೋಮೈಟ್ ಸುಣ್ಣ",
    "zinc_sulfate": "ಜಿಂಕ್ (Zinc)",
    "borax": "ಬೋರಾಕ್ಸ್",
    "magnesium_sulfate": "ಮೆಗ್ನೀಸಿಯಮ್ (Epsom)",
}



# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class ShoppingItem:
    product_name: str
    product_local: str
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
    products: List[str]  # e.g. ["2 bags Urea", "1 bag Potash"]
    instructions: List[str]

@dataclass
class FarmerAdvisory:
    crop_name: str
    sowing_date: str
    shopping_list: List[ShoppingItem]
    schedule: List[ScheduleItem]
    simple_warnings: List[str]
    soil_health_card: List[str]
    # v5.2 Enhancements
    substitutes: List[str]
    voice_script: str
    manure_credit_msg: str = ""

# =============================================================================
# COLLOQUIAL UNITS & MIXING GUIDE
# =============================================================================

COLLOQUIAL_UNITS = {
    "urea": {"mug_1L": 0.65, "handful": 0.05, "bucket_10L": 6.5},  # specific gravity approx 0.65
    "dap": {"mug_1L": 0.95, "handful": 0.06, "bucket_10L": 9.5},   # heavier
    "mop": {"mug_1L": 1.05, "handful": 0.07, "bucket_10L": 10.5},  # standard salt-like
    "zinc_sulfate": {"mug_1L": 1.4, "handful": 0.08, "bucket_10L": 14.0}, # heavy crystal
}

MIXING_COMPATIBILITY = {
    # (Product A, Product B): Safe?
    ("calcium", "phosphate"): False,  # Ca + P -> precipitate (Lime + DAP)
    ("urea", "lime"): False,          # Ammonia loss if mixed
    ("ammonium", "lime"): False,      # Ammonia loss
    ("zinc", "phosphate"): False,     # Zn + P antagonism in soil (apply separately)
    ("urea", "mop"): True,            # Safe
    ("urea", "dap"): True,            # Safe (mix just before use)
    ("dap", "mop"): True,             # Safe
}

RAIN_THRESHOLDS = {
    "light": 2.5,   # mm - Okay to apply
    "moderate": 10.0, # mm - Avoid urea
    "heavy": 20.0,    # mm - STOP all application
}

def get_colloquial_measure(product: str, kg_amount: float) -> str:
    """
    Convert loose kg to mugs/buckets.
    Example: 1.3 kg Urea -> "2 Mugs"
    """
    units = COLLOQUIAL_UNITS.get(product.lower())
    if not units:
        return f"{kg_amount} kg"
        
    mug_capacity = units["mug_1L"]
    
    # If < 1kg, use handfuls? No, too variable. Use mugs or grams.
    mugs = round(kg_amount / mug_capacity, 1)
    
    if mugs < 0.5:
        return f"{int(kg_amount * 1000)} grams"
    elif mugs < 10:
        return f"~{mugs} ಮಗ್ (1L Mug)"
    else:
        buckets = round(kg_amount / units["bucket_10L"], 1)
        return f"~{buckets} ಬಕೆಟ್ (10L Bucket)"

def check_compatibility(shopping_list: List[ShoppingItem]) -> List[str]:
    """Check if items in shopping list can be mixed."""
    warnings = []
    products = [item.product_name.lower() for item in shopping_list if item.total_kg > 0]
    
    # Check Lime vs DAP/Urea
    has_lime = any("lime" in p or "dolomite" in p for p in products)
    has_dap = any("dap" in p or "phosphate" in p for p in products)
    has_urea = any("urea" in p or "ammonium" in p for p in products)
    has_zinc = any("zinc" in p for p in products)
    
    if has_lime and has_dap:
        warnings.append("⚠️ DO NOT MIX Lime and DAP. Apply Lime 2 weeks before.")
    if has_lime and has_urea:
        warnings.append("⚠️ DO NOT MIX Lime and Urea. Nitrogen loss occurs.")
    if has_zinc and has_dap:
        warnings.append("⚠️ DO NOT MIX Zinc and DAP. Apply Zinc separately.")
        
    return warnings

def check_weather_rule(forecast_mm: float) -> str:
    """Get recommendation based on rain forecast."""
    if forecast_mm > RAIN_THRESHOLDS["heavy"]:
        return "🔴 HEAVY RAIN FORECAST: STOP! Do not apply fertilizer today."
    elif forecast_mm > RAIN_THRESHOLDS["moderate"]:
        return "⚠️ Rain expected: Avoid Urea/Nitrogen application today."
    else:
        return "✅ Weather suitable for application."

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

def get_substitute_advice(product: str, bag_count: int) -> str:
    """Get Plan B if product is unavailable."""
    if bag_count == 0:
        return ""
        
    if product.lower() == "dap":
        # 1 Bag DAP (50kg) = 9kg N + 23kg P2O5
        # SSP (16% P2O5) -> Need 144kg SSP (3 bags)
        # Urea (46% N) -> Need 20kg Urea (0.5 bag)
        ssp_bags = bag_count * 3
        urea_bags = round(bag_count * 0.4, 1) # Approx 20kg is close to half bag
        return f"💡 **Plan B**: If DAP unavailble, use **{ssp_bags} bags SSP + {urea_bags} bags Urea**."
        
    return ""

def generate_voice_script(advisory: FarmerAdvisory) -> str:
    """Generate phonetic Kannada script."""
    # Simplified logic for demo
    script = f"Namaskara. Nimma {advisory.crop_name} belege..."
    script += f" Bithane dina: {advisory.sowing_date}..."
    
    # Shopping
    script += " Neevu khareedi madbekada gobbara: "
    for item in advisory.shopping_list:
        if item.bags > 0:
            script += f"{item.bags} bag {item.product_local}, "
            
    # Warnings
    if any("Lime" in w for w in advisory.simple_warnings):
        script += " Manninalli amla amsha hecchige ide, sunna haakodu kaddaya."
        
    script += " Dhanyavadagalu."
    return script

# Update conversion to include colloquial
def convert_to_bags_detailed(product: str, kg_amount: float) -> ShoppingItem:
    """Enhanced converter with colloquial string."""
    item = convert_to_bags(product, kg_amount)
    return item

# =============================================================================
# LOGIC
# =============================================================================

def convert_to_bags(product: str, kg_amount: float) -> ShoppingItem:
    """
    Convert raw kg to bags + loose kg.
    Example: 120kg Urea -> 2 bags (90kg) + 30kg loose
    """
    bag_size = BAG_SIZES.get(product.lower(), 50)
    
    # Round to nearest 0.1 kg
    kg_amount = round(kg_amount, 1)
    
    bags = int(kg_amount // bag_size)
    loose = round(kg_amount % bag_size, 1)
    
    # If loose amount is very close to a bag (e.g. >95%), just suggest another bag
    if loose > (bag_size * 0.95):
        bags += 1
        loose = 0
    
    return ShoppingItem(
        product_name=product,
        product_local=LOCAL_NAMES.get(product.lower(), product.title()),
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
    
    # We need to distribute the PRODUCTS (Urea, DAP, MOP) based on nutrient splits
    # This is an approximation since DAP contains N and P
    # Simple logic: 
    # - DAP goes 100% in Basal usually (or follow P split)
    # - MOP follows K split
    # - Urea fills the remaining N requirement in each split
    
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
        
        # Calculate product amounts for this split
        # P is usually 100% basal unless specified
        p_pct = details.get("p_pct", 0)
        n_pct = details.get("n_pct", 0)
        k_pct = details.get("k_pct", 0)
        
        # Distribute products
        split_dap = dap_total * (p_pct / 100)
        split_mop = mop_total * (k_pct / 100)
        split_urea = urea_total * (n_pct / 100)
        
        products_list = []
        if split_urea > 1:
            bags_urea = convert_to_bags("urea", split_urea)
            qty_str = f"{bags_urea.bags} ಬ್ಯಾಗ್" if bags_urea.bags > 0 else ""
            if bags_urea.loose_kg > 0:
                qty_str += f" + {bags_urea.loose_kg:.0f} kg"
            products_list.append(f"ಯೂರಿಯಾ: {qty_str.strip(' + ')}")
            
        if split_dap > 1:
            bags_dap = convert_to_bags("dap", split_dap)
            qty_str = f"{bags_dap.bags} ಬ್ಯಾಗ್" if bags_dap.bags > 0 else ""
            if bags_dap.loose_kg > 0:
                qty_str += f" + {bags_dap.loose_kg:.0f} kg"
            products_list.append(f"ಡಿ.ಎ.ಪಿ: {qty_str.strip(' + ')}")
            
        if split_mop > 1:
            bags_mop = convert_to_bags("mop", split_mop)
            qty_str = f"{bags_mop.bags} ಬ್ಯಾಗ್" if bags_mop.bags > 0 else ""
            if bags_mop.loose_kg > 0:
                qty_str += f" + {bags_mop.loose_kg:.0f} kg"
            products_list.append(f"ಪೊಟ್ಯಾಷ್: {qty_str.strip(' + ')}")
            
        if not products_list:
            continue
            
        schedule_items.append(ScheduleItem(
            stage_name=stage,
            stage_kannada=timing_str,
            timing=f"Day {days_offset}",
            date_range=date_str,
            products=products_list,
            instructions=[details.get("timing", "")]
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
    manure_type: str = None,           # v5.2
    manure_tons: float = 0.0,          # v5.2
    area_acres: float = 1.0
) -> FarmerAdvisory:
    """
    Create the full farmer advisory structure.
    """
    try:
        sowing_date = datetime.strptime(sowing_date_str, "%Y-%m-%d")
    except:
        sowing_date = datetime.now()
        
    # CONVERSION: HA -> ACRE
    acre_factor = 2.5 
    
    urea_acre = urea_kg / acre_factor
    dap_acre = dap_kg / acre_factor
    mop_acre = mop_kg / acre_factor
    zinc_acre = zinc_kg / acre_factor
    lime_tons_acre = lime_t_ha / acre_factor
    
    # 0. v5.2 MANURE CREDIT
    manure_msg = ""
    net_urea_acre = urea_acre
    net_dap_acre = dap_acre
    net_mop_acre = mop_acre
    
    if manure_type and manure_tons > 0:
        manure_tons_acre = manure_tons 
        credits = calculate_manure_credit(manure_type, manure_tons_acre) 
        
        # Deduct nutrients
        urea_reduction = credits['n'] / 0.46
        dap_reduction = credits['p'] / 0.46 
        mop_reduction = credits['k'] / 0.60
        
        net_urea_acre = max(0, urea_acre - urea_reduction)
        net_dap_acre = max(0, dap_acre - dap_reduction)
        net_mop_acre = max(0, mop_acre - mop_reduction)
        
        manure_msg = f"✅ Manure Credit: Reduced Urea by {round(urea_reduction,1)}kg & DAP by {round(dap_reduction,1)}kg"

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
    health_card = [
        "✅ ಮಣ್ಣಿನ ಆರೋಗ್ಯ: ಉತ್ತಮವಾಗಿದೆ" if not any("Critical" in w for w in raw_warnings) else "⚠️ ಮಣ್ಣಿನ ಆರೋಗ್ಯ: ಸುಧಾರಣೆ ಅಗತ್ಯ",
        f"📅 ಬಿತ್ತನೆ ದಿನಾಂಕ: {sowing_date.strftime('%d-%m-%Y')}"
    ]
    
    # 4. Warnings + NEW ENHANCEMENTS
    simple_warnings = []
    
    # A. Weather Rule
    weather_msg = check_weather_rule(weather_forecast_mm)
    simple_warnings.append(weather_msg)
    
    # B. Compatibility Rule
    mix_warnings = check_compatibility(shopping)
    simple_warnings.extend(mix_warnings)
    
    # C. Existing Soil Warnings
    for w in raw_warnings:
        if "Al toxicity" in w or "Al ವಿಷತ್ವ" in w:
            simple_warnings.append("⚠️ ಮಣ್ಣಿನಲ್ಲಿ ಆಮ್ಲತೆ ಹೆಚ್ಚಾಗಿದೆ - ಸುಣ್ಣ ಹಾಕುವುದು ಕಡ್ಡಾಯ.")
        elif "Drainage" in w or "ನೀರು ಬಸಿಯುವಿಕೆ" in w:
            simple_warnings.append("⚠️ ಹೊಲದಲ್ಲಿ ನೀರು ನಿಲ್ಲದಂತೆ ನೋಡಿಕೊಳ್ಳಿ.")
        else:
            simple_warnings.append(w)
            
    # D. Substitutes (v5.2)
    substitutes = []
    for item in shopping:
        sub = get_substitute_advice(item.product_name, item.bags)
        if sub:
            substitutes.append(sub)
            
    # Create object to generate script
    partial_advisory = FarmerAdvisory(
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
