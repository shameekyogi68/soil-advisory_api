import sys
import os
import unittest

# Add root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.api_logic import process_request

class TestErrorHandling(unittest.TestCase):
    
    def test_missing_coordinates(self):
        """Test missing Lat/Lon"""
        res = process_request({"crop": "Paddy"})
        self.assertEqual(res.get("error"), "Missing Soil Data or GPS Coordinates")
        
    def test_invalid_coordinates(self):
        """Test non-numeric Lat/Lon"""
        res = process_request({"lat": "invalid", "lon": 74.0, "crop": "Paddy"})
        self.assertEqual(res.get("error"), "Invalid Latitude/Longitude")

    def test_invalid_soil_data(self):
        """Test non-numeric Lab Data"""
        res = process_request({
            "ph": "acidic", # Should be float
            "nitrogen_kg_ha": 100,
            "crop": "Paddy"
        })
        self.assertEqual(res.get("error"), "Invalid numeric values in Soil Data")
        
    def test_missing_manure_values(self):
        """Test valid logic even if optional manure fields are garbage"""
        # Should NOT crash, just default to 0
        res = process_request({
            "lat": 13.0, "lon": 74.0, "crop": "Paddy",
            "manure_loads": "invalid_number"
        })
        self.assertEqual(res["status"], "success")
        
    def test_missing_crop(self):
        """Test default crop fallback"""
        res = process_request({"lat": 13.0, "lon": 74.0})
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["meta"]["crop"], "Paddy") # Default

if __name__ == '__main__':
    unittest.main()
