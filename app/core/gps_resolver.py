import csv
import json
import os
import functools
from typing import Dict, Optional, Tuple

class GPSResolver:
    """
    Resolves Taluk/Zone from GPS coordinates and fetches average soil profile.
    """
    
    def __init__(self, profiles_dir: Optional[str] = None):
        if profiles_dir is None:
            # Locate 'data/taluk_profiles' relative to this file (app/core/gps_resolver.py)
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # app/
            profiles_dir = os.path.join(base_dir, "data", "taluk_profiles")
            
        self.profiles_dir = profiles_dir
        self.bounds_file = os.path.join(profiles_dir, "taluk_bounds_lookup.csv")
        self.profiles_file = os.path.join(profiles_dir, "taluk_profiles.json")
        self.bounds = []
        self.profiles = {}
        self._load_data()
        
    def _load_data(self):
        # Load Bounds
        try:
            with open(self.bounds_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.bounds.append({
                        "taluk": row["taluk"],
                        "min_lat": float(row["min_lat"]),
                        "max_lat": float(row["max_lat"]),
                        "min_lon": float(row["min_lon"]),
                        "max_lon": float(row["max_lon"])
                    })
        except FileNotFoundError:
            print(f"Warning: Bounds file not found at {self.bounds_file}")

        # Load Profiles
        try:
            with open(self.profiles_file, 'r') as f:
                self.profiles = json.load(f)
        except FileNotFoundError:
            print(f"Warning: Profiles file not found at {self.profiles_file}")

    @functools.lru_cache(maxsize=1024)
    def resolve_taluk(self, lat: float, lon: float) -> Optional[str]:
        """Find which taluk contains the coordinate."""
        for b in self.bounds:
            if (b["min_lat"] <= lat <= b["max_lat"]) and \
               (b["min_lon"] <= lon <= b["max_lon"]):
                return b["taluk"]
        return "Udupi" # Default fallback

    def get_agro_zone(self, lon: float) -> str:
        """
        Determine Agro-Climatic Zone based on Longitude (Udupi Geography).
        West = Coastal, East = Western Ghats.
        """
        if lon < 74.75:
            return "coastal"
        elif lon > 74.95:
            return "ghats"
        else:
            return "midland"

    @functools.lru_cache(maxsize=1024)
    def is_lowland(self, lat: float, lon: float) -> bool:
        """
        Heuristic: Locations close to major rivers are likely 'Lowland' (Gadde).
        Simple proximity check to known river segments in Udupi.
        """
        # Approximate segments of Swarna, Sita, Udyavara rivers
        # Format: (lat1, lon1, lat2, lon2) - simplified line segments
        RIVERS = [
            (13.40, 74.70, 13.35, 74.80), # Swarna towards sea
            (13.45, 74.75, 13.42, 74.70), # Sita river
            (13.25, 74.75, 13.28, 74.78), # Udyavara river
            (13.60, 74.65, 13.65, 74.70)  # Varahi/North rivers
        ]
        
    
        threshold = 0.015 # Approx 1.5km
        
        def dist_sq(x1, y1, x2, y2):
            return (x1-x2)**2 + (y1-y2)**2

        for r in RIVERS:
            # Segment V(r0,r1) to W(r2,r3)
            # Point P(lat, lon)
            vx, vy = r[0], r[1]
            wx, wy = r[2], r[3]
            
            l2 = dist_sq(vx, vy, wx, wy)
            if l2 == 0: 
                d2 = dist_sq(lat, lon, vx, vy)
            else:
                t = ((lat - vx) * (wx - vx) + (lon - vy) * (wy - vy)) / l2
                t = max(0, min(1, t))
                
                proj_x = vx + t * (wx - vx)
                proj_y = vy + t * (wy - vy)
                
                d2 = dist_sq(lat, lon, proj_x, proj_y)
                
            if d2 < (threshold**2):
                return True
            
        return False

    def get_profile(self, lat: float, lon: float, land_type_override: Optional[str] = None) -> Dict:
        """Get refined soil profile for location."""
        taluk = self.resolve_taluk(lat, lon)
        if not taluk:
            taluk = "Udupi"
            
        # 1. Base Profile from Taluk Average
        base_profile = self.profiles.get(taluk, self.profiles.get("Udupi", {}))
        
        # 2. Refine based on Agro-Climatic Zone
        zone = self.get_agro_zone(lon)
        
        # 3. Refine based on Topography (Auto-detected or User Input)
        if land_type_override:
            is_lowland = (land_type_override.lower() == "lowland")
        else:
            is_lowland = self.is_lowland(lat, lon)
            
        topo_type = "Lowland" if is_lowland else "Upland"
        
        # Default values from Taluk
        n = base_profile.get("nitrogen_class", "medium")
        p = base_profile.get("phosphorus_class", "medium")
        k = base_profile.get("potassium_class", "medium")
        ph_class = base_profile.get("ph_class", "acidic")
        texture = base_profile.get("soil_texture_class", "lateritic")
        
        # 4. Apply Heuristics (The "Expert" Layer)
        if zone == "coastal":
            # Narrow Coastal Strip Logic (< 2km from sea approx)
            # 74.70 is approx 4-5km inland from 74.65 shoreline
            if lon < 74.70:
                texture = "sandy"
            
            # Broader Coastal Zone Effect
            ph_class = "neutral" 
            
        elif zone == "ghats":
            texture = "clay_loam" 
            ph_class = "acidic" 
            n = "high" 
            
        elif zone == "midland":
            # Midlands are typically lateritic, not sandy
            if texture in ["sandy", "sandy_loam"]:
                texture = "lateritic"
            ph_class = "acidic"
            
        # Topography Adjustment
        if is_lowland:
            # Lowlands accumulate clay and nutrients
            if texture == "lateritic": texture = "clay_loam"
            if n == "low": n = "medium"
            # if k == "low": k = "medium"  <-- Removed per Expert Audit (Region is K deficient)
            
        return {
            "taluk": taluk,
            "zone": zone,
            "topography": topo_type, # Exposed for metadata
            "n": n,
            "p": p,
            "k": k,
            "ph_class": ph_class,
            "texture": texture
        }

# Usage Example
if __name__ == "__main__":
    resolver = GPSResolver()
    # Test Udupi Coord
    lat, lon = 13.3409, 74.7421
    profile = resolver.get_profile(lat, lon)
    print(f"Location ({lat}, {lon}) -> Taluk: {profile['taluk']}")
    print(f"Profile: N={profile['n']}, P={profile['p']}, K={profile['k']}, pH={profile['ph_class']}")
