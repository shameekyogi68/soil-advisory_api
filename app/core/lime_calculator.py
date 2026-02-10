#!/usr/bin/env python3
"""
GrowMate Lime Requirement Calculator
Calculates lime requirement using Buffer pH (SMP) method.

Based on:
- ICAR Handbook of Agriculture (2022)
- Adams-Evans Buffer pH Method
- KVK Brahmavar recommendations for Udupi lateritic soils
"""

from dataclasses import dataclass
from typing import Dict, Optional, Tuple
from enum import Enum

# =============================================================================
# LIME CALCULATION CONSTANTS
# =============================================================================

class LimeProduct(Enum):
    """Common liming materials with neutralizing values"""
    CALCITE = ("calcite", "ite ಸುಣ್ಣ", 100)  # Pure CaCO3
    DOLOMITE = ("dolomite", "ಡೋಲೋಮೈಟ್", 109)  # CaMgCO3
    QUICKLITE = ("quicklime", "ಆಕ್ಸೈ ಲೈಮ್", 179)  # CaO
    HYDRATED_LIME = ("hydrated_lime", "ತುಂಗಚುಣ್ಣ", 136)  # Ca(OH)2
    SHELL_LIME = ("shell_lime", "ಚಿಪ್ಪಿ ಸುಣ್ಣ", 85)  # Ground shells
    SLAG = ("slag", "ಸ್ಲ್ಯಾಗ್", 80)  # Steel slag


# SMP Buffer pH to Lime Requirement Table (t/ha CaCO3 equivalent)
# Target pH 6.5 for 15 cm depth, medium texture soil
SMP_LIME_TABLE = {
    # (buffer_pH_low, buffer_pH_high): lime_t_ha
    (6.8, 7.0): 0.5,
    (6.6, 6.8): 1.0,
    (6.4, 6.6): 1.5,
    (6.2, 6.4): 2.0,
    (6.0, 6.2): 2.5,
    (5.8, 6.0): 3.0,
    (5.6, 5.8): 3.5,
    (5.4, 5.6): 4.0,
    (5.2, 5.4): 4.5,
    (5.0, 5.2): 5.0,
    (4.8, 5.0): 5.5,
    (4.6, 4.8): 6.0,
    (4.4, 4.6): 6.5,
    (4.2, 4.4): 7.0,
    (4.0, 4.2): 7.5,
}

# Texture adjustment factors (relative to medium texture)
TEXTURE_FACTORS = {
    "sandy": 0.6,       # Less buffering, needs less lime
    "sandy_loam": 0.8,
    "loam": 1.0,
    "silt_loam": 1.1,
    "clay_loam": 1.2,
    "clay": 1.5,        # High buffering, needs more lime
}

# Depth adjustment (base is 15 cm)
def depth_factor(depth_cm: int) -> float:
    """Adjust lime for incorporation depth"""
    return depth_cm / 15.0

# Target pH by soil type (optimal for most crops)
TARGET_PH = {
    "lateritic": 6.0,    # Ghats soils - don't over-lime
    "coastal_sandy": 6.5,
    "alluvial": 6.5,
    "black_clay": 7.0,   # Already neutral, rarely needs lime
    "acid_saline": 6.0,  # Special case
}


# =============================================================================
# LIME CALCULATOR CLASS
# =============================================================================

@dataclass
class LimeResult:
    """Result of lime requirement calculation"""
    needs_lime: bool
    lime_required_t_ha: float           # Pure CaCO3 equivalent
    product_amount_t_ha: float          # Actual product amount
    product_type: str
    product_kannada: str
    bags_per_acre: int                  # 50 kg bags
    target_ph: float
    current_ph: float
    method_used: str
    confidence: str
    warnings: list
    kannada_summary: list


class LimeCalculator:
    """
    Calculates lime requirement for acidic soils.
    
    Methods:
    1. Buffer pH (SMP) - Most accurate, requires lab buffer pH
    2. Water pH only - Approximate, when buffer pH not available
    3. Empirical (Udupi specific) - Based on local research
    """
    
    # Removed cost estimates per user request
    
    def __init__(
        self,
        soil_ph: float,
        buffer_ph: Optional[float] = None,
        soil_texture: str = "loam",
        soil_type: str = "lateritic",
        depth_cm: int = 15,
        preferred_product: str = "dolomite"
    ):
        self.soil_ph = soil_ph
        self.buffer_ph = buffer_ph
        self.soil_texture = soil_texture
        self.soil_type = soil_type
        self.depth_cm = depth_cm
        self.preferred_product = preferred_product
        
        # Get target pH based on soil type
        self.target_ph = TARGET_PH.get(soil_type, 6.5)
        
        # Get lime product properties
        self.product = self._get_product(preferred_product)
    
    def _get_product(self, name: str) -> Tuple[str, str, int]:
        """Get lime product by name"""
        for product in LimeProduct:
            if product.value[0] == name:
                return product.value
        return LimeProduct.DOLOMITE.value  # Default
    
    def calculate_buffer_ph_method(self) -> LimeResult:
        """
        Calculate lime using SMP Buffer pH method (most accurate).
        Requires laboratory buffer pH measurement.
        """
        warnings = []
        
        # Check if lime is needed
        if self.soil_ph >= self.target_ph:
            return LimeResult(
                needs_lime=False,
                lime_required_t_ha=0,
                product_amount_t_ha=0,
                product_type=self.product[0],
                product_kannada=self.product[1],
                bags_per_acre=0,
                target_ph=self.target_ph,
                current_ph=self.soil_ph,
                method_used="buffer_ph",
                confidence="high",
                warnings=["ಸುಣ್ಣ ಅಗತ್ಯವಿಲ್ಲ - pH ಸಾಕಷ್ಟು ಇದೆ"],
                kannada_summary=["✅ ಮಣ್ಣಿನ pH ಸೂಕ್ತವಾಗಿದೆ, ಸುಣ್ಣ ಅಗತ್ಯವಿಲ್ಲ"]
            )
        
        if self.buffer_ph is None:
            raise ValueError("Buffer pH required for this method. Use calculate_empirical_method() instead.")
        
        # Look up lime requirement from SMP table
        base_lime = 0
        for (low, high), amount in SMP_LIME_TABLE.items():
            if low <= self.buffer_ph < high:
                base_lime = amount
                break
        
        if base_lime == 0 and self.buffer_ph < 4.0:
            base_lime = 8.0  # Maximum for very low buffer pH
            warnings.append("⚠️ ಅತಿ ಆಮ್ಲೀಯ ಮಣ್ಣು - ಎರಡು ಬಾರಿ ಸುಣ್ಣ ಹಾಕಬೇಕು")
        
        # Apply adjustments
        texture_adj = TEXTURE_FACTORS.get(self.soil_texture, 1.0)
        depth_adj = depth_factor(self.depth_cm)
        
        # Calculate CaCO3 equivalent
        lime_caco3 = base_lime * texture_adj * depth_adj
        
        # Adjust for product neutralizing value
        product_lime = lime_caco3 * (100 / self.product[2])
        
        # Convert to bags per acre (1 acre = 0.4 ha, 50 kg bags)
        bags_per_acre = int((product_lime * 0.4 * 1000) / 50)
        
        # Generate Kannada summary
        kannada_summary = [
            f"📊 ಪ್ರಸ್ತುತ pH: {self.soil_ph}, ಗುರಿ pH: {self.target_ph}",
            f"🧪 ಬಫರ್ pH: {self.buffer_ph}",
            f"💊 {self.product[1]}: {product_lime:.1f} ಟನ್/ಹೆ (ಸುಮಾರು {bags_per_acre} ಚೀಲ/ಎಕರೆ)",
            "⏰ ಮಳೆಗಾಲಕ್ಕೆ ಮುಂಚೆ ಹಾಕಿ, 15 ಸೆಂ.ಮೀ ಆಳಕ್ಕೆ ಮಿಶ್ರ ಮಾಡಿ"
        ]
        
        # Add warnings for high lime amounts
        if lime_caco3 > 4:
            warnings.append("⚠️ 2 ಟನ್/ಹೆ ಮೊದಲು, ಉಳಿದದ್ದು 6 ತಿಂಗಳ ನಂತರ")
        
        return LimeResult(
            needs_lime=True,
            lime_required_t_ha=round(lime_caco3, 2),
            product_amount_t_ha=round(product_lime, 2),
            product_type=self.product[0],
            product_kannada=self.product[1],
            bags_per_acre=bags_per_acre,
            target_ph=self.target_ph,
            current_ph=self.soil_ph,
            method_used="buffer_ph",
            confidence="high",
            warnings=warnings,
            kannada_summary=kannada_summary
        )
    
    def calculate_empirical_method(self) -> LimeResult:
        """
        Calculate lime using empirical method (when buffer pH not available).
        Based on water pH and soil texture only - less accurate.
        """
        warnings = []
        
        # Check if lime is needed
        if self.soil_ph >= self.target_ph:
            return LimeResult(
                needs_lime=False,
                lime_required_t_ha=0,
                product_amount_t_ha=0,
                product_type=self.product[0],
                product_kannada=self.product[1],
                bags_per_acre=0,
                target_ph=self.target_ph,
                current_ph=self.soil_ph,
                method_used="empirical",
                confidence="medium",
                warnings=["ಸುಣ್ಣ ಅಗತ್ಯವಿಲ್ಲ"],
                kannada_summary=["✅ ಮಣ್ಣಿನ pH ಸೂಕ್ತವಾಗಿದೆ"]
            )
        
        # Empirical formula for Udupi lateritic soils
        # Based on local research from KVK Brahmavar
        ph_deficit = self.target_ph - self.soil_ph
        
        # Base calculation (t/ha CaCO3 per pH unit)
        if self.soil_texture in ["clay", "clay_loam"]:
            factor = 1.5  # High buffer capacity
        elif self.soil_texture in ["loam", "silt_loam"]:
            factor = 1.0
        else:
            factor = 0.7  # Sandy soils
        
        base_lime = ph_deficit * factor
        
        # Adjust for depth
        base_lime *= depth_factor(self.depth_cm)
        
        # Calculate product amount
        product_lime = base_lime * (100 / self.product[2])
        
        # Bags per acre
        bags_per_acre = int((product_lime * 0.4 * 1000) / 50)
        
        warnings.append("⚠️ ನಿಖರವಾದ ಲೆಕ್ಕಕ್ಕೆ ಬಫರ್ pH ಪರೀಕ್ಷೆ ಮಾಡಿ")
        
        kannada_summary = [
            f"📊 ಪ್ರಸ್ತುತ pH: {self.soil_ph}, ಗುರಿ pH: {self.target_ph}",
            f"💊 {self.product[1]}: ಸುಮಾರು {product_lime:.1f} ಟನ್/ಹೆ",
            f"📦 ಸುಮಾರು {bags_per_acre} ಚೀಲ/ಎಕರೆ (50 ಕೆಜಿ ಚೀಲ)",
        ]
        
        return LimeResult(
            needs_lime=True,
            lime_required_t_ha=round(base_lime, 2),
            product_amount_t_ha=round(product_lime, 2),
            product_type=self.product[0],
            product_kannada=self.product[1],
            bags_per_acre=bags_per_acre,
            target_ph=self.target_ph,
            current_ph=self.soil_ph,
            method_used="empirical",
            confidence="medium",
            warnings=warnings,
            kannada_summary=kannada_summary
        )
    
    def calculate(self) -> LimeResult:
        """
        Auto-select best method based on available data.
        """
        if self.buffer_ph is not None:
            return self.calculate_buffer_ph_method()
        else:
            return self.calculate_empirical_method()


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def calculate_lime(
    soil_ph: float,
    buffer_ph: Optional[float] = None,
    soil_texture: str = "loam",
    soil_type: str = "lateritic",
    depth_cm: int = 15,
    product: str = "dolomite"
) -> LimeResult:
    """
    Convenience function to calculate lime requirement.
    
    Args:
        soil_ph: Water pH (1:2 soil:water)
        buffer_ph: SMP buffer pH (if available from lab)
        soil_texture: sandy, sandy_loam, loam, clay_loam, clay
        soil_type: lateritic, coastal_sandy, alluvial, black_clay
        depth_cm: Incorporation depth (default 15 cm)
        product: calcite, dolomite, quicklime, hydrated_lime, shell_lime
    
    Returns:
        LimeResult with recommendations
    """
    calc = LimeCalculator(
        soil_ph=soil_ph,
        buffer_ph=buffer_ph,
        soil_texture=soil_texture,
        soil_type=soil_type,
        depth_cm=depth_cm,
        preferred_product=product
    )
    return calc.calculate()


# =============================================================================
# DEMO
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("GrowMate Lime Requirement Calculator")
    print("=" * 60)
    
    # Example 1: With buffer pH (accurate)
    print("\n📋 Example 1: Lateritic soil with buffer pH")
    print("-" * 50)
    
    result = calculate_lime(
        soil_ph=5.2,
        buffer_ph=6.0,
        soil_texture="clay_loam",
        soil_type="lateritic",
        depth_cm=15,
        product="dolomite"
    )
    
    print(f"  Needs Lime: {result.needs_lime}")
    print(f"  CaCO3 Equivalent: {result.lime_required_t_ha} t/ha")
    print(f"  Product ({result.product_kannada}): {result.product_amount_t_ha} t/ha")
    print(f"  Bags/Acre: {result.bags_per_acre}")
    print(f"  Method: {result.method_used} (Confidence: {result.confidence})")
    
    print("\n  Kannada Summary:")
    for line in result.kannada_summary:
        print(f"    {line}")
    
    if result.warnings:
        print("\n  Warnings:")
        for w in result.warnings:
            print(f"    {w}")
    
    # Example 2: Without buffer pH (empirical)
    print("\n📋 Example 2: Sandy soil without buffer pH")
    print("-" * 50)
    
    result2 = calculate_lime(
        soil_ph=4.8,
        buffer_ph=None,
        soil_texture="sandy_loam",
        soil_type="coastal_sandy",
        product="shell_lime"
    )
    
    print(f"  Needs Lime: {result2.needs_lime}")
    print(f"  Product ({result2.product_kannada}): {result2.product_amount_t_ha} t/ha")
    print(f"  Bags/Acre: {result2.bags_per_acre}")
    print(f"  Method: {result2.method_used} (Confidence: {result2.confidence})")
    
    # Example 3: No lime needed
    print("\n📋 Example 3: Neutral soil")
    print("-" * 50)
    
    result3 = calculate_lime(soil_ph=6.8, soil_type="alluvial")
    
    print(f"  Needs Lime: {result3.needs_lime}")
    print(f"  Summary: {result3.kannada_summary[0]}")
