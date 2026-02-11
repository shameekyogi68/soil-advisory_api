#!/bin/bash
echo "🚀 Testing API (Localhost)..."
curl -X POST http://127.0.0.1:5000/api/advisory \
     -H "Content-Type: application/json" \
     -d @test_payload.json

# echo "🚀 Testing API (Render - Replace URL)..."
# curl -X POST https://your-app-name.onrender.com/api/advisory \
#      -H "Content-Type: application/json" \
#      -d @test_payload.json
