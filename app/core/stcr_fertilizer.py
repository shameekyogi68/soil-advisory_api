#!/usr/bin/env python3
"""
GrowMate STCR Fertilizer Calculator
Yield-Target Based Fertilizer Recommendations using STCR Methodology.

Based on:
- AICRP-STCR (All India Coordinated Research Project on STCR)
- ICAR targeted yield approach
- KVK Brahmavar recommendations for Udupi crops
- UAS Dharwad fertilizer equations for Karnataka
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum

# =============================================================================
# CROP NUTRIENT REQUIREMENTS
# =============================================================================

# Nutrient uptake per unit yield (kg/unit)
# Sources: ICAR Technical Bulletins, UAS Dharwad Research
CROP_NUTRIENT_UPTAKE = {
    # Cereals (kg/t grain)
    "paddy": {
        "yield_unit": "t/ha",
        "n_uptake": 22,    # kg N per t grain
        "p_uptake": 4.5,   # kg P2O5 per t grain
        "k_uptake": 25,    # kg K2O per t grain
        "min_yield": 2.0,
        "max_yield": 8.0,
        "typical_yield": 4.5,
        "kannada": "ಭತ್ತ",
    },
    "finger_millet": {
        "yield_unit": "t/ha",
        "n_uptake": 28,
        "p_uptake": 5.0,
        "k_uptake": 30,
        "min_yield": 1.5,
        "max_yield": 4.0,
        "typical_yield": 2.5,
        "kannada": "ರಾಗಿ",
    },
    
    # Plantation crops (g/palm/year)
    "arecanut": {
        "yield_unit": "kg/palm",
        "n_uptake": 0.1,   # g N per kg nut
        "p_uptake": 0.04,
        "k_uptake": 0.15,
        "min_yield": 1.0,
        "max_yield": 3.0,
        "typical_yield": 2.0,
        "fixed_dose": True,  # Use fixed dose per palm
        "n_per_palm": 100,   # g/palm/year
        "p_per_palm": 40,
        "k_per_palm": 140,
        "kannada": "ಅಡಿಕೆ",
    },
    "coconut": {
        "yield_unit": "nuts/palm",
        "n_uptake": 5.0,   # g N per nut
        "p_uptake": 3.2,
        "k_uptake": 12.0,
        "min_yield": 50,
        "max_yield": 150,
        "typical_yield": 80,
        "fixed_dose": True,
        "n_per_palm": 500,
        "p_per_palm": 320,
        "k_per_palm": 1200,
        "kannada": "ತೆಂಗು",
    },
    
    # Vegetables (kg/t)
    "banana": {
        "yield_unit": "t/ha",
        "n_uptake": 7.0,
        "p_uptake": 1.5,
        "k_uptake": 17.0,
        "min_yield": 30,
        "max_yield": 70,
        "typical_yield": 50,
        "kannada": "ಬಾಳೆ",
    },
    
    # Spices
    "pepper": {
        "yield_unit": "kg/vine",
        "n_uptake": 25,
        "p_uptake": 5,
        "k_uptake": 20,
        "min_yield": 1,
        "max_yield": 5,
        "typical_yield": 2,
        "fixed_dose": True,
        "n_per_vine": 50,
        "p_per_vine": 20,
        "k_per_vine": 100,
        "kannada": "ಕಾಳುಮೆಣಸು",
    },
    "ginger": {
        "yield_unit": "t/ha",
        "n_uptake": 6.5,
        "p_uptake": 1.5,
        "k_uptake": 10,
        "min_yield": 8,
        "max_yield": 25,
        "typical_yield": 15,
        "kannada": "ಶುಂಠಿ",
    },
    "turmeric": {
        "yield_unit": "t/ha",
        "n_uptake": 5.0,
        "p_uptake": 1.2,
        "k_uptake": 8.0,
        "min_yield": 5,
        "max_yield": 15,
        "typical_yield": 8,
        "kannada": "ಅರಿಶಿನ",
    },
}

# Soil contribution coefficients (% nutrient from soil)
SOIL_CONTRIBUTION = {
    "nitrogen": {
        "low": 0.3,      # 30% from soil if low status
        "medium": 0.5,   # 50% from soil if medium
        "high": 0.7,     # 70% from soil if high
    },
    "phosphorus": {
        "low": 0.2,
        "medium": 0.4,
        "high": 0.6,
    },
    "potassium": {
        "low": 0.3,
        "medium": 0.5,
        "high": 0.7,
    },
}

# Fertilizer efficiency factors
FERTILIZER_EFFICIENCY = {
    "nitrogen": 0.50,     # 50% recovery of applied N
    "phosphorus": 0.25,   # 25% recovery (low due to fixation)
    "potassium": 0.60,    # 60% recovery
}

# P-fixation factors by soil type
P_FIXATION_FACTORS = {
    "lateritic": 0.55,     # 55% of P gets fixed
    "coastal_sandy": 0.15,
    "alluvial": 0.25,
    "black_clay": 0.35,
    "acid_saline": 0.30,
}

# Previous crop N-credits (kg/ha)
PREVIOUS_CROP_CREDITS = {
    "paddy": 0,
    "groundnut": 25,
    "cowpea": 35,
    "green_gram": 25,
    "black_gram": 20,
    "soybean": 30,
    "dhaincha": 40,      # Green manure
    "sesbania": 45,
    "fallow": 0,
}

# =============================================================================
# MICRONUTRIENT REQUIREMENTS
# =============================================================================

MICRONUTRIENT_DOSES = {
    "paddy": {
        "zinc_sulfate": 25,     # kg/ha if deficient
        "ferrous_sulfate": 50,
        "borax": 2.5,
        "manganese_sulfate": 20,
    },
    "arecanut": {
        "zinc_sulfate": 50,    # g/palm
        "borax": 25,
        "ferrous_sulfate": 100,
    },
    "coconut": {
        "zinc_sulfate": 100,
        "borax": 50,
        "manganese_sulfate": 50,
    },
}


# =============================================================================
# STCR CALCULATOR CLASS
# =============================================================================

@dataclass
class STCRResult:
    """Result of STCR fertilizer calculation"""
    crop: str
    crop_kannada: str
    target_yield: float
    yield_unit: str
    
    # Calculated doses (kg/ha or g/plant)
    n_required: float
    p_required: float
    k_required: float
    
    # Fertilizer products
    urea_kg: float
    dap_kg: float
    mop_kg: float
    
    # Adjustments applied
    n_credit: float
    p_fixation_factor: float
    
    # Split application
    splits: Dict
    

    
    # Kannada summary
    kannada_summary: List[str]
    
    # Warnings
    warnings: List[str]


class STCRCalculator:
    """
    Soil Test Crop Response (STCR) based fertilizer calculator.
    
    Formula:
    Fertilizer N = (Yield Target × N uptake - Soil N × Cs) / Efficiency
    Fertilizer P = (Yield Target × P uptake - Soil P × Cs) / (Efficiency × (1 - Fixation))
    Fertilizer K = (Yield Target × K uptake - Soil K × Cs) / Efficiency
    """
    
    # Removed cost calculations per user request
    
    def __init__(
        self,
        crop: str,
        target_yield: float,
        soil_n_status: str = "medium",  # low/medium/high
        soil_p_status: str = "medium",
        soil_k_status: str = "medium",
        soil_type: str = "lateritic",
        previous_crop: str = "fallow",
        area_ha: float = 1.0,
    ):
        self.crop = crop.lower()
        self.target_yield = target_yield
        self.soil_n_status = soil_n_status
        self.soil_p_status = soil_p_status
        self.soil_k_status = soil_k_status
        self.soil_type = soil_type
        self.previous_crop = previous_crop
        self.area_ha = area_ha
        
        # Get crop data
        if self.crop not in CROP_NUTRIENT_UPTAKE:
            raise ValueError(f"Unknown crop: {crop}. Available: {list(CROP_NUTRIENT_UPTAKE.keys())}")
        
        self.crop_data = CROP_NUTRIENT_UPTAKE[self.crop]
        
        # Validate yield target
        if target_yield < self.crop_data["min_yield"]:
            self.target_yield = self.crop_data["min_yield"]
        elif target_yield > self.crop_data["max_yield"]:
            self.target_yield = self.crop_data["max_yield"]
    
    def calculate(self) -> STCRResult:
        """Calculate fertilizer requirement using STCR method"""
        warnings = []
        
        # For plantation crops with fixed doses
        if self.crop_data.get("fixed_dose"):
            return self._calculate_fixed_dose()
        
        # Get soil contribution coefficients
        cs_n = SOIL_CONTRIBUTION["nitrogen"][self.soil_n_status]
        cs_p = SOIL_CONTRIBUTION["phosphorus"][self.soil_p_status]
        cs_k = SOIL_CONTRIBUTION["potassium"][self.soil_k_status]
        
        # Get fertilizer efficiency
        eff_n = FERTILIZER_EFFICIENCY["nitrogen"]
        eff_p = FERTILIZER_EFFICIENCY["phosphorus"]
        eff_k = FERTILIZER_EFFICIENCY["potassium"]
        
        # Get P fixation factor
        p_fix = P_FIXATION_FACTORS.get(self.soil_type, 0.30)
        
        # Get previous crop credit
        n_credit = PREVIOUS_CROP_CREDITS.get(self.previous_crop, 0)
        
        # Calculate nutrient uptake for target yield
        n_uptake = self.target_yield * self.crop_data["n_uptake"]
        p_uptake = self.target_yield * self.crop_data["p_uptake"]
        k_uptake = self.target_yield * self.crop_data["k_uptake"]
        
        # Calculate fertilizer requirement
        # N = (Total uptake - Soil supply - Credit) / Efficiency
        n_required = max(0, (n_uptake * (1 - cs_n) - n_credit) / eff_n)
        
        # P = (Total uptake - Soil supply) / (Efficiency × (1 - Fixation))
        p_required = max(0, (p_uptake * (1 - cs_p)) / (eff_p * (1 - p_fix)))
        
        # K = (Total uptake - Soil supply) / Efficiency
        k_required = max(0, (k_uptake * (1 - cs_k)) / eff_k)
        
        # Convert to fertilizer products
        # DAP: 18% N, 46% P2O5
        # Urea: 46% N
        # MOP: 60% K2O
        
        # Use DAP for P requirement first
        dap_kg = p_required / 0.46
        n_from_dap = dap_kg * 0.18
        
        # Remaining N from urea
        urea_kg = max(0, (n_required - n_from_dap) / 0.46)
        
        # MOP for K
        mop_kg = k_required / 0.60
        
        # Round to practical values
        urea_kg = round(urea_kg, 1)
        dap_kg = round(dap_kg, 1)
        mop_kg = round(mop_kg, 1)
        
        # Generate split recommendations
        splits = self._get_splits(urea_kg, dap_kg, mop_kg)
        
        # Warnings
        if self.target_yield > self.crop_data["typical_yield"] * 1.2:
            warnings.append(f"⚠️ ಗುರಿ ಇಳುವರಿ ಹೆಚ್ಚು - ನೀರಾವರಿ ಮತ್ತು ನಿರ್ವಹಣೆ ಅತ್ಯುತ್ತಮವಾಗಿರಬೇಕು")
        
        if p_fix > 0.4:
            warnings.append(f"⚠️ ಲ್ಯಾಟರೈಟ್ ಮಣ್ಣಿನಲ್ಲಿ P ಸ್ಥಿರೀಕರಣ ಹೆಚ್ಚು - P ಬ್ಯಾಂಡ್ ಪ್ಲೇಸ್‌ಮೆಂಟ್ ಶಿಫಾರಸು")
        
        if n_credit > 0:
            warnings.append(f"✅ ಹಿಂದಿನ ದ್ವಿದಳ ಬೆಳೆಯಿಂದ {n_credit} kg/ha N ಕ್ರೆಡಿಟ್")
        
        # Kannada summary
        kannada_summary = [
            f"🌾 ಗುರಿ ಇಳುವರಿ: {self.target_yield} {self.crop_data['yield_unit']}",
            f"📊 ಪೋಷಕಾಂಶ ಅಗತ್ಯ: {n_required:.0f} N, {p_required:.0f} P₂O₅, {k_required:.0f} K₂O kg/ha",
            f"💊 ಯೂರಿಯಾ: {urea_kg} kg, DAP: {dap_kg} kg, MOP: {mop_kg} kg",
        ]
        
        return STCRResult(
            crop=self.crop,
            crop_kannada=self.crop_data["kannada"],
            target_yield=self.target_yield,
            yield_unit=self.crop_data["yield_unit"],
            n_required=round(n_required, 1),
            p_required=round(p_required, 1),
            k_required=round(k_required, 1),
            urea_kg=urea_kg,
            dap_kg=dap_kg,
            mop_kg=mop_kg,
            n_credit=n_credit,
            p_fixation_factor=p_fix,
            splits=splits,
            kannada_summary=kannada_summary,
            warnings=warnings,
        )
    
    def _calculate_fixed_dose(self) -> STCRResult:
        """Calculate for plantation crops with fixed dose per plant"""
        # Get fixed doses
        n_per_plant = self.crop_data.get("n_per_palm", self.crop_data.get("n_per_vine", 100))
        p_per_plant = self.crop_data.get("p_per_palm", self.crop_data.get("p_per_vine", 40))
        k_per_plant = self.crop_data.get("k_per_palm", self.crop_data.get("k_per_vine", 140))
        
        # Adjust for soil status
        n_adj = {"low": 1.0, "medium": 0.75, "high": 0.5}[self.soil_n_status]
        p_adj = {"low": 1.0, "medium": 0.75, "high": 0.5}[self.soil_p_status]
        k_adj = {"low": 1.0, "medium": 0.75, "high": 0.5}[self.soil_k_status]
        
        n_required = n_per_plant * n_adj
        p_required = p_per_plant * p_adj
        k_required = k_per_plant * k_adj
        
        # Convert to fertilizer (g/plant)
        urea_g = n_required / 0.46
        dap_g = p_required / 0.46
        mop_g = k_required / 0.60
        
        # Calculate for typical plant density
        if self.crop == "arecanut":
            plants_per_ha = 1100
        elif self.crop == "coconut":
            plants_per_ha = 175
        elif self.crop == "pepper":
            plants_per_ha = 1600
        else:
            plants_per_ha = 1000
        
        # Total per ha
        total_urea = (urea_g * plants_per_ha) / 1000
        total_dap = (dap_g * plants_per_ha) / 1000
        total_mop = (mop_g * plants_per_ha) / 1000
        
        splits = {
            "basal": {"timing": "ಮಳೆಗಾಲ ಆರಂಭ (ಜೂನ್)", "n_pct": 50, "p_pct": 100, "k_pct": 50},
            "top_dress_1": {"timing": "ಸೆಪ್ಟೆಂಬರ್", "n_pct": 25, "p_pct": 0, "k_pct": 25},
            "top_dress_2": {"timing": "ನವೆಂಬರ್", "n_pct": 25, "p_pct": 0, "k_pct": 25},
        }
        
        kannada_summary = [
            f"🌴 {self.crop_data['kannada']} - ಪ್ರತಿ ಮರಕ್ಕೆ/ಬಳ್ಳಿಗೆ",
            f"💊 ಯೂರಿಯಾ: {urea_g:.0f} g, DAP: {dap_g:.0f} g, MOP: {mop_g:.0f} g",
            f"📊 ಒಟ್ಟು ಪ್ರತಿ ಹೆಕ್ಟೇರ್: ಯೂರಿಯಾ {total_urea:.0f} kg, DAP {total_dap:.0f} kg, MOP {total_mop:.0f} kg",
        ]
        
        return STCRResult(
            crop=self.crop,
            crop_kannada=self.crop_data["kannada"],
            target_yield=self.target_yield,
            yield_unit=self.crop_data["yield_unit"],
            n_required=round(n_required, 1),
            p_required=round(p_required, 1),
            k_required=round(k_required, 1),
            urea_kg=round(urea_g, 1),  # g per plant
            dap_kg=round(dap_g, 1),
            mop_kg=round(mop_g, 1),
            n_credit=0,
            p_fixation_factor=0,
            splits=splits,
            kannada_summary=kannada_summary,
            warnings=[],
        )
    
    def _get_splits(self, urea: float, dap: float, mop: float) -> Dict:
        """Get split application schedule for the crop"""
        if self.crop == "paddy":
            return {
                "basal": {
                    "timing": "ನಾಟಿ ಮಾಡುವಾಗ",
                    "timing_en": "At transplanting",
                    "urea_kg": round(urea * 0.5, 1),
                    "dap_kg": dap,  # Full P at basal
                    "mop_kg": round(mop * 0.5, 1),
                },
                "tillering": {
                    "timing": "ಪಿಲ್ಲಿ ಬರುವ ಹಂತ (21 DAT)",
                    "timing_en": "Tillering (21 DAT)",
                    "urea_kg": round(urea * 0.25, 1),
                    "dap_kg": 0,
                    "mop_kg": 0,
                },
                "panicle": {
                    "timing": "ತೆನೆ ಬರುವ ಹಂತ (45 DAT)",
                    "timing_en": "Panicle initiation (45 DAT)",
                    "urea_kg": round(urea * 0.25, 1),
                    "dap_kg": 0,
                    "mop_kg": round(mop * 0.5, 1),
                },
            }
        else:
            # Default 2-split for other crops
            return {
                "basal": {
                    "timing": "ಬಿತ್ತನೆ/ನಾಟಿ ಸಮಯದಲ್ಲಿ",
                    "timing_en": "At sowing/planting",
                    "urea_kg": round(urea * 0.5, 1),
                    "dap_kg": dap,
                    "mop_kg": round(mop * 0.5, 1),
                },
                "top_dress": {
                    "timing": "30-40 ದಿನಗಳ ನಂತರ",
                    "timing_en": "30-40 days after",
                    "urea_kg": round(urea * 0.5, 1),
                    "dap_kg": 0,
                    "mop_kg": round(mop * 0.5, 1),
                },
            }


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

def calculate_fertilizer(
    crop: str,
    target_yield: float,
    soil_n: str = "medium",
    soil_p: str = "medium",
    soil_k: str = "medium",
    soil_type: str = "lateritic",
    previous_crop: str = "fallow",
) -> STCRResult:
    """
    Calculate fertilizer requirement for a target yield.
    
    Args:
        crop: paddy, arecanut, coconut, pepper, ginger, etc.
        target_yield: Desired yield in appropriate units
        soil_n, soil_p, soil_k: low/medium/high from soil test
        soil_type: lateritic, coastal_sandy, alluvial, black_clay
        previous_crop: groundnut, cowpea, dhaincha, fallow, etc.
    
    Returns:
        STCRResult with fertilizer recommendations
    """
    calc = STCRCalculator(
        crop=crop,
        target_yield=target_yield,
        soil_n_status=soil_n,
        soil_p_status=soil_p,
        soil_k_status=soil_k,
        soil_type=soil_type,
        previous_crop=previous_crop,
    )
    return calc.calculate()


# =============================================================================
# DEMO
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("GrowMate STCR Fertilizer Calculator")
    print("=" * 60)
    
    # Example 1: Paddy with target yield
    print("\n📋 Example 1: Paddy - Target 5 t/ha")
    print("-" * 50)
    
    result = calculate_fertilizer(
        crop="paddy",
        target_yield=5.0,
        soil_n="low",
        soil_p="medium",
        soil_k="medium",
        soil_type="lateritic",
        previous_crop="groundnut"
    )
    
    print(f"  Crop: {result.crop_kannada} ({result.crop})")
    print(f"  Target: {result.target_yield} {result.yield_unit}")
    print(f"\n  Nutrient Requirement:")
    print(f"    N: {result.n_required} kg/ha")
    print(f"    P₂O₅: {result.p_required} kg/ha")
    print(f"    K₂O: {result.k_required} kg/ha")
    print(f"\n  Fertilizer Products:")
    print(f"    Urea: {result.urea_kg} kg/ha")
    print(f"    DAP: {result.dap_kg} kg/ha")
    print(f"    MOP: {result.mop_kg} kg/ha")

    
    print("\n  Split Application:")
    for stage, details in result.splits.items():
        print(f"    {stage}: {details['timing']}")
        print(f"      Urea: {details['urea_kg']} kg, DAP: {details['dap_kg']} kg, MOP: {details['mop_kg']} kg")
    
    if result.warnings:
        print("\n  Warnings:")
        for w in result.warnings:
            print(f"    {w}")
    
    # Example 2: Arecanut (fixed dose)
    print("\n📋 Example 2: Arecanut - Per Palm Dose")
    print("-" * 50)
    
    result2 = calculate_fertilizer(
        crop="arecanut",
        target_yield=2.0,
        soil_n="medium",
        soil_p="low",
        soil_k="medium",
        soil_type="lateritic"
    )
    
    print(f"  Crop: {result2.crop_kannada}")
    print(f"\n  Per Palm Requirement:")
    print(f"    Urea: {result2.urea_kg} g/palm")
    print(f"    DAP: {result2.dap_kg} g/palm")
    print(f"    MOP: {result2.mop_kg} g/palm")

    
    print("\n  Kannada Summary:")
    for line in result2.kannada_summary:
        print(f"    {line}")
    
    # Example 3: Pepper
    print("\n📋 Example 3: Pepper - Per Vine Dose")
    print("-" * 50)
    
    result3 = calculate_fertilizer(crop="pepper", target_yield=2.0)
    
    print(f"  Crop: {result3.crop_kannada}")
    print(f"  Urea: {result3.urea_kg} g/vine, DAP: {result3.dap_kg} g/vine, MOP: {result3.mop_kg} g/vine")

    
    # List available crops
    print("\n" + "=" * 60)
    print("Available Crops")
    print("=" * 60)
    for crop, data in CROP_NUTRIENT_UPTAKE.items():
        print(f"  {crop:15} ({data['kannada']}): {data['min_yield']}-{data['max_yield']} {data['yield_unit']}")
